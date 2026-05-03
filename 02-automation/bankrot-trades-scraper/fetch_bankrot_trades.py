"""
Скрипт для сбора объявлений о проведении торгов с old.bankrot.fedresurs.ru
"""
import argparse
import json
import logging
import os
import random
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import urlopen
from typing import Any, Callable

from scrapling.fetchers import StealthyFetcher
from scrapling.engines.toolbelt.custom import Response, StatusText

logger = logging.getLogger(__name__)


def _configure_logging(log_file: str | None, verbose: bool) -> None:
    """Консоль + опционально файл; при verbose — DEBUG."""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    if log_file:
        path = Path(log_file).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(path, encoding="utf-8"))
    logging.basicConfig(level=level, format=fmt, datefmt=datefmt, handlers=handlers, force=True)

BASE_URL = "https://old.bankrot.fedresurs.ru"
MESSAGES_URL = f"{BASE_URL}/Messages.aspx"
# Новый портал: карточка сообщения — https://fedresurs.ru/bankruptmessages/{ID}
FEDRESURS_PUBLIC = "https://fedresurs.ru"

# ID полей на странице Messages.aspx
DATE_FROM_ID = "ctl00_cphBody_cldrBeginDate_tbSelectedDate"
DATE_TO_ID = "ctl00_cphBody_cldrEndDate_tbSelectedDate"
MESSAGE_TYPE_FIELD_ID = "ctl00_cphBody_mdsMessageType_tbSelectedText"

# Тип сообщения: в форме выбираем в модалке, чтобы сервер вернул только эти записи (95/133/168 по датам).
MESSAGE_TYPE_TRADE = "Объявление о проведении торгов"

# Сборка JS: карточка может задаваться только __doPostBack / ShowMessageWindow(ID) без подстроки MessageWindow.aspx.
def _build_extract_trade_links_js(skip_type_filter: bool) -> str:
    """skip_type_filter: доверять отбору формы (тип + даты), не отсекать строки по тексту «торгов»."""
    tf = MESSAGE_TYPE_TRADE.replace("'", "\\'")
    skip_js = "true" if skip_type_filter else "false"
    base = BASE_URL.rstrip("/")
    return f"""
() => {{
  const baseUrl = '{base}';
  const typeFull = '{tf}';
  const typeShort = 'проведении торгов';
  const skipTypeFilter = {skip_js};
  const result = [];
  const seen = new Set();

  function textClean(s) {{
    return (s || '').trim().replace(/\\s+/g, ' ');
  }}

  function rowOf(el) {{
    let p = el.parentElement;
    while (p && p.tagName !== 'TR' && p.tagName !== 'BODY') p = p.parentElement;
    if (p && p.tagName === 'TR') return textClean(p.innerText || p.textContent || '');
    return '';
  }}

  function isTradeRow(linkText, rowText) {{
    if (skipTypeFilter) return true;
    if (linkText.indexOf(typeFull) >= 0 || linkText.indexOf(typeShort) >= 0) return true;
    if (rowText.indexOf(typeFull) >= 0 || rowText.indexOf(typeShort) >= 0) return true;
    return false;
  }}

  /** URL карточки: href, javascript:, __doPostBack, ShowMessageWindow('guid'), MessageWindow.aspx?ID= */
  function extractMsgPath(el) {{
    const href = (el.getAttribute('href') || '').trim();
    const oc = (el.getAttribute('onclick') || '') + ' ' + (el.getAttribute('onmousedown') || '');
    const blob = (href + ' ' + oc).replace(/\\s+/g, ' ');

    let m = blob.match(/(https?:\\/\\/[^\\s'\"<>]*fedresurs\\.ru\\/bankruptmessages\\/[A-Fa-f0-9]{{32}})/i);
    if (m) return m[1].split('#')[0];
    m = blob.match(/\\/bankruptmessages\\/([A-Fa-f0-9]{{32}})/i);
    if (m) return 'https://fedresurs.ru/bankruptmessages/' + m[1];

    m = blob.match(/MessageWindow\\.aspx\\?[^'\"\\s<>]+/i);
    if (!m) m = blob.match(/MessageCard\\.aspx\\?[^'\"\\s<>]+/i);
    if (m) {{
      const p = m[0];
      if (p.indexOf('http://') === 0 || p.indexOf('https://') === 0) return p.split('#')[0];
      return p.replace(/^\\.\\//, '');
    }}
    m = blob.match(/['\"]\\s*([/]?MessageWindow\\.aspx\\?[^'\"\\s]+)['\"]?/i);
    if (m) return m[1].replace(/^\\.\\//, '');
    m = blob.match(/MessageWindow\\s*\\(\\s*['\"]([^'\"]{20,})['\"]/i);
    if (m) return 'MessageWindow.aspx?ID=' + m[1];
    m = blob.match(/ShowMessageWindow\\s*\\(\\s*['\"]([A-Fa-f0-9]{{32,}})['\"]/i);
    if (!m) m = blob.match(/OpenMessageWindow\\s*\\(\\s*['\"]([A-Fa-f0-9]{{32,}})['\"]/i);
    if (!m) m = blob.match(/MessageWindow\\s*\\(\\s*['\"]([A-Fa-f0-9]{{32,}})['\"]/i);
    if (m) return 'MessageWindow.aspx?ID=' + m[1];
    m = blob.match(/__doPostBack\\s*\\(\\s*['\"][^'\"]*['\"]\\s*,\\s*['\"]([A-Fa-f0-9]{{32,}})['\"]\\s*\\)/i);
    if (m) return 'MessageWindow.aspx?ID=' + m[1];
    m = blob.match(/window\\.open\\s*\\(\\s*['\"]([^'\"]*MessageWindow[^'\"]*)['\"]/i);
    if (m) {{
      const inner = m[1];
      if (inner.indexOf('?') >= 0) return inner.indexOf('http') === 0 ? inner.split('#')[0] : inner.replace(/^\\.\\//, '');
    }}
    m = blob.match(/window\\.open\\s*\\(\\s*['\"]([^'\"]*bankruptmessages[^'\"]*)['\"]/i);
    if (m) {{
      const inner = m[1];
      if (inner.indexOf('http') === 0) return inner.split('#')[0];
      if (inner.indexOf('/') === 0) return 'https://fedresurs.ru' + inner.split('#')[0];
    }}
    m = blob.match(/\\bID\\s*=\\s*['\"]?([A-Fa-f0-9]{{32,}})['\"]?/i);
    if (m && /lbtnMessage|MessageWindow|messagecard|MessageCard|grdMessage|ShowMessage|OpenMessage/i.test(blob))
      return 'MessageWindow.aspx?ID=' + m[1];
    if (href && href.indexOf('javascript:') !== 0) {{
      const low = href.toLowerCase();
      if (low.indexOf('messagewindow') >= 0 || low.indexOf('messagecard') >= 0) return href.replace(/^\\.\\//, '');
    }}
    if (href && href.indexOf('javascript:') !== 0 && /bankruptmessages\\/[A-Fa-f0-9]{{32}}/i.test(href)) {{
      if (href.indexOf('http') === 0) return href.split('#')[0];
      if (href.indexOf('/') === 0) return 'https://fedresurs.ru' + href.split('#')[0];
    }}
    return '';
  }}

  function toFullUrl(path) {{
    if (!path) return '';
    if (path.indexOf('http://') === 0 || path.indexOf('https://') === 0) return path.split('#')[0];
    const p = path.startsWith('/') ? path : '/' + path.replace(/^\\.\\//, '');
    return baseUrl + p;
  }}

  const root = document.querySelector('#ctl00_cphBody') || document.body;
  const candidates = new Set();
  root.querySelectorAll('a').forEach(a => candidates.add(a));
  root.querySelectorAll('[onclick]').forEach(el => {{
    const o = el.getAttribute('onclick') || '';
    if (/MessageWindow|MessageCard|lbtnMessage|ShowMessage|OpenMessage|doPostBack|PostBack|bankruptmessages|message/i.test(o)) candidates.add(el);
  }});

  for (const el of candidates) {{
    const path = extractMsgPath(el);
    if (!path) continue;
    const linkText = textClean(el.innerText || el.textContent || '');
    const rowText = rowOf(el);
    if (!isTradeRow(linkText, rowText)) continue;
    const fullUrl = toFullUrl(path);
    if (!fullUrl || seen.has(fullUrl)) continue;
    seen.add(fullUrl);
    result.push({{ linkText: linkText || typeFull, fullUrl }});
  }}
  return result;
}}
"""


StealthyFetcher.auto_match = True


def _click_next_pagination_page(page: Any, next_page_num: int) -> bool:
    """Переход на следующую страницу списка (ASP.NET / Telerik RadGrid).

    Сначала «Следующая» / rgPageNext — иначе на узком пейджере нет ссылок Page$17 и цикл обрывается.
    Затем ссылка с __doPostBack и Page$N. В CSS [href*=\"Page$2\"] символ $ часто ломает селектор — используем XPath.
    """
    # 1) Telerik / типичные классы следующей страницы
    for sel in (
        "a.rgPageNext",
        "input.rgPageNext",
        ".rgPager a.rgPageNext",
        "a[title*='Следующ']",
        "a[title*='Next']",
    ):
        try:
            loc = page.locator(sel)
            if loc.count() > 0:
                loc.first.click(timeout=45_000)
                return True
        except Exception:
            continue

    # 2) Текстовые ссылки «Следующая» / стрелки (точное совпадение текста ссылки)
    for label in ("Следующая", ">", "»", "›"):
        try:
            loc = page.locator("a").filter(has_text=re.compile("^" + re.escape(label) + r"\s*$"))
            if loc.count() > 0:
                loc.first.click(timeout=45_000)
                return True
        except Exception:
            continue

    # 3) __doPostBack с Page$N (XPath — без проблем с $ в CSS)
    try:
        needle = f"Page${next_page_num}"
        loc = page.locator(f"xpath=//a[contains(@href, '{needle}')]")
        if loc.count() > 0:
            loc.first.click(timeout=45_000)
            return True
    except Exception:
        pass

    # 4) Ячейка пейджера с номером страницы
    try:
        loc = page.locator("td[colspan] a, .rgPager a").filter(
            has_text=re.compile(r"^" + str(next_page_num) + r"$")
        )
        if loc.count() > 0:
            loc.first.click(timeout=45_000)
            return True
    except Exception:
        pass

    return False


def _wait_after_pagination_click(page: Any) -> None:
    """Postback ASP.NET: дождаться загрузки, не полагаться только на sleep."""
    try:
        page.wait_for_load_state("load", timeout=120_000)
    except Exception:
        try:
            page.wait_for_load_state("domcontentloaded", timeout=60_000)
        except Exception:
            pass
    page.wait_for_timeout(600)


# JS: извлечение полей карточки и раздела «Лоты» (все поля внутри секции Лоты)
_EXTRACT_CARD_DATA_JS = """
() => {
  function getText(el) {
    if (!el) return '';
    const tag = (el.tagName || '').toUpperCase();
    if (tag === 'INPUT' || tag === 'TEXTAREA') return (el.value || '').trim().replace(/\\s+/g, ' ');
    const inner = (el.innerText || el.textContent || '').trim().replace(/\\s+/g, ' ');
    if (inner) return inner;
    const inp = el.querySelector('input, textarea');
    if (inp) return (inp.value || '').trim().replace(/\\s+/g, ' ');
    const title = el.getAttribute('title');
    if (title) return title.trim().replace(/\\s+/g, ' ');
    return '';
  }
  function getCellText(el) {
    const t = getText(el);
    if (t) return t;
    const dataVal = el.getAttribute('data-value') || el.getAttribute('data-text') || el.getAttribute('value');
    if (dataVal) return String(dataVal).trim().replace(/\\s+/g, ' ');
    return '';
  }
  const fields = {};
  const lots = [];
  const LOT_FIELDS = ['Номер лота', 'Описание', 'Начальная цена, руб.', 'Шаг', 'Задаток', 'Информация о снижении цены', 'Классификация имущества'];
  const path = (typeof location !== 'undefined' && location.pathname) ? location.pathname : '';
  const isBankruptMsgCard = /\\/bankruptmessages\\/[0-9A-F]{32}\\/?$/i.test(path);
  const messageWindowPage = /MessageWindow\\.aspx/i.test(path || '');

  /** document + все открытые shadowRoot (Angular/custom elements на fedresurs.ru). */
  function getSearchRoots() {
    const roots = [document];
    for (let i = 0; i < roots.length; i++) {
      const base = roots[i];
      const iter = base.querySelectorAll ? base.querySelectorAll('*') : [];
      for (let j = 0; j < iter.length; j++) {
        const el = iter[j];
        if (el.shadowRoot) roots.push(el.shadowRoot);
      }
    }
    return roots;
  }

  function matchLotField(canonical, rawKey) {
    const k = (rawKey || '').toLowerCase().trim();
    if (!k) return false;
    switch (canonical) {
      case 'Номер лота':
        return /лот\\s*№|№\\s*лота|номер\\s*лота|^№$/.test(k)
          || (k.indexOf('лот') >= 0 && (k.indexOf('номер') >= 0 || k.indexOf('№') >= 0))
          || /^лот\\s*№?\\s*\\d/.test(k.trim())
          || k === 'лот' || k.indexOf('№ лот') >= 0 || k.indexOf('номер лот') >= 0;
      case 'Описание':
        return k.indexOf('описание') >= 0
          || (k.indexOf('предмет') >= 0 && (k.indexOf('торг') >= 0 || k.indexOf('продаж') >= 0 || k.indexOf('лот') >= 0))
          || (k.indexOf('наименование') >= 0 && k.indexOf('лот') >= 0)
          || (k.indexOf('объект') >= 0 && (k.indexOf('торг') >= 0 || k.indexOf('продаж') >= 0));
      case 'Начальная цена, руб.':
        return (k.indexOf('начальн') >= 0 && k.indexOf('цен') >= 0) || /цен.*руб|руб.*цен/.test(k)
          || (k.indexOf('стартов') >= 0 && k.indexOf('цен') >= 0)
          || (k.indexOf('минимальн') >= 0 && k.indexOf('цен') >= 0)
          || (k.indexOf('цен') >= 0 && (k.indexOf('руб') >= 0 || k.indexOf('рубл') >= 0))
          || (k.indexOf('стоимост') >= 0 && (k.indexOf('продаж') >= 0 || k.indexOf('лот') >= 0 || k.indexOf('торг') >= 0))
          || (k.indexOf('цен') >= 0 && (k.indexOf('продаж') >= 0 || k.indexOf('торг') >= 0 || k.indexOf('объект') >= 0));
      case 'Шаг': return k === 'шаг' || /^шаг\\s/.test(k);
      case 'Задаток': return k.indexOf('задаток') >= 0;
      case 'Информация о снижении цены':
        return (k.indexOf('снижен') >= 0 && k.indexOf('цен') >= 0) || k.indexOf('снижение цены') >= 0;
      case 'Классификация имущества': return k.indexOf('классифик') >= 0 || (k.indexOf('имуществ') >= 0 && k.indexOf('классифик') >= 0) || k.indexOf('классификация') >= 0;
      default: return false;
    }
  }

  function normalizeLot(raw) {
    const out = {};
    for (const canon of LOT_FIELDS) {
      for (const key of Object.keys(raw)) {
        if (matchLotField(canon, key) && raw[key]) {
          out[canon] = raw[key];
          break;
        }
      }
    }
    return out;
  }

  function looksLikeRealLot(norm) {
    const desc = (norm['Описание'] || '').trim();
    const price = (norm['Начальная цена, руб.'] || '').trim();
    const numLot = (norm['Номер лота'] || '').trim();
    const dep = (norm['Задаток'] || '').trim();
    let filled = 0;
    for (const f of LOT_FIELDS) {
      if ((norm[f] || '').trim()) filled += 1;
    }
    const priceLike = /\\d[\\d\\s,.]{4,}/.test(price);
    const depLike = /\\d[\\d\\s,.]{4,}/.test(dep);
    const numOk = /^\\d{1,4}$/.test(numLot);
    if (desc.length >= 25) return true;
    if (priceLike) return true;
    if (numOk && desc.length >= 20) return true;
    if (numOk && priceLike) return true;
    if (numOk && desc.length >= 12) return true;
    if (filled >= 4 && desc.length >= 18) return true;
    if (filled >= 4 && (priceLike || depLike || numOk)) return true;
    if (filled >= 3 && (desc.length >= 18 || priceLike || depLike)) return true;
    if (depLike && (priceLike || desc.length >= 20)) return true;
    return false;
  }

  function pushLot(lotObj) {
    const normalized = normalizeLot(lotObj);
    if (Object.keys(normalized).length === 0) return;
    if (!looksLikeRealLot(normalized)) return;
    lots.push(normalized);
  }

  /** В уже накопленном куске 2-колоночной таблицы есть строка с номером лота? */
  function chunkHasLotNumber(chunk) {
    for (const pk of Object.keys(chunk)) {
      if (matchLotField('Номер лота', pk)) return true;
    }
    return false;
  }
  function chunkHasDescription(chunk) {
    for (const pk of Object.keys(chunk)) {
      if (matchLotField('Описание', pk)) return true;
    }
    return false;
  }
  function chunkHasStartPrice(chunk) {
    for (const pk of Object.keys(chunk)) {
      if (matchLotField('Начальная цена, руб.', pk)) return true;
    }
    return false;
  }

  /** MessageWindow: 3 колонки — отступ, подпись, значение; иногда 4+. */
  function labelValueFromRow(tr) {
    const cells = tr.querySelectorAll('td, th');
    const n = cells.length;
    if (n < 2) return { k: '', v: '' };
    if (n === 2) return { k: getCellText(cells[0]), v: getCellText(cells[1]) };
    if (n === 3) {
      return {
        k: getCellText(cells[1]) || getCellText(cells[0]),
        v: getCellText(cells[2]),
      };
    }
    const k = getCellText(cells[1]) || getCellText(cells[0]);
    const v = getCellText(cells[n - 1]);
    return { k, v };
  }

  // Найти контейнер раздела «Лоты»: элемент с текстом Лоты/Лот и следующий за ним контент
  function findLotsContainer() {
    for (const root of getSearchRoots()) {
      const candidates = root.querySelectorAll('th, td, div, span, caption, label, .caption, h2, h3, h4');
      for (const el of candidates) {
        const t = getText(el);
        if (!t) continue;
        const lower = t.toLowerCase();
        let hit = false;
        if (messageWindowPage) {
          hit = (lower === 'лоты' || lower.indexOf('сведения о лот') >= 0 || lower.indexOf('информация о лот') >= 0
            || lower.indexOf('сведения по лот') >= 0 || /^лот\\s*№?\\s*\\d/.test(t.trim()));
          if (!hit && lower === 'лот' && t.length <= 12) hit = true;
        } else {
          hit = (lower === 'лоты' || lower === 'лот' || lower.indexOf('сведения о лот') >= 0 || lower.indexOf('лоты ') === 0);
        }
        if (!hit) continue;
        let container = el.closest('table');
        if (container) return container;
        container = el.parentElement;
        const stop = root === document ? document.body : root;
        while (container && container !== stop && container !== null) {
          const tables = container.querySelectorAll('table');
          if (tables.length > 0) return container;
          container = container.parentElement;
        }
        return el.parentElement;
      }
    }
    return null;
  }

  const lotsContainer = findLotsContainer();

  /** На MessageWindow несколько лотов часто в отдельных 2-col таблицах без общего родителя с заголовком «Лоты». */
  function tableLooksLikeLotBlock(table) {
    if (!messageWindowPage || !table) return false;
    let hasNum = false;
    let hasOther = false;
    let lotRowHits = 0;
    const rows = table.querySelectorAll('tr');
    for (let r = 0; r < rows.length; r++) {
      const pair = labelValueFromRow(rows[r]);
      const k = pair.k;
      if (!k) continue;
      if (matchLotField('Номер лота', k)) hasNum = true;
      if (matchLotField('Описание', k) || matchLotField('Начальная цена, руб.', k)) hasOther = true;
      if (matchLotField('Номер лота', k) || matchLotField('Описание', k) || matchLotField('Начальная цена, руб.', k)
          || matchLotField('Задаток', k) || matchLotField('Шаг', k) || matchLotField('Информация о снижении цены', k)
          || matchLotField('Классификация имущества', k)) {
        lotRowHits += 1;
      }
    }
    if (!hasNum) return false;
    return hasOther || lotRowHits >= 5;
  }

  /** Только настоящая шапка сетки лотов (не любая широкая таблица). */
  function lotGridHeaderScore(headerTexts) {
    const j = headerTexts.map(t => (t || '').toLowerCase().trim()).join(' | ');
    let s = 0;
    if (j.indexOf('номер') >= 0 && j.indexOf('лот') >= 0) s++;
    if (j.indexOf('описание') >= 0) s++;
    if ((j.indexOf('начальн') >= 0 && j.indexOf('цен') >= 0)
        || (j.indexOf('цен') >= 0 && j.indexOf('руб') >= 0)
        || /цен[^|]*руб|руб[^|]*цен/.test(j)) s++;
    if (j.indexOf('шаг') >= 0) s++;
    if (j.indexOf('задаток') >= 0) s++;
    if (j.indexOf('классифик') >= 0) s++;
    if (j.indexOf('снижен') >= 0 && j.indexOf('цен') >= 0) s++;
    return s;
  }

  // Таблицы: 2–3 колонки (MessageWindow) — labelValueFromRow; >3 — шапка + строки (каждая строка = один лот)
  getSearchRoots().forEach(root => {
    root.querySelectorAll('table').forEach(table => {
    const rows = Array.from(table.querySelectorAll('tr'));
    if (rows.length === 0) return;
    let maxCols = 0;
    rows.forEach(tr => {
      const n = tr.querySelectorAll('td, th').length;
      if (n > maxCols) maxCols = n;
    });
    const narrowTable = maxCols >= 2 && (messageWindowPage ? maxCols <= 4 : maxCols <= 3);
    const treatAsLots = tableLooksLikeLotBlock(table)
      || (lotsContainer && lotsContainer.contains(table) && !messageWindowPage);
    if (lotsContainer && !lotsContainer.contains(table) && !tableLooksLikeLotBlock(table)) {
      if (narrowTable) {
        rows.forEach(tr => {
          const pair = labelValueFromRow(tr);
          if (pair.k) fields[pair.k] = pair.v;
        });
      }
      return;
    }
    if (narrowTable) {
      if (treatAsLots) {
        let chunk = {};
        const flushChunk = () => {
          if (Object.keys(chunk).length > 0) {
            pushLot(chunk);
            chunk = {};
          }
        };
        rows.forEach(tr => {
          const pair = labelValueFromRow(tr);
          const k = pair.k;
          const v = pair.v;
          if (!k || !v) return;
          if (matchLotField('Номер лота', k) && chunkHasLotNumber(chunk)) flushChunk();
          if (matchLotField('Начальная цена, руб.', k) && chunkHasStartPrice(chunk)) flushChunk();
          if (matchLotField('Описание', k) && chunkHasDescription(chunk)) flushChunk();
          chunk[k] = v;
        });
        flushChunk();
      } else {
        rows.forEach(tr => {
          const pair = labelValueFromRow(tr);
          if (pair.k) fields[pair.k] = pair.v;
        });
      }
    } else if (maxCols > (messageWindowPage ? 4 : 3)) {
      let hdrIdx = -1;
      for (let ri = 0; ri < rows.length; ri++) {
        const cells = rows[ri].querySelectorAll('td, th');
        if (cells.length !== maxCols) continue;
        const headersTry = Array.from(cells).map(c => getCellText(c));
        if (lotGridHeaderScore(headersTry) >= 4) {
          hdrIdx = ri;
          break;
        }
      }
      if (hdrIdx < 0) return;
      const headerCells = rows[hdrIdx].querySelectorAll('td, th');
      const headers = Array.from(headerCells).map(c => getCellText(c));
      const nHead = headers.length;
      const minDataCells = nHead >= 6 ? nHead - 1 : Math.max(3, nHead - 1);
      for (let i = hdrIdx + 1; i < rows.length; i++) {
        const cells = rows[i].querySelectorAll('td, th');
        if (cells.length < minDataCells) continue;
        const valueTexts = [];
        const row = {};
        for (let j = 0; j < nHead; j++) {
          const key = (headers[j] && headers[j].trim()) ? headers[j].trim() : ('column_' + j);
          const val = cells[j] ? getCellText(cells[j]) : '';
          valueTexts.push(val);
          if (val) row[key] = val;
        }
        if (lotGridHeaderScore(valueTexts) >= 4) continue;
        if (Object.keys(row).length < 3) continue;
        const joined = valueTexts.join(' ');
        if (joined.replace(/\\s/g, '').length < 12) continue;
        const vals = valueTexts.map(v => String(v || '').trim());
        const maxValLen = vals.reduce((a, b) => Math.max(a, b.length), 0);
        const hasShortLotNum = vals.some(v => /^\\d{1,4}$/.test(v));
        const hasMoneyLike = vals.some(v => /\\d[\\d\\s,.]{4,}/.test(v));
        if (!hasShortLotNum && maxValLen < 28 && !hasMoneyLike) continue;
        pushLot(row);
      }
    }
  });
  });

  // Списки определений dl/dt/dd: вне раздела Лоты -> fields; внутри -> один лот на каждый dl
  getSearchRoots().forEach(root => {
    root.querySelectorAll('dl').forEach(dl => {
    const dts = dl.querySelectorAll('dt');
    const dds = dl.querySelectorAll('dd');
    const obj = {};
    dts.forEach((dt, i) => {
      if (dds[i]) {
        const k = getCellText(dt);
        const v = getCellText(dds[i]);
        if (k && v) obj[k] = v;
      }
    });
    if (lotsContainer && lotsContainer.contains(dl) && Object.keys(obj).length > 0) {
      pushLot(obj);
    } else if (Object.keys(obj).length > 0) {
      Object.assign(fields, obj);
    }
  });
  });

  // Элементы с классом/подписью вида label и значением рядом (часто на старых ASP-сайтах)
  getSearchRoots().forEach(root => {
    root.querySelectorAll(".fieldRow, .infoRow, tr.infoRow, [class*='Label']").forEach(row => {
    const label = row.querySelector("[id*='Label'], [class*='label'], th, .caption");
    const value = row.querySelector("[id*='Value'], [class*='value'], td:last-child, td + td");
    if (label && value) {
      const k = getCellText(label);
      const v = getCellText(value);
      if (k) fields[k] = v;
    }
  });
  });

  if (isBankruptMsgCard) {
    const nx = document.getElementById('__NEXT_DATA__');
    if (nx && nx.textContent) {
      try {
        const jd = JSON.parse(nx.textContent);
        const pp = jd.props && jd.props.pageProps;
        if (pp && typeof pp === 'object') {
          Object.keys(pp).forEach(k => {
            const v = pp[k];
            if (v !== null && v !== undefined && typeof v !== 'object') {
              fields['page.' + k] = String(v);
            } else if (v && typeof v === 'object' && !Array.isArray(v)) {
              Object.keys(v).forEach(k2 => {
                const v2 = v[k2];
                if (v2 !== null && v2 !== undefined && typeof v2 !== 'object') {
                  fields['page.' + k + '.' + k2] = String(v2);
                }
              });
            }
          });
        }
      } catch (eN) {}
    }
    const app = document.querySelector('fedresurs-app');
    let scope = null;
    if (app && app.shadowRoot) scope = app.shadowRoot;
    else if (app) scope = app;
    if (!scope) scope = document.querySelector('main, [role="main"], article') || document.body;
    if (scope) {
      scope.querySelectorAll('div').forEach(row => {
        if (row.children.length !== 2) return;
        const k = getCellText(row.children[0]);
        const v = getCellText(row.children[1]);
        if (!k || !v || k.length > 160 || v.length > 12000) return;
        const kl = k.toLowerCase();
        const looksKey = kl.endsWith(':') || kl.endsWith('：') || /лот|цен|торг|опис|дата|номер|задаток|шаг|организ|должник|площад|адрес|инн|огрн|фио|вид торгов/i.test(kl);
        if (looksKey && !fields[k]) fields[k] = v;
      });
    }
  }

  return { fields, lots };
}
"""


# Канонические поля лота (единый порядок работы с лотами: только эти поля, только «реальные» лоты)
LOT_FIELDS = [
    "Номер лота",
    "Описание",
    "Начальная цена, руб.",
    "Шаг",
    "Задаток",
    "Информация о снижении цены",
    "Классификация имущества",
]


def _match_lot_field(canonical: str, raw_key: str) -> bool:
    """Проверяет, что сырой заголовок соответствует каноническому полю лота."""
    k = (raw_key or "").lower().strip()
    if not k:
        return False
    if canonical == "Номер лота":
        if bool(re.search(r"лот\s*№|№\s*лота|номер\s*лота|^№$", k)):
            return True
        if "лот" in k and ("номер" in k or "№" in k):
            return True
        if k.strip() == "лот":
            return True
        if "№ лот" in k or "номер лот" in k:
            return True
        return bool(re.match(r"^лот\s*№?\s*\d", k.strip()))
    if canonical == "Описание":
        if "описание" in k:
            return True
        if "предмет" in k and ("торг" in k or "продаж" in k or "лот" in k):
            return True
        if "наименование" in k and "лот" in k:
            return True
        if "объект" in k and ("торг" in k or "продаж" in k):
            return True
        return False
    if canonical == "Начальная цена, руб.":
        if ("начальн" in k and "цен" in k) or bool(re.search(r"цен.*руб|руб.*цен", k)):
            return True
        if "стартов" in k and "цен" in k:
            return True
        if "минимальн" in k and "цен" in k:
            return True
        if "цен" in k and ("руб" in k or "рубл" in k):
            return True
        if "стоимост" in k and ("продаж" in k or "лот" in k or "торг" in k):
            return True
        if "цен" in k and ("продаж" in k or "торг" in k or "объект" in k):
            return True
        return False
    if canonical == "Шаг":
        return k == "шаг" or k.startswith("шаг ")
    if canonical == "Задаток":
        return "задаток" in k
    if canonical == "Информация о снижении цены":
        return ("снижен" in k and "цен" in k) or "снижение цены" in k
    if canonical == "Классификация имущества":
        return "классифик" in k or ("имуществ" in k and "классифик" in k) or "классификация" in k
    return False


def _match_lot_field_api(canonical: str, raw_key: str) -> bool:
    """Доп. соответствия для JSON backend (camelCase / англ.)."""
    rk = (raw_key or "").strip()
    low = rk.lower()
    if canonical == "Номер лота":
        return low in ("lotnumber", "number", "lotno", "lotid", "num", "nomerlota") or low.endswith(
            "lotnumber"
        )
    if canonical == "Описание":
        return low in ("description", "lotdescription", "name", "subject", "naimenovanie", "opisanie")
    if canonical == "Начальная цена, руб.":
        return low in (
            "startprice",
            "initialprice",
            "price",
            "minprice",
            "startingprice",
            "nachalnayatsena",
        ) or ("price" in low and "step" not in low and "total" not in low)
    if canonical == "Шаг":
        return low in ("step", "pricestep", "shag", "auctionstep") or low.endswith("pricestep")
    if canonical == "Задаток":
        return low in ("deposit", "earnest", "zalog", "zadatok", "pledgeamount")
    if canonical == "Информация о снижении цены":
        return "pricereduction" in low or "pricedrop" in low or "snizhenie" in low
    if canonical == "Классификация имущества":
        return low in ("propertyclassification", "classification", "klassifikatsiya")
    return False


def _normalize_lot(raw: dict[str, Any]) -> dict[str, Any]:
    """Приводит сырой объект лота к каноническим полям (только LOT_FIELDS)."""
    out: dict[str, Any] = {}
    for canon in LOT_FIELDS:
        for key, value in raw.items():
            if value and (_match_lot_field(canon, key) or _match_lot_field_api(canon, key)):
                out[canon] = value
                break
    return out


def _looks_like_real_lot(norm: dict[str, Any]) -> bool:
    """Отсекает мусор по содержимому; число лотов на карточке может быть 100+ (одна строка сетки = один лот)."""
    desc = (norm.get("Описание") or "").strip()
    price = (norm.get("Начальная цена, руб.") or "").strip()
    num_lot = (norm.get("Номер лота") or "").strip()
    dep = (norm.get("Задаток") or "").strip()
    price_like = bool(re.search(r"\d[\d\s,.]{4,}", price))
    dep_like = bool(re.search(r"\d[\d\s,.]{4,}", dep))
    num_ok = bool(re.match(r"^\d{1,4}$", num_lot))
    if len(desc) >= 25:
        return True
    if price_like:
        return True
    if num_ok and len(desc) >= 20:
        return True
    if num_ok and price_like:
        return True
    if num_ok and len(desc) >= 12:
        return True
    filled = sum(1 for f in LOT_FIELDS if (norm.get(f) or "").strip())
    if filled >= 4 and len(desc) >= 18:
        return True
    if filled >= 4 and (price_like or dep_like or num_ok):
        return True
    if filled >= 3 and (len(desc) >= 18 or price_like or dep_like):
        return True
    if dep_like and (price_like or len(desc) >= 20):
        return True
    return False


def _try_synthetic_lot_from_fields(fields: dict[str, Any]) -> list[dict[str, Any]]:
    """Если блок «Лоты» не распознан по вёрстке, подписи лота часто лежат в общих двухколоночных полях."""
    if not fields:
        return []
    normalized = _normalize_lot(dict(fields))
    if not normalized:
        return []
    if _looks_like_real_lot(normalized):
        return [normalized]
    return []


# Предупреждение только при подозрительно большом сыром списке (ложная сетка); 100+ реальных лотов бывает.
_LOTS_RAW_WARN_THRESHOLD = 250
# Защита от сбоев парсера (тысячи строк); обычные объявления с сотнями лотов не режем.
_LOTS_RESULT_CAP = 2000


def _lot_dedup_key(lot: dict[str, Any]) -> tuple[str, str, str]:
    d = (lot.get("Описание") or "").strip()[:400]
    return (
        (lot.get("Номер лота") or "").strip(),
        (lot.get("Начальная цена, руб.") or "").strip(),
        d,
    )


def _apply_lots_policy(lots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Нормализация и фильтр: только канонические поля, только реальные лоты (порядок работы с лотами)."""
    if len(lots) > _LOTS_RAW_WARN_THRESHOLD:
        logger.warning(
            "С карточки пришло сырых записей «лот»: %s — при норме «одна строка таблицы = один лот» такое бывает "
            "редко; если это не ложная сетка на странице, проверьте логику извлечения.",
            len(lots),
        )
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for raw in lots:
        normalized = _normalize_lot(raw)
        if not normalized or not _looks_like_real_lot(normalized):
            continue
        key = _lot_dedup_key(normalized)
        if key in seen:
            continue
        if key == ("", "", ""):
            continue
        seen.add(key)
        result.append(normalized)
    if len(result) > _LOTS_RESULT_CAP:
        logger.warning(
            "После фильтра лотов осталось %s — обрезано до %s (защита от сбоев парсера).",
            len(result),
            _LOTS_RESULT_CAP,
        )
        result = result[:_LOTS_RESULT_CAP]
    return result


# Таблица announcements в режиме --table (по одной строке на каждый распознанный лот карточки).
SLIM_DB_COLUMNS = [
    "url",
    "должник",
    "вид торгов",
    "ИНН",
    "начальная цена",
    "адрес",
    "extras_json",
    "Описание_из_extras_json",
]


def _collect_opisanie_strings_recursive(obj: Any) -> list[str]:
    """Все значения по ключу «Описание» в дереве dict/list (как в extras_db_add_opisanie)."""
    out: list[str] = []

    def rec(o: Any) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "Описание":
                    if isinstance(v, str) and v.strip():
                        out.append(v.strip())
                    elif isinstance(v, (dict, list)):
                        out.append(json.dumps(v, ensure_ascii=False))
                    elif v is not None:
                        out.append(str(v).strip())
                elif isinstance(v, (dict, list)):
                    rec(v)
        elif isinstance(o, list):
            for it in o:
                if isinstance(it, (dict, list)):
                    rec(it)

    rec(obj)
    return out


def _get_extras_json_value(obj: Any) -> str:
    """Возвращает значение extras_json из dict (если есть) или ''.

    В разных схемах ключ может быть extras_json / Extras_json / 'extras json' и т.п.
    """
    if not isinstance(obj, dict):
        return ""
    v = obj.get("extras_json")
    if v is not None:
        return str(v)
    for k, val in obj.items():
        lk = str(k).strip().lower().replace("_", " ")
        if lk == "extras json":
            return "" if val is None else str(val)
    return ""


def _opisanie_from_extras_json(extras_json: Any) -> str:
    """Извлекает строку «Описание» из JSON-строки extras_json (рекурсивно по ключу 'Описание')."""
    if extras_json is None:
        return ""
    if not isinstance(extras_json, str):
        extras_json = str(extras_json)
    raw = extras_json.strip()
    if not raw:
        return ""
    try:
        obj = json.loads(raw)
    except Exception:
        return ""
    parts = [
        s.strip()
        for s in _collect_opisanie_strings_recursive(obj)
        if isinstance(s, str) and s.strip()
    ]
    return "\n\n".join(parts).strip()


def _opisanie_from_extras_json_current_lot(extras_json: Any) -> str:
    """Только описание из объекта «lot» в extras_json — без склейки текстов всех лотов карточки."""
    if extras_json is None:
        return ""
    if not isinstance(extras_json, str):
        extras_json = str(extras_json)
    raw = extras_json.strip()
    if not raw:
        return ""
    try:
        obj = json.loads(raw)
    except Exception:
        return ""
    if not isinstance(obj, dict):
        return ""
    lot_obj = obj.get("lot")
    if not isinstance(lot_obj, dict):
        return ""
    parts = [
        s.strip()
        for s in _collect_opisanie_strings_recursive(lot_obj)
        if isinstance(s, str) and s.strip()
    ]
    return "\n\n".join(parts).strip()


def _extras_json_from_scraped(
    *,
    item_url: Any,
    item_id: Any,
    fields: dict[str, Any],
    lots: list[dict[str, Any]],
    lot: dict[str, Any] | None,
) -> str:
    """Складывает ВСЁ полученное скраппингом в JSON-строку для записи в БД (extras_json)."""
    payload: dict[str, Any] = {
        "url": item_url,
        "id": item_id,
        "fields": fields,
        "lots": lots,
    }
    if lot is not None:
        payload["lot"] = lot
    try:
        return json.dumps(payload, ensure_ascii=False)
    except Exception:
        # на всякий случай — не роняем запись, но сохраняем хоть что-то
        return json.dumps(
            {
                "url": _slim_str(item_url),
                "id": _slim_str(item_id),
                "fields": {str(k): _slim_str(v) for k, v in (fields or {}).items()},
                "lots": [
                    {str(k): _slim_str(v) for k, v in (lt or {}).items()}
                    for lt in (lots or [])
                    if isinstance(lt, dict)
                ],
                "lot": {str(k): _slim_str(v) for k, v in (lot or {}).items()} if isinstance(lot, dict) else None,
            },
            ensure_ascii=False,
        )


def _slim_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def _looks_like_ru_inn_digits(s: str) -> bool:
    d = re.sub(r"\D", "", s)
    return len(d) in (10, 12)


def _pick_debtor(fields: dict[str, Any]) -> str:
    for k, v in fields.items():
        lk = str(k).lower().replace("_", " ")
        if "представитель должника" in lk:
            continue
        if "наименование должника" in lk or lk.strip() == "должник" or lk.strip() == "должник:":
            s = _slim_str(v)
            if s and len(s) < 2000:
                return s
        if "должник" in lk and "представитель" not in lk and "конкурсн" not in lk and "общая сумма" not in lk:
            s = _slim_str(v)
            if s and len(s) < 2000 and not re.fullmatch(r"[\d\s.,]+", s):
                return s
    for k, v in sorted(fields.items(), key=lambda kv: len(str(kv[0]))):
        lk = str(k).lower().replace("_", " ")
        if ("debtor" in lk and "name" in lk) or lk.endswith("debtorname"):
            s = _slim_str(v)
            if s:
                return s
    return ""


def _pick_trade_type(fields: dict[str, Any]) -> str:
    for k, v in fields.items():
        lk = str(k).lower().replace("_", " ")
        if "вид" in lk and "торг" in lk:
            return _slim_str(v)
        if "тип" in lk and "торг" in lk:
            return _slim_str(v)
        if "вид сообщения" in lk:
            return _slim_str(v)
        if lk in ("messagecategory", "tradetype"):
            return _slim_str(v)
    return ""


def _pick_inn(fields: dict[str, Any]) -> str:
    scored: list[tuple[int, str]] = []
    for k, v in fields.items():
        lk = str(k).lower().replace("_", " ").replace("-", " ")
        klow = str(k).lower().replace("-", "")
        innish = "инн" in lk or "taxid" in lk or klow.endswith("inn")
        if not innish:
            continue
        s = _slim_str(v)
        if not _looks_like_ru_inn_digits(s):
            continue
        pri = 1
        if "долж" in lk or "debtor" in lk:
            pri += 10
        if lk.strip() == "инн" or lk == "inn":
            pri += 3
        if "организ" in lk or "площад" in lk:
            pri -= 2
        scored.append((pri, s))
    if not scored:
        return ""
    scored.sort(key=lambda x: (-x[0], -len(x[1])))
    return scored[0][1]


def _pick_address(fields: dict[str, Any]) -> str:
    for k, v in fields.items():
        lk = str(k).lower().replace("_", " ")
        if lk == "адрес" or "местонахождение" in lk or "место нахождения" in lk:
            s = _slim_str(v)
            if s:
                return s
        if lk in ("address", "location"):
            s = _slim_str(v)
            if s:
                return s
    return ""


def _pick_start_price(fields: dict[str, Any], lots: list[dict[str, Any]]) -> str:
    for lot in lots:
        if isinstance(lot, dict):
            s = _slim_str(lot.get("Начальная цена, руб."))
            if s:
                return s
    for k, v in fields.items():
        if _match_lot_field("Начальная цена, руб.", k) or _match_lot_field_api("Начальная цена, руб.", k):
            s = _slim_str(v)
            if s:
                return s
        lk = str(k).lower().replace("_", " ")
        if ("начальн" in lk and "цен" in lk) or ("стартов" in lk and "цен" in lk):
            return _slim_str(v)
    return ""


def slim_rows_from_card(item: dict[str, Any]) -> list[dict[str, str]]:
    """Компактная БД (SLIM_DB_COLUMNS); по строке на каждый элемент item['lots']; без лотов — одна строка из полей объявления."""
    fields = dict(item.get("fields") or {})
    lots = [x for x in (item.get("lots") or []) if isinstance(x, dict)]
    base_shared = {
        "url": _slim_str(item.get("url")),
        "должник": _pick_debtor(fields),
        "вид торгов": _pick_trade_type(fields),
        "ИНН": _pick_inn(fields),
        "адрес": _pick_address(fields),
    }
    rows: list[dict[str, str]] = []
    if lots:
        for lot in lots:
            extras = _extras_json_from_scraped(
                item_url=item.get("url"),
                item_id=item.get("id"),
                fields=fields,
                lots=lots,
                lot=lot,
            )
            # По каждому лоту — только его «Описание», без объединения всех лотов карточки.
            desc = _opisanie_from_extras_json_current_lot(extras)
            if not desc.strip():
                desc = "\n\n".join(
                    p.strip()
                    for p in _collect_opisanie_strings_recursive(lot)
                    if isinstance(p, str) and p.strip()
                ).strip()
            if not desc.strip() and len(lots) == 1:
                desc = _opisanie_from_extras_json(extras)
            if not desc.strip() and len(lots) == 1:
                desc = "\n\n".join(
                    p.strip()
                    for p in _collect_opisanie_strings_recursive(fields)
                    if isinstance(p, str) and p.strip()
                ).strip()
            price = _slim_str(lot.get("Начальная цена, руб."))
            if not price.strip():
                price = _pick_start_price(fields, [lot])
            rows.append(
                {
                    **base_shared,
                    "начальная цена": price,
                    "extras_json": extras,
                    "Описание_из_extras_json": desc,
                }
            )
    else:
        extras = _extras_json_from_scraped(
            item_url=item.get("url"),
            item_id=item.get("id"),
            fields=fields,
            lots=[],
            lot=None,
        )
        rows.append(
            {
                **base_shared,
                "начальная цена": _pick_start_price(fields, []),
                "extras_json": extras,
                "Описание_из_extras_json": (
                    _opisanie_from_extras_json(extras)
                    or "\n\n".join(_collect_opisanie_strings_recursive(fields))
                ),
            }
        )
    return rows


def _fieldnames_from_announcement_keys(announcement_keys: set[str]) -> list[str]:
    other = sorted(k for k in announcement_keys if k not in ("url", "id"))
    return ["url", "id"] + other + list(LOT_FIELDS)


def _rows_for_one_item(item: dict[str, Any]) -> list[dict[str, Any]]:
    """Строки таблицы для одной карточки (по одной на лот)."""
    fields = item.get("fields") or {}
    lots = item.get("lots") or []
    base = {
        "url": item.get("url", ""),
        "id": item.get("id", ""),
        **fields,
    }
    if lots:
        return [{**base, **lot} for lot in lots]
    return [{**base, **{f: "" for f in LOT_FIELDS}}]


def _build_rows_and_fieldnames(
    collected_data: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Плоская таблица для SQLite: одна строка = один лот (поля объявления дублируются)."""
    rows: list[dict[str, Any]] = []
    announcement_keys: set[str] = set()
    for item in collected_data:
        fields = item.get("fields") or {}
        announcement_keys.update(["url", "id", *fields.keys()])
        rows.extend(_rows_for_one_item(item))
    fieldnames = _fieldnames_from_announcement_keys(announcement_keys)
    return rows, fieldnames


def _sanitize_column(name: str) -> str:
    """Имя колонки для SQLite: буквы, цифры, подчёркивание (в т.ч. кириллица)."""
    s = re.sub(r"[^\w\u0400-\u04ff]", "_", (name or "").strip())
    return s or "col_" + str(abs(hash(name)))[:8]


def _safe_headers_from_fieldnames(fieldnames: list[str]) -> list[str]:
    seen: set[str] = set()
    safe_headers: list[str] = []
    for i, h in enumerate(fieldnames):
        name = _sanitize_column(h) or f"col_{i}"
        while name in seen:
            name = name + "_" + str(i)
        seen.add(name)
        safe_headers.append(name)
    return safe_headers


def _cell_sqlite(value: Any, max_len: int) -> str:
    """Текст для SQLite: без U+0000 (иначе pysqlite может обрезать/ломать строку)."""
    if value is None:
        return ""
    s = str(value).replace("\x00", "")
    return s[:max_len] if len(s) > max_len else s


def _write_table_to_db(rows: list[dict[str, Any]], fieldnames: list[str], db_path: str) -> None:
    """Создаёт таблицу announcements в SQLite и вставляет строки. Все колонки TEXT."""
    db_abs = str(Path(db_path).resolve())
    safe_headers = _safe_headers_from_fieldnames(fieldnames)

    conn = sqlite3.connect(db_abs)
    try:
        conn.execute("PRAGMA encoding = 'UTF-8'")
        cur = conn.cursor()
        cols_sql = ", ".join(f'"{h}" TEXT' for h in safe_headers)
        # Схема зависит от набора полей в выгрузке (новые ключи карточки — новые колонки).
        # CREATE IF NOT EXISTS не обновляет старую таблицу → OperationalError при INSERT.
        cur.execute("DROP TABLE IF EXISTS announcements")
        cur.execute(f"CREATE TABLE announcements ({cols_sql})")
        placeholders = ", ".join("?" * len(safe_headers))
        cols_quoted = ", ".join(f'"{h}"' for h in safe_headers)
        max_cell = 1_000_000
        insert_sql = f"INSERT INTO announcements ({cols_quoted}) VALUES ({placeholders})"
        batch = [
            tuple(_cell_sqlite(r.get(k, ""), max_cell) for k in fieldnames)
            for r in rows
        ]
        if batch:
            cur.executemany(insert_sql, batch)
        conn.commit()
    finally:
        conn.close()
    logger.info("SQLite: записано строк: %s → %s", len(rows), db_abs)


class _IncrementalAnnouncementsWriter:
    """SQLite: SLIM_DB_COLUMNS; по одной строке на каждый лот в карточке (см. slim_rows_from_card)."""

    _MAX_CELL = 1_000_000

    def __init__(self, db_path: str) -> None:
        self.db_abs = str(Path(db_path).resolve())
        self._conn = sqlite3.connect(self.db_abs)
        self._conn.execute("PRAGMA encoding = 'UTF-8'")
        self._cur = self._conn.cursor()
        self._cur.execute("DROP TABLE IF EXISTS announcements")
        self._conn.commit()
        self._fields = list(SLIM_DB_COLUMNS)
        safe = _safe_headers_from_fieldnames(self._fields)
        cols_sql = ", ".join(f'"{h}" TEXT' for h in safe)
        self._cur.execute(f"CREATE TABLE announcements ({cols_sql})")
        self._conn.commit()
        self._quoted_cols = ", ".join(f'"{h}"' for h in safe)
        self.total_rows = 0

    def write_card(self, item: dict[str, Any]) -> None:
        batch_rows = slim_rows_from_card(item)
        placeholders = ", ".join("?" * len(self._fields))
        insert_sql = (
            f"INSERT INTO announcements ({self._quoted_cols}) VALUES ({placeholders})"
        )
        for row in batch_rows:
            tup = tuple(_cell_sqlite(row.get(k, ""), self._MAX_CELL) for k in self._fields)
            self._cur.execute(insert_sql, tup)
            self.total_rows += 1
        self._conn.commit()
        logger.info(
            "БД: +%s строк по карточке (лотов в записи: %s, всего строк в таблице: %s) → %s",
            len(batch_rows),
            len(batch_rows),
            self.total_rows,
            self.db_abs,
        )

    def close(self) -> None:
        self._conn.close()


def _message_id_from_url(url: str) -> str | None:
    """Извлекает ID сообщения: MessageWindow.aspx?ID=… или https://fedresurs.ru/bankruptmessages/{ID}."""
    try:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        ids = qs.get("ID") or qs.get("id")
        if ids and ids[0]:
            return ids[0].strip()
        m = re.search(r"/bankruptmessages/([A-Fa-f0-9]{32})(?:/|$|\?|#)", parsed.path or "", re.I)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def _env_card_old_portal() -> bool:
    """Старый MessageWindow на old.bankrot (редиректит на fedresurs). FEDRESURS_CARD_OLD_PORTAL=1."""
    v = (os.environ.get("FEDRESURS_CARD_OLD_PORTAL") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _env_card_public_fedresurs() -> bool:
    """По умолчанию True: карточка https://fedresurs.ru/bankruptmessages/{GUID} (извлечение: DOM + /backend/…).
    Отключить: FEDRESURS_CARD_OLD_PORTAL=1 или FEDRESURS_CARD_PUBLIC=0."""
    if _env_card_old_portal():
        return False
    v = (os.environ.get("FEDRESURS_CARD_PUBLIC") or "").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def _resolve_card_url(url: str) -> str:
    """URL для загрузки карточки в браузере.

    По умолчанию: https://fedresurs.ru/bankruptmessages/{GUID} (тот же ID, что в MessageWindow.aspx?ID=).
    Старый портал: FEDRESURS_CARD_OLD_PORTAL=1 → MessageWindow.aspx на old.bankrot.
    """
    u = (url or "").strip()
    if not u:
        return u
    low = u.lower()
    mid = _message_id_from_url(u)
    if not mid:
        return u
    mid_public = mid.upper() if re.fullmatch(r"(?i)[A-F0-9]{32}", mid) else mid
    use_public = _env_card_public_fedresurs()
    if use_public:
        if "bankruptmessages" in low and "fedresurs.ru" in low:
            parsed = urlparse(u.split("#")[0])
            path = parsed.path or ""
            mpath = re.search(r"/bankruptmessages/([A-Fa-f0-9]{32})", path, re.I)
            if mpath:
                fixed = f"{FEDRESURS_PUBLIC}/bankruptmessages/{mpath.group(1).upper()}"
                if parsed.query:
                    fixed += "?" + parsed.query
                return fixed
            return u.split("#")[0]
        return f"{FEDRESURS_PUBLIC}/bankruptmessages/{mid_public}"
    if u.startswith("http") and "old.bankrot.fedresurs.ru" in low:
        if "messagewindow" in low or "messagecard" in low:
            return u.split("#")[0]
    if "messagewindow" in low or "messagecard" in low:
        if u.startswith("/"):
            return f"{BASE_URL}{u.split('#')[0]}"
        if u.startswith("http"):
            return u.split("#")[0]
    return f"{BASE_URL}/MessageWindow.aspx?ID={mid}"


def _card_navigation_referer(open_url: str, current_page_url: str) -> str:
    """Referer для перехода на карточку. bankruptmessages при Referer только с old.bankrot часто даёт HTTP 403."""
    ou = (open_url or "").strip().lower()
    if (
        "fedresurs.ru" in ou
        and "bankruptmessages" in ou
        and _env_card_public_fedresurs()
    ):
        return f"{FEDRESURS_PUBLIC}/"
    cu = (current_page_url or "").strip()
    return cu if cu.startswith("http") else MESSAGES_URL


# fetch из контекста страницы fedresurs.ru (куки, CORS same-site) — несколько путей backend.
_FETCH_BANKRUPT_MESSAGE_JS = """
async (guid) => {
  const urls = [
    'https://fedresurs.ru/backend/bankruptmessages/' + guid,
    'https://fedresurs.ru/backend/bankrupt-messages/' + guid,
    'https://fedresurs.ru/backend/BankruptMessages/' + guid,
    'https://fedresurs.ru/backend/bankruptmessage/' + guid,
    'https://fedresurs.ru/backend/efrsb/bankruptmessages/' + guid,
    'https://fedresurs.ru/backend/v1/bankruptmessages/' + guid,
    'https://fedresurs.ru/backend/messages/bankrupt/' + guid,
  ];
  const ref = (typeof location !== 'undefined' && location.href) ? location.href : 'https://fedresurs.ru/';
  for (const u of urls) {
    try {
      const r = await fetch(u, {
        credentials: 'include',
        headers: {
          Accept: 'application/json, text/plain, */*',
          'X-Requested-With': 'XMLHttpRequest',
          Referer: ref,
        },
      });
      if (r.ok) {
        const text = await r.text();
        try {
          return { ok: true, fetchUrl: u, json: JSON.parse(text) };
        } catch (e) {
          continue;
        }
      }
    } catch (e) {
      continue;
    }
  }
  return { ok: false };
}
"""


def _parse_bankrupt_backend_json(data: Any) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """Разбор JSON карточки с backend fedresurs.ru: плоские поля + массивы лотов."""
    fields: dict[str, str] = {}
    lots_out: list[dict[str, Any]] = []
    if not isinstance(data, dict):
        return fields, lots_out

    lot_array_keys = (
        "lots",
        "propertyLots",
        "auctionLots",
        "tradeLots",
        "lotList",
        "lotsInfo",
        "lotInfos",
        "messageLots",
    )

    def add_lots_from(obj: Any) -> None:
        if not isinstance(obj, dict):
            return
        for key in lot_array_keys:
            arr = obj.get(key)
            if isinstance(arr, list):
                for item in arr:
                    if isinstance(item, dict):
                        lots_out.append(item)

    add_lots_from(data)

    def scalar_fields(obj: dict[str, Any], prefix: str = "") -> None:
        for k, v in obj.items():
            if k in lot_array_keys:
                continue
            name = f"{prefix}{k}" if not prefix else f"{prefix}.{k}"
            if isinstance(v, dict):
                add_lots_from(v)
                scalar_fields(v, name)
            elif isinstance(v, list):
                if v and isinstance(v[0], dict):
                    for i, it in enumerate(v):
                        if isinstance(it, dict):
                            add_lots_from(it)
                            scalar_fields(it, f"{name}[{i}]")
                elif v:
                    fields[name] = "; ".join(str(x) for x in v[:30])
            elif v is not None and not isinstance(v, (dict, list)):
                fields[name] = str(v)

    scalar_fields(data)

    for nest in ("content", "data", "message", "bankruptMessage", "messageContent", "body"):
        sub = data.get(nest)
        if isinstance(sub, dict):
            add_lots_from(sub)
            for k, v in sub.items():
                if k in lot_array_keys:
                    continue
                if isinstance(v, (dict, list)):
                    continue
                if v is not None:
                    fields[f"{nest}.{k}"] = str(v)

    return fields, lots_out


def _try_backend_bankrupt_message(page: Any, guid: str) -> tuple[dict[str, str], list[dict[str, Any]]]:
    if not re.fullmatch(r"(?i)[A-F0-9]{32}", guid or ""):
        return {}, []
    try:
        res = page.evaluate(_FETCH_BANKRUPT_MESSAGE_JS, guid)
    except Exception:
        return {}, []
    if not isinstance(res, dict) or not res.get("ok") or not isinstance(res.get("json"), dict):
        return {}, []
    return _parse_bankrupt_backend_json(res["json"])


def _record_card_url(page: Any, *candidates: str | None) -> str:
    """URL для БД: фактический page.url после goto; иначе первый непустой candidate (open_url, ссылка из списка)."""
    pu = (getattr(page, "url", None) or "").strip()
    if pu.startswith("http://") or pu.startswith("https://"):
        return pu.split("#")[0]
    for c in candidates:
        s = (c or "").strip()
        if s:
            return s.split("#")[0]
    return ""


def _extract_card_data(page: Any, url: str, opened_as: str | None = None) -> dict[str, Any]:
    """Извлекает с открытой страницы карточки все поля и лоты (таблицы, dl, и т.д.).
    Лоты приводятся к единому порядку: только канонические поля (LOT_FIELDS) и только реальные лоты.
    Для fedresurs.ru/bankruptmessages/ дополнительно подтягивается JSON с /backend/… в контексте страницы.
    """
    page_u = (getattr(page, "url", None) or "").strip()
    msg_id = _message_id_from_url(page_u) or _message_id_from_url(url) or url
    try:
        be_fields: dict[str, str] = {}
        be_lots: list[dict[str, Any]] = []
        page_url = (getattr(page, "url", None) or "").lower()
        on_public_card = "fedresurs.ru" in page_url and "bankruptmessages" in page_url
        if not on_public_card:
            ulow = (url or "").lower()
            on_public_card = "fedresurs.ru" in ulow and "bankruptmessages" in ulow
        guid = _message_id_from_url(getattr(page, "url", "") or "") or _message_id_from_url(url or "")
        if not guid and isinstance(msg_id, str) and re.fullmatch(r"(?i)[A-F0-9]{32}", msg_id):
            guid = msg_id
        if on_public_card and guid:
            be_fields, be_lots = _try_backend_bankrupt_message(page, guid)
            if be_fields or be_lots:
                logger.debug("backend карточки: полей=%s, сырых лотов=%s", len(be_fields), len(be_lots))

        raw = page.evaluate(_EXTRACT_CARD_DATA_JS)
        dom_fields = raw.get("fields") or {}
        dom_lots = raw.get("lots") or []
        fields = {**dom_fields, **be_fields}
        lots_raw = list(be_lots) if be_lots else list(dom_lots)
        lots = _apply_lots_policy(lots_raw)
        if not lots and fields:
            lots = _try_synthetic_lot_from_fields(fields)
        # Объявление о торгах по смыслу всегда с лотом; если вёрстка не дала таблицу — одна строка лота (как в БД).
        if not lots and fields:
            lots = [{f: "" for f in LOT_FIELDS}]
        return {"url": _record_card_url(page, opened_as, url), "id": msg_id, "fields": fields, "lots": lots}
    except Exception as e:
        return {"url": _record_card_url(page, opened_as, url), "id": msg_id, "fields": {}, "lots": [], "_error": str(e)}


def _extract_card_data_with_stale_public_fallback(page: Any, url: str, open_url: str) -> dict[str, Any]:
    """Если публичная карточка (по умолчанию) без полей — один переход на MessageWindow.aspx (запасной разбор)."""
    data = _extract_card_data(page, url, open_url)
    ou = (open_url or "").lower()
    if (
        _env_card_public_fedresurs()
        and "fedresurs.ru" in ou
        and "bankruptmessages" in ou
        and not data.get("_error")
        and not (data.get("fields") or {})
        and not (data.get("lots") or [])
    ):
        mid_fb = _message_id_from_url(url) or _message_id_from_url(open_url)
        if mid_fb:
            alt = f"{BASE_URL}/MessageWindow.aspx?ID={mid_fb}"
            try:
                logger.info("публичная карточка без данных — fallback: %s", alt)
                page.goto(alt, wait_until="domcontentloaded", timeout=60_000, referer=MESSAGES_URL)
                page.wait_for_timeout(800)
                return _extract_card_data(page, url, open_url)
            except Exception as e:
                logger.warning("fallback MessageWindow после пустой публичной карточки: %s", e)
    return data


def _make_search_action(
    collected_links: list[tuple[str, str]],
    stats: dict,
    date_from: str | None = None,
    date_to: str | None = None,
    use_modal: bool = False,
    manual_type: bool = False,
    open_each: bool = False,
    extract_table: bool = False,
    collected_data: list[dict[str, Any]] | None = None,
    collect_links_only: bool = False,
) -> Callable:
    """
    use_modal: выбор типа через модалку (видимый браузер).
    manual_type: пауза 15 с — пользователь вручную выбирает тип, затем скрипт продолжает (95/133/168).
    Иначе — JS, сервер часто игнорирует (~37).
    """

    def action(page):
        # Для обхода карточек — больше времени на загрузку MessageWindow
        page.set_default_timeout(60_000 if (open_each or extract_table) else 10_000)

        if manual_type:
            # Режим ручного выбора: открыт браузер, 15 с на выбор типа в форме, потом скрипт продолжит
            page.wait_for_timeout(15_000)
        elif use_modal:
            # Выбор типа через модалку (работает с headless=False)
            try:
                page.set_default_timeout(12_000)
                page.locator(f"#{MESSAGE_TYPE_FIELD_ID}").scroll_into_view_if_needed()
                page.locator(f"#{MESSAGE_TYPE_FIELD_ID}").click()
                page.wait_for_selector('iframe[src*="MessageTypeSelect"]', timeout=6_000)
                page.wait_for_timeout(1000)
                frame = page.frame_locator('iframe[src*="MessageTypeSelect"]')
                frame.locator('span.rtIn', has_text=re.compile(re.escape("проведении торгов"))).first.wait_for(state='visible', timeout=8_000)
                frame.locator('span.rtIn', has_text=re.compile(re.escape("проведении торгов"))).first.click()
                page.wait_for_timeout(400)
                frame.locator('input[value="Выбрать"]').or_(frame.get_by_role('button', name='Выбрать')).first.click()
                page.wait_for_timeout(800)
                try:
                    page.wait_for_selector('iframe[src*="MessageTypeSelect"]', state='detached', timeout=5_000)
                except Exception:
                    pass
                page.evaluate("""document.querySelectorAll('[id^="RadWindowWrapper_"]').forEach(el=>{el.style.display='none'}); document.querySelectorAll('.TelerikModalOverlay').forEach(el=>{el.style.display='none'});""")
                page.wait_for_timeout(200)
            except Exception:
                page.evaluate("""document.querySelectorAll('[id^="RadWindowWrapper_"]').forEach(el=>{el.style.display='none'}); document.querySelectorAll('.TelerikModalOverlay').forEach(el=>{el.style.display='none'});""")
            page.set_default_timeout(60_000 if (open_each or extract_table) else 10_000)
        else:
            # Тип через JS (в headless сервер часто не принимает — будет ~37)
            page.evaluate(
                """
                (typeText) => {
                    var fid = '""" + MESSAGE_TYPE_FIELD_ID + """';
                    var textEl = document.getElementById(fid);
                    if (textEl) { textEl.value = typeText; textEl.dispatchEvent(new Event('input', { bubbles: true })); textEl.dispatchEvent(new Event('change', { bubbles: true })); }
                    var cs = document.querySelector('input[id*="mdsMessageType"][id*="ClientState"]') || document.querySelector('input[name*="mdsMessageType_ClientState"]');
                    if (cs) cs.value = JSON.stringify({ logEntries: [], value: typeText, text: typeText, enabled: true });
                }
                """,
                MESSAGE_TYPE_TRADE,
            )
            page.wait_for_timeout(400)

        if date_from and date_to:
            page.locator(f"#{DATE_FROM_ID}").fill(date_from)
            page.locator(f"#{DATE_TO_ID}").fill(date_to)

        page.get_by_role("button", name="Поиск").click()
        page.wait_for_timeout(3000)
        try:
            page.wait_for_function(
                """() => {
                  for (const a of document.querySelectorAll('a')) {
                    const h = (a.getAttribute('href') || '') + (a.getAttribute('onclick') || '');
                    if (/MessageWindow|MessageCard|bankruptmessages/i.test(h)) return true;
                  }
                  return document.querySelectorAll('a[href*="MessageWindow"], a[href*="MessageCard"], a[href*="bankruptmessages"]').length >= 1;
                }""",
                timeout=8_000,
            )
            page.wait_for_timeout(500)
        except Exception:
            pass

        seen_ids_in_loop: set[str] = set()
        next_page_num = 2
        max_pages = 50  # защита от бесконечного цикла
        while stats["pages"] < max_pages:
            try:
                page.locator("table").first.scroll_into_view_if_needed(timeout=3_000)
                page.wait_for_timeout(200)
            except Exception:
                pass
            skip_type_filter = manual_type or extract_table or open_each
            chunk = page.evaluate(_build_extract_trade_links_js(skip_type_filter))
            # Только новые по ID сообщения (один ID = одна запись)
            new_items = []
            for item in chunk:
                url = (item.get("fullUrl") or "").strip()
                if not url:
                    continue
                url = _resolve_card_url(url)
                msg_id = _message_id_from_url(url) or url
                if msg_id in seen_ids_in_loop:
                    continue
                seen_ids_in_loop.add(msg_id)
                new_items.append((item.get("linkText", ""), url))
            if new_items:
                for text, url in new_items:
                    collected_links.append((text, url))
                stats["messages"] += len(new_items)
            stats["pages"] += 1
            if extract_table or open_each:
                logger.info(
                    "пагинация: обработана страница %s, уникальных ссылок в списке: %s, новых на шаге: %s",
                    stats["pages"],
                    len(collected_links),
                    len(new_items),
                )

            # Следующая страница: см. _click_next_pagination_page (сначала «Следующая», не только Page$N)
            try:
                pause_ms = random.randint(2_000, 7_000)
                logger.debug("пагинация: случайная пауза %s мс перед следующей страницей", pause_ms)
                page.wait_for_timeout(pause_ms)
                if not _click_next_pagination_page(page, next_page_num):
                    logger.info(
                        "пагинация: следующая страница не найдена после страницы %s (конец списка или сменилась вёрстка)",
                        stats["pages"],
                    )
                    break
                _wait_after_pagination_click(page)
                next_page_num += 1
            except Exception as e:
                logger.error("пагинация остановлена на странице %s: %s", stats["pages"], e)
                break

        # Режим «зайти внутрь» каждого объявления (для --table обход делается отдельно через Playwright)
        visit_links = (open_each or extract_table) and collected_links and (collected_data is not None)
        if visit_links and not collect_links_only:
            seen_ids_visit: set[str] = set()
            to_visit: list[tuple[str, str]] = []
            for text, url in collected_links:
                mid = _message_id_from_url(url) or url
                if mid not in seen_ids_visit:
                    seen_ids_visit.add(mid)
                    to_visit.append((text, url))
            logger.info("--- Переход по карточкам: %s объявлений ---", len(to_visit))
            for i, (text, url) in enumerate(to_visit, 1):
                open_url = _resolve_card_url(url)
                if open_url != url:
                    logger.info("карточка: открываем %s (вместо %s)", open_url, url)
                try:
                    pu = (getattr(page, "url", None) or "").strip()
                    page.goto(
                        open_url,
                        wait_until="domcontentloaded",
                        timeout=15_000,
                        referer=_card_navigation_referer(open_url, pu),
                    )
                    if _env_card_humanize():
                        _human_scroll_document(page)
                        page.wait_for_timeout(int(200 + random.random() * 380))
                    else:
                        page.wait_for_timeout(800)
                except Exception as e:
                    logger.error("[%s/%s] ошибка перехода: %s: %s", i, len(to_visit), open_url, e)
                    continue
                data = _extract_card_data_with_stale_public_fallback(page, url, open_url)
                collected_data.append(data)
                logger.info(
                    "[%s/%s] сырых полей: %s, лотов после фильтра: %s → в БД по строке на лот",
                    i,
                    len(to_visit),
                    len(data.get("fields", {})),
                    len(data.get("lots", [])),
                )
                if open_each and not extract_table:
                    answer = input("Enter — следующее объявление, q — выход: ").strip().lower()
                    if answer in ("q", "й", "exit", "quit"):
                        break

    return action


# Для --table: только пагинация в первом fetch; для --open-each — пагинация + карточки в одном fetch.
_FETCH_TIMEOUT_LONG_MS = 3_600_000  # 1 час


def _playwright_launch_browser(p: Any, *, headless: bool, prefer_system_chrome: bool) -> Any:
    """Встроенный Chromium Playwright иногда не открывает отдельные гос.сайты; системный Chrome/Edge обычно работает."""
    kw: dict[str, Any] = {"headless": headless}
    if not prefer_system_chrome:
        logger.info("Playwright: встроенный Chromium (--bundled-chromium)")
        return p.chromium.launch(**kw)
    for channel, label in (("chrome", "Google Chrome"), ("msedge", "Microsoft Edge")):
        try:
            browser = p.chromium.launch(channel=channel, **kw)
            logger.info("Playwright: %s (channel=%s)", label, channel)
            return browser
        except Exception as e:
            logger.debug("%s недоступен: %s", label, e)
    logger.warning(
        "Системный Chrome/Edge не найден для Playwright — используется встроенный Chromium. "
        "Если сайт не открывается, установите Chrome или выполните: playwright install chrome"
    )
    return p.chromium.launch(**kw)


def _playwright_connect_or_launch(p: Any, *, headless: bool, prefer_system_chrome: bool) -> Any:
    ws = _resolve_cdp_ws_url()
    if ws:
        logger.info(
            "Playwright: connect_over_cdp к уже запущенному браузеру (новый контекст = отдельное окно, см. FEDRESURS_CDP_PORT)."
        )
        return p.chromium.connect_over_cdp(ws)
    return _playwright_launch_browser(p, headless=headless, prefer_system_chrome=prefer_system_chrome)


def _env_prefer_system_browser() -> bool:
    v = (os.environ.get("FEDRESURS_USE_BUNDLED_CHROMIUM") or "").strip().lower()
    return v not in ("1", "true", "yes")


def _env_ignore_https_errors() -> bool:
    """Игнорировать ошибки TLS (корпоративный прокси, нестандартная цепочка). Отключить: FEDRESURS_STRICT_SSL=1."""
    v = (os.environ.get("FEDRESURS_STRICT_SSL") or "").strip().lower()
    return v not in ("1", "true", "yes")


def _env_messages_google_referer() -> bool:
    """Как в scrapling по умолчанию: первый GET с referer google.com (меньше расхождений с Sec-Fetch-* и WAF).
    Отключить: FEDRESURS_NO_GOOGLE_REFERER=1 — тогда подставляется Referer с fedresurs.ru (см. fetch_page)."""
    v = (os.environ.get("FEDRESURS_NO_GOOGLE_REFERER") or "").strip().lower()
    return v not in ("1", "true", "yes", "on")


def _fetch_locale() -> str | None:
    """Локаль контекста браузера (Accept-Language, navigator.language).
    Не задано в окружении — ru-RU; FEDRESURS_LOCALE= (пусто) — как у системы (не передаём в fetcher)."""
    raw = os.environ.get("FEDRESURS_LOCALE")
    if raw is None:
        return "ru-RU"
    v = raw.strip()
    return v or None


def _resolve_cdp_ws_url() -> str | None:
    """WebSocket CDP для connect_over_cdp: FEDRESURS_CDP_URL=ws://... или FEDRESURS_CDP_PORT=9222 (запрос /json/version)."""
    direct = (os.environ.get("FEDRESURS_CDP_URL") or "").strip()
    if direct:
        if not direct.startswith(("ws://", "wss://")):
            logger.warning("FEDRESURS_CDP_URL должен быть ws:// или wss:// (получено: %s…)", direct[:48])
            return None
        return direct
    port = (os.environ.get("FEDRESURS_CDP_PORT") or "").strip()
    if not port:
        return None
    ver_url = f"http://127.0.0.1:{port}/json/version"
    try:
        with urlopen(ver_url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except (URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        logger.warning(
            "FEDRESURS_CDP_PORT=%s: не удалось прочитать %s (%s). Запустите Chrome с --remote-debugging-port=%s",
            port,
            ver_url,
            e,
            port,
        )
        return None
    ws = data.get("webSocketDebuggerUrl")
    if not ws:
        logger.warning("В ответе %s нет webSocketDebuggerUrl", ver_url)
        return None
    return ws


def _stealth_retries() -> int:
    """Повторы StealthyFetcher при сбое. По умолчанию 1 — после закрытия окна ретраи обычно только ломают контекст. 1–10: FEDRESURS_STEALTH_RETRIES."""
    raw = (os.environ.get("FEDRESURS_STEALTH_RETRIES") or "1").strip()
    try:
        n = int(raw)
    except ValueError:
        return 1
    return max(1, min(10, n))


def _env_card_humanize() -> bool:
    """По умолчанию вкл.: скролл вниз + пауза между карточками. Отключить: FEDRESURS_CARD_FAST=1 или FEDRESURS_CARD_HUMANIZE=0."""
    fast = (os.environ.get("FEDRESURS_CARD_FAST") or "").strip().lower()
    if fast in ("1", "true", "yes", "on"):
        return False
    v = (os.environ.get("FEDRESURS_CARD_HUMANIZE") or "").strip().lower()
    if v in ("0", "false", "no", "off"):
        return False
    return True


def _card_gap_base_ms() -> int:
    """Базовая пауза между карточками (мс); джиттер ±22%%. По умолчанию 5000 (~12 карточек/мин). Переопределение: FEDRESURS_CARD_GAP_MS."""
    raw = (os.environ.get("FEDRESURS_CARD_GAP_MS") or "5000").strip()
    try:
        base = int(raw)
    except ValueError:
        base = 5000
    return max(0, min(180_000, base))


def _pause_between_cards_ms() -> int:
    b = _card_gap_base_ms()
    if b <= 0:
        return 0
    return int(b * random.uniform(0.78, 1.22))


def _human_scroll_document(page: Any) -> None:
    """Пошаговая прокрутка вниз (как при чтении длинной страницы)."""
    try:
        for _ in range(48):
            at_end = page.evaluate(
                """() => {
                  const z = document.scrollingElement || document.documentElement;
                  if (!z) return true;
                  const maxy = Math.max(0, z.scrollHeight - z.clientHeight);
                  if (z.scrollTop >= maxy - 1) return true;
                  const step = Math.min(260 + Math.floor(Math.random() * 200), maxy - z.scrollTop + 1);
                  z.scrollBy(0, step);
                  return false;
                }"""
            )
            if at_end:
                break
            page.wait_for_timeout(int(40 + random.random() * 110))
    except Exception:
        try:
            page.evaluate(
                "() => { const z = document.scrollingElement || document.documentElement; if (z) z.scrollTo(0, z.scrollHeight); }"
            )
        except Exception:
            pass


def _env_portal_warmup() -> bool:
    """Сначала главная fedresurs.ru, затем Messages.aspx — браузер сам шлёт Referer с портала (как при ручном переходе).
    Отключить: FEDRESURS_NO_PORTAL_WARMUP=1."""
    v = (os.environ.get("FEDRESURS_NO_PORTAL_WARMUP") or "").strip().lower()
    return v not in ("1", "true", "yes", "on")


def _url_base_path(url: str) -> str:
    return url.split("?", 1)[0].rstrip("/")


def _use_portal_warmup_for_url(url: str) -> bool:
    return _env_portal_warmup() and _url_base_path(url) == _url_base_path(MESSAGES_URL)


def _goto_bankrot_messages(
    page: Any, messages_url: str, timeout_ms: int, referer: str | None = None
) -> Any:
    """Переход на Messages.aspx. Переживает гонку редиректов/скриптов на корне (Playwright: navigation interrupted)."""
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            kw: dict[str, Any] = {
                "wait_until": "domcontentloaded",
                "timeout": timeout_ms,
            }
            if referer is not None:
                kw["referer"] = referer
            return page.goto(messages_url, **kw)
        except Exception as e:
            last_exc = e
            if "interrupted by another navigation" not in str(e).lower():
                raise
            logger.warning(
                "Переход на Messages.aspx прерван другой навигацией (попытка %s/3): %s",
                attempt + 1,
                e,
            )
            page.wait_for_timeout(400 + attempt * 200)
            try:
                if "Messages.aspx" in (page.url or ""):
                    return None
            except Exception:
                pass
    assert last_exc is not None
    raise last_exc


def _env_list_playwright_fallback() -> bool:
    """После 401 у Stealthy — одна попытка списка через голый Playwright. Отключить: FEDRESURS_NO_LIST_PLAYWRIGHT_FALLBACK=1."""
    v = (os.environ.get("FEDRESURS_NO_LIST_PLAYWRIGHT_FALLBACK") or "").strip().lower()
    return v not in ("1", "true", "yes", "on")


def _env_list_skip_stealth() -> bool:
    """Сразу только Playwright для списка (без StealthyFetcher). FEDRESURS_LIST_USE_PLAYWRIGHT_ONLY=1."""
    v = (os.environ.get("FEDRESURS_LIST_USE_PLAYWRIGHT_ONLY") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _portal_then_messages_page_action(
    messages_url: str,
    timeout_ms: int,
    inner: Callable | None,
) -> Callable:
    """После первого goto (портал): корень old.bankrot → Messages.aspx → page_action. Возвращает HTTP-код страницы списка (или 200 после inner)."""

    bankrot_root = f"{BASE_URL}/"

    def action(page: Any) -> int:
        try:
            r0 = page.goto(bankrot_root, wait_until="domcontentloaded", timeout=timeout_ms)
            if r0 is not None and getattr(r0, "status", 200) >= 400:
                logger.warning("Корень %s ответил HTTP %s — всё равно переходим к списку", bankrot_root, r0.status)
            page.wait_for_timeout(800)
            r = _goto_bankrot_messages(page, messages_url, timeout_ms)
            if r is not None and getattr(r, "status", 200) >= 400:
                logger.error(
                    "Список сообщений HTTP %s — формы нет, дальнейший page_action бессмыслен. "
                    "Не закрывайте окно до текста ошибки скрипта: при закрытии Chrome возможны ошибки контекста. "
                    "Если корень bankrot тоже дал 401 — сайт режет автоматизацию; см. FEDRESURS_CDP_PORT, сеть/прокси.",
                    r.status,
                )
                return int(r.status)
        except Exception as e:
            logger.error("Переход к списку сообщений: %s", e)
            raise
        if inner is not None:
            inner(page)
        return 200

    return action


PORTAL_ENTRY_URL = f"{FEDRESURS_PUBLIC}/"


_PLAYWRIGHT_COOKIE_KEYS = frozenset(
    {"name", "value", "domain", "path", "expires", "httpOnly", "secure", "sameSite"}
)


def _cookies_for_playwright(cookies: Any) -> list[dict[str, Any]]:
    """Преобразует cookies из ответа scrapling в формат Playwright add_cookies."""
    if not cookies:
        return []
    seq = cookies if isinstance(cookies, (list, tuple)) else (cookies,)
    default_host = urlparse(MESSAGES_URL).hostname or "old.bankrot.fedresurs.ru"
    out: list[dict[str, Any]] = []
    for c in seq:
        if not isinstance(c, dict):
            continue
        if c.get("name") is None or c.get("value") is None:
            continue
        entry: dict[str, Any] = {
            k: c[k] for k in _PLAYWRIGHT_COOKIE_KEYS if k in c and c[k] is not None
        }
        if "sameSite" in entry and str(entry["sameSite"]) not in ("Strict", "Lax", "None"):
            del entry["sameSite"]
        entry.setdefault("path", "/")
        if "domain" not in entry:
            entry["domain"] = default_host
        out.append(entry)
    return out


def _browser_context_kw_for_cards(list_response: Response | None) -> dict[str, Any]:
    """Заголовки и UA как у сессии со списком.
    Для карточек fedresurs.ru/bankruptmessages Referer с портала (а не только Messages.aspx на old.bankrot) —
    иначе запросы к новому URL часто получают 403.
    """
    ref = f"{FEDRESURS_PUBLIC}/" if _env_card_public_fedresurs() else MESSAGES_URL
    headers = {
        "Referer": ref,
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    }
    # Как у scrapling Stealth — меньше отличий от «живого» окна, WAF реже режет.
    kw: dict[str, Any] = {
        "locale": "ru-RU",
        "extra_http_headers": headers,
        "viewport": {"width": 1920, "height": 1080},
        "screen": {"width": 1920, "height": 1080},
        "has_touch": False,
        "is_mobile": False,
    }
    if list_response:
        rh = getattr(list_response, "request_headers", None) or {}
        ua = rh.get("user-agent") or rh.get("User-Agent")
        if ua:
            kw["user_agent"] = ua
    return kw


def _sync_playwright_for_cards() -> tuple[Any, str]:
    """Patchright (как у scrapling) предпочтительнее обычного Playwright при 403 от WAF."""
    try:
        from patchright.sync_api import sync_playwright

        return sync_playwright, "patchright"
    except ImportError:
        try:
            from playwright.sync_api import sync_playwright

            return sync_playwright, "playwright"
        except ImportError as e:
            raise RuntimeError(
                "Нужен patchright (рекомендуется: pip install patchright) или playwright"
            ) from e


def _visit_cards_playwright(
    collected_links: list[tuple[str, str]],
    collected_data: list[dict[str, Any]],
    db_path: str | None = None,
    prefer_system_chrome: bool = True,
    list_response: Response | None = None,
    *,
    wide_table: bool = False,
) -> int:
    """Обход карточек отдельным браузером (patchright или Playwright).

    list_response: ответ первой сессии (список) — переносим cookies и User-Agent, иначе новый браузер часто получает 403.

    При переданном db_path после каждой карточки выполняется commit в SQLite. Возвращает число строк, записанных в БД.
    """
    sync_playwright, pw_backend = _sync_playwright_for_cards()

    seen_ids: set[str] = set()
    to_visit: list[str] = []
    for _text, url in collected_links:
        mid = _message_id_from_url(url) or url
        if mid not in seen_ids:
            seen_ids.add(mid)
            to_visit.append(url)

    if not to_visit:
        logger.warning("Нет ссылок для обхода карточек.")
        return 0

    writer: _IncrementalAnnouncementsWriter | None = None
    rows_written = 0
    if db_path and not wide_table:
        writer = _IncrementalAnnouncementsWriter(db_path)

    logger.info("--- Переход по карточкам (%s): %s объявлений ---", pw_backend, len(to_visit))
    if _env_card_humanize():
        logger.info(
            "%s: карточки — скролл вниз и пауза ~%s мс между карточками (±джиттер); быстрый режим: FEDRESURS_CARD_FAST=1.",
            pw_backend,
            _card_gap_base_ms(),
        )
    try:
        with sync_playwright() as p:
            browser = _playwright_connect_or_launch(p, headless=False, prefer_system_chrome=prefer_system_chrome)
            ctx_kw = _browser_context_kw_for_cards(list_response)
            if _env_ignore_https_errors():
                ctx_kw["ignore_https_errors"] = True
                logger.info(
                    "%s: ignore_https_errors=True (сертификат). Строгий SSL: FEDRESURS_STRICT_SSL=1",
                    pw_backend,
                )
            context = browser.new_context(**ctx_kw)
            if list_response is not None:
                ck = _cookies_for_playwright(getattr(list_response, "cookies", None))
                if ck:
                    try:
                        context.add_cookies(ck)
                        logger.info(
                            "%s: перенесено %s cookie из сессии со списком",
                            pw_backend,
                            len(ck),
                        )
                    except Exception as e:
                        logger.warning("%s: add_cookies не удался: %s", pw_backend, e)
                else:
                    logger.warning(
                        "%s: в ответе списка нет cookies — вероятны 403; не закрывайте окно браузера, "
                        "пока скрипт не закончит сбор списка.",
                        pw_backend,
                    )
            page = context.new_page()
            page.set_default_timeout(60_000)
            if _env_card_public_fedresurs():
                try:
                    home = f"{FEDRESURS_PUBLIC}/"
                    logger.info("%s: прогрев главной %s (сессия для карточек bankruptmessages)", pw_backend, home.rstrip("/"))
                    r_home = page.goto(home, wait_until="domcontentloaded", timeout=60_000)
                    if r_home is not None and r_home.status >= 400:
                        logger.warning("%s: главная fedresurs.ru ответила HTTP %s", pw_backend, r_home.status)
                    page.wait_for_timeout(400)
                except Exception as e:
                    logger.warning("%s: прогрев главной fedresurs.ru не выполнен: %s", pw_backend, e)
            logger.info("Прогрев: открываем %s (та же сессия, что и для карточек)", MESSAGES_URL)
            warm = page.goto(MESSAGES_URL, wait_until="domcontentloaded", timeout=90_000)
            if warm is not None and warm.status >= 400:
                logger.error(
                    "Прогрев: HTTP %s на странице списка — cookie/сессия невалидны, карточки с 403 ожидаемы",
                    warm.status,
                )
            page.wait_for_timeout(1500)
            for i, url in enumerate(to_visit, 1):
                open_url = _resolve_card_url(url)
                if open_url != url:
                    logger.info("карточка: открываем %s (вместо %s)", open_url, url)
                try:
                    open_low = (open_url or "").lower()
                    pu = (getattr(page, "url", None) or "").strip()
                    card_referer = _card_navigation_referer(open_url, pu)
                    nav = page.goto(
                        open_url,
                        wait_until="domcontentloaded",
                        timeout=60_000,
                        referer=card_referer,
                    )
                    if (
                        nav is not None
                        and nav.status in (401, 403, 404)
                        and "fedresurs.ru" in open_low
                        and "bankruptmessages" in open_low
                        and card_referer != MESSAGES_URL
                        and _env_card_public_fedresurs()
                    ):
                        nav = page.goto(
                            open_url,
                            wait_until="domcontentloaded",
                            timeout=60_000,
                            referer=MESSAGES_URL,
                        )
                        if nav is not None and nav.status < 400:
                            logger.info(
                                "[%s/%s] карточка открылась со второй попытки (Referer=%s)",
                                i,
                                len(to_visit),
                                MESSAGES_URL,
                            )
                    if (
                        nav is not None
                        and nav.status in (401, 403, 404)
                        and "fedresurs.ru" in open_low
                        and "bankruptmessages" in open_low
                        and _env_card_public_fedresurs()
                    ):
                        mid_fb = _message_id_from_url(url) or _message_id_from_url(open_url)
                        if mid_fb:
                            alt = f"{BASE_URL}/MessageWindow.aspx?ID={mid_fb}"
                            logger.warning(
                                "[%s/%s] %s HTTP %s — fallback: %s",
                                i,
                                len(to_visit),
                                open_url,
                                nav.status,
                                alt,
                            )
                            nav = page.goto(
                                alt,
                                wait_until="domcontentloaded",
                                timeout=60_000,
                                referer=MESSAGES_URL,
                            )
                    page_low = (page.url or "").lower()
                    if "fedresurs.ru" in page_low and "bankruptmessages" in page_low:
                        try:
                            page.wait_for_load_state("load", timeout=25_000)
                        except Exception:
                            pass
                        page.wait_for_timeout(400)
                    if nav is not None and nav.status >= 400:
                        logger.error(
                            "[%s/%s] HTTP %s при открытии карточки: %s (текущий URL: %s)",
                            i,
                            len(to_visit),
                            nav.status,
                            open_url,
                            page.url,
                        )
                    if _env_card_humanize():
                        _human_scroll_document(page)
                        page.wait_for_timeout(int(200 + random.random() * 380))
                    else:
                        page.wait_for_timeout(800)
                    data = _extract_card_data_with_stale_public_fallback(page, url, open_url)
                    collected_data.append(data)
                    if writer:
                        writer.write_card(data)
                    logger.info(
                        "[%s/%s] сырых полей: %s, лотов после фильтра: %s → в БД по строке на лот",
                        i,
                        len(to_visit),
                        len(data.get("fields", {})),
                        len(data.get("lots", [])),
                    )
                except Exception as e:
                    logger.error("[%s/%s] ошибка карточки: %s: %s", i, len(to_visit), open_url, e)
                    mid = _message_id_from_url(url) or url
                    err_item = {
                        "url": _record_card_url(page, open_url, url),
                        "id": mid,
                        "fields": {},
                        "lots": [],
                        "_error": str(e),
                    }
                    collected_data.append(err_item)
                    if writer:
                        writer.write_card(err_item)
                if _env_card_humanize() and i < len(to_visit):
                    gap = _pause_between_cards_ms()
                    if gap > 0:
                        page.wait_for_timeout(gap)
            browser.close()
    finally:
        if writer:
            rows_written = writer.total_rows
            writer.close()
    if db_path and wide_table:
        rows, fieldnames = _build_rows_and_fieldnames(collected_data)
        _write_table_to_db(rows, fieldnames, db_path)
        return len(rows)
    return rows_written  # 0, если db_path не передан


def _response_from_playwright_list(page: Any, context: Any, status: int) -> Response:
    """Собирает scrapling Response после сценария списка на голом Playwright (cookie для второй фазы)."""
    cookies_tup = tuple(dict(c) for c in context.cookies())
    parser = {**StealthyFetcher._generate_parser_arguments()}
    return Response(
        url=page.url,
        content=page.content().encode("utf-8"),
        status=status,
        reason=StatusText.get(status),
        cookies=cookies_tup,
        headers={},
        request_headers={},
        meta={},
        **parser,
    )


def _fetch_list_playwright_only(
    messages_url: str,
    page_action: Callable | None,
    *,
    headless: bool,
    timeout_ms: int,
    prefer_system_chrome: bool,
    google_search: bool,
    use_portal: bool,
) -> Response:
    """Тот же сценарий списка, что и Stealthy, но без scrapling Stealthy (иногда 401 только на слое patchright/scrapling)."""
    sync_playwright, pw_backend = _sync_playwright_for_cards()
    ref0 = "https://www.google.com/" if google_search else None
    combined = _portal_then_messages_page_action(messages_url, timeout_ms, page_action) if use_portal else None
    logger.info("Список сообщений: канал %s без StealthyFetcher.", pw_backend)
    with sync_playwright() as p:
        browser = _playwright_connect_or_launch(p, headless=headless, prefer_system_chrome=prefer_system_chrome)
        ctx_kw: dict[str, Any] = {
            "viewport": {"width": 1920, "height": 1080},
            "screen": {"width": 1920, "height": 1080},
            "has_touch": False,
            "is_mobile": False,
        }
        loc = _fetch_locale()
        if loc:
            ctx_kw["locale"] = loc
        if _env_ignore_https_errors():
            ctx_kw["ignore_https_errors"] = True
        context = browser.new_context(**ctx_kw)
        page = context.new_page()
        page.set_default_navigation_timeout(timeout_ms)
        page.set_default_timeout(timeout_ms)
        try:
            if use_portal:
                logger.info(
                    "Playwright-список: %s → корень bankrot → Messages.aspx.",
                    PORTAL_ENTRY_URL.rstrip("/"),
                )
                page.goto(PORTAL_ENTRY_URL, referer=ref0, wait_until="domcontentloaded", timeout=timeout_ms)
                st = combined(page) if combined else 200
            else:
                r = _goto_bankrot_messages(page, messages_url, timeout_ms, referer=ref0)
                if r is not None and getattr(r, "status", 200) >= 400:
                    st = int(r.status)
                    logger.error("Список (Playwright) HTTP %s", st)
                else:
                    if page_action is not None:
                        page_action(page)
                    st = 200
            return _response_from_playwright_list(page, context, st)
        finally:
            browser.close()


def fetch_page(
    url: str,
    page_action: Callable | None = None,
    headless: bool = True,
    timeout_ms: int = 60_000,
    real_chrome: bool = False,
    google_search: bool = True,
    extra_headers: dict[str, str] | None = None,
) -> Response:
    # При google_search=False scrapling передаёт в goto referer=None — часть WAF отвечает 401 без Referer.
    # extra_http_headers добавляет Referer ко всем запросам; на первом GET к old.bankrot это может не совпасть с Sec-Fetch-*.
    use_portal = _use_portal_warmup_for_url(url)
    merged_headers = dict(extra_headers or {})
    if not google_search and not use_portal:
        merged_headers.setdefault("Referer", f"{FEDRESURS_PUBLIC}/")
    if use_portal:
        merged_headers.pop("Referer", None)
        fetch_url = PORTAL_ENTRY_URL
        effective_action = _portal_then_messages_page_action(url, timeout_ms, page_action)
        logger.info(
            "Прогрев портала: %s → корень bankrot → Messages.aspx (Referer как у обычного браузера).",
            fetch_url.rstrip("/"),
        )
    else:
        fetch_url = url
        effective_action = page_action

    kwargs = dict(
        headless=headless,
        network_idle=False,
        timeout=timeout_ms,
        wait=0,
        google_search=google_search,
        disable_resources=False,
        # После закрытия окна пользователем лишние ретраи scrapling часто падают на new_page (мёртвый контекст).
        retries=_stealth_retries(),
    )
    loc = _fetch_locale()
    if loc:
        kwargs["locale"] = loc
    if merged_headers:
        kwargs["extra_headers"] = merged_headers
    cdp_ws = _resolve_cdp_ws_url()
    if cdp_ws:
        kwargs["cdp_url"] = cdp_ws
        logger.info(
            "StealthyFetcher: подключение по CDP к уже запущенному Chrome. "
            "Обычно откроется ещё одно окно (новый контекст), не та вкладка, что вы открыли вручную."
        )
    elif real_chrome:
        kwargs["real_chrome"] = True
    if _env_ignore_https_errors():
        # scrapling Stealthy обычно уже с ignore_https_errors; явно дублируем в additional_args
        aa = dict(kwargs.get("additional_args") or {})
        aa.setdefault("ignore_https_errors", True)
        kwargs["additional_args"] = aa
    if effective_action is not None:
        kwargs["page_action"] = effective_action

    if _env_list_skip_stealth():
        return _fetch_list_playwright_only(
            url,
            page_action,
            headless=headless,
            timeout_ms=timeout_ms,
            prefer_system_chrome=real_chrome,
            google_search=google_search,
            use_portal=use_portal,
        )

    page = StealthyFetcher.fetch(fetch_url, **kwargs)
    if page.status == 401 and _env_list_playwright_fallback():
        logger.warning(
            "StealthyFetcher: HTTP 401 — повтор без слоя scrapling (голый Playwright). "
            "Отключить автоповтор: FEDRESURS_NO_LIST_PLAYWRIGHT_FALLBACK=1."
        )
        page = _fetch_list_playwright_only(
            url,
            page_action,
            headless=headless,
            timeout_ms=timeout_ms,
            prefer_system_chrome=real_chrome,
            google_search=google_search,
            use_portal=use_portal,
        )

    if page.status != 200:
        msg = f"Failed to fetch {url}, status={page.status}"
        if page.status == 401:
            msg += (
                ". HTTP 401 на old.bankrot.fedresurs.ru: узел целиком не отдаёт HTML (не только поля дат). "
                "В обычном окне Chrome у вас может быть 200 — это типичный отказ автоматизированному клиенту или прокси. "
                "Попробуйте: FEDRESURS_CDP_PORT к Chrome с --remote-debugging-port и отдельным user-data-dir; "
                "другую сеть без корпоративного SSL/прокси; FEDRESURS_USE_BUNDLED_CHROMIUM=1; "
                "сразу только Playwright для списка: FEDRESURS_LIST_USE_PLAYWRIGHT_ONLY=1. "
                "Прогрев портала: FEDRESURS_NO_PORTAL_WARMUP=1."
            )
        raise RuntimeError(msg)
    return page


def main(
    date_from: str | None = None,
    date_to: str | None = None,
    skip_links_prompt: bool = False,
    print_links: bool = False,
    links_file: str | None = None,
    visible_browser: bool = False,
    manual_type: bool = False,
    open_each: bool = False,
    extract_table: bool = False,
    prefer_system_chrome: bool = True,
):
    """
    manual_type: пауза 15 с для ручного выбора типа в браузере — затем 95/133/168.
    visible_browser + use_modal: автоматический выбор в модалке (часто не срабатывает).
    open_each: после сбора — по очереди открывать каждое объявление (Enter — следующее, q — выход).
    extract_table: пройти по ссылкам и сохранить в SQLite фиксированные поля (url, должник, вид торгов, …).
    """
    if open_each or extract_table:
        visible_browser = True
    collected_links: list[tuple[str, str]] = []
    collected_data: list[dict[str, Any]] = []
    stats: dict = {"messages": 0, "pages": 0}
    use_modal = visible_browser and not manual_type
    page_action = _make_search_action(
        collected_links,
        stats,
        date_from=date_from,
        date_to=date_to,
        use_modal=use_modal,
        manual_type=manual_type,
        open_each=open_each,
        extract_table=extract_table,
        collected_data=collected_data,
        collect_links_only=extract_table,
    )

    if date_from and date_to:
        logger.info("Фильтр по датам: с %s по %s.", date_from, date_to)
    if manual_type:
        logger.info(
            "Тип сообщения: выберите вручную в браузере в течение 15 с («Объявление о проведении торгов»)"
        )
    else:
        logger.info("Тип сообщения: %s (%s)", MESSAGE_TYPE_TRADE, "модалка" if use_modal else "JS")
    if open_each:
        logger.info(
            "Режим: после сбора по очереди откроется каждое объявление; данные (поля + лоты) сохраняются в JSON (Enter — следующее, q — выход)."
        )
    if extract_table:
        logger.info(
            "Режим --table: обход карточек → SQLite announcements (компактная схема; по одной строке на каждый лот карточки)."
        )
    if getattr(args, "table_wide", False):
        logger.info(
            "Режим --table-wide: обход карточек → SQLite announcements (широкая схема: каждое найденное поле/значение = отдельная колонка; строка на лот)."
        )

    # Для --table первый шаг только список + пагинация; карточки — отдельно в Playwright
    fetch_timeout = _FETCH_TIMEOUT_LONG_MS if (open_each or extract_table) else 60_000
    if open_each or extract_table:
        logger.info("Таймаут первой сессии (список): %s мин.", fetch_timeout // 60_000)
        if extract_table:
            logger.info("Затем откроется второй браузер (Playwright) и по очереди загрузятся карточки объявлений.")

    use_real_chrome = prefer_system_chrome and _env_prefer_system_browser()
    if open_each or extract_table:
        logger.info(
            "Первый запуск открывает отдельное окно автоматизации (временный профиль), не ту же сессию, что ручной Chrome."
        )
        if use_real_chrome:
            logger.info("Используется системный Chrome/Edge — ближе к вашему обычному браузеру, чем встроенный Chromium.")
        else:
            logger.warning(
                "Включён встроенный Chromium (или не найден системный браузер). Сайт может вести себя иначе, чем в вашем Chrome — "
                "см. FEDRESURS_USE_BUNDLED_CHROMIUM и установку Chrome для Playwright."
            )
    page = fetch_page(
        MESSAGES_URL,
        page_action=page_action,
        headless=not visible_browser,
        timeout_ms=fetch_timeout,
        real_chrome=use_real_chrome,
        google_search=_env_messages_google_referer(),
    )

    if open_each and collected_data and not extract_table:
        out_file = __file__.replace(".py", "_announcements_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(collected_data, f, ensure_ascii=False, indent=2)
        logger.info("Сохранено объявлений в файл: %s", out_file)

    if extract_table:
        db_name = __file__.replace(".py", "_table")
        if date_from and date_to:
            db_name += f"_{date_from.replace('.', '-')}_{date_to.replace('.', '-')}"
        db_name += ".db"
        db_abs = str(Path(db_name).resolve())
        wide_table = bool(getattr(args, "table_wide", False))
        if wide_table:
            logger.info("Файл БД: %s — заполняется после обхода всех карточек (широкая схема).", db_abs)
        else:
            logger.info("Файл БД: %s — после каждой карточки выполняется INSERT и COMMIT.", db_abs)
        rows_in_db = 0
        try:
            if collected_links:
                rows_in_db = _visit_cards_playwright(
                    collected_links,
                    collected_data,
                    db_name,
                    prefer_system_chrome=use_real_chrome,
                    list_response=page,
                    wide_table=wide_table,
                )
            else:
                logger.warning(
                    "Режим --table: список ссылок пуст (возможна ошибка в page_action — см. лог scrapling). "
                    "Создаём пустую таблицу announcements."
                )
                _write_table_to_db([], list(SLIM_DB_COLUMNS), db_name)
        except KeyboardInterrupt:
            logger.warning(
                "Прервано (Ctrl+C): данные уже записанных карточек в БД; последняя могла не успеть."
            )
            try:
                conn = sqlite3.connect(db_abs)
                rows_in_db = conn.execute("SELECT COUNT(*) FROM announcements").fetchone()[0]
                conn.close()
            except Exception:
                rows_in_db = 0
        logger.info(
            "Итог БД: %s | карточек в памяти=%s | строк в таблице (по лотам / записям)=%s",
            db_abs,
            len(collected_data),
            rows_in_db,
        )
        if not collected_data and collected_links:
            logger.warning(
                "collected_data пуст при непустом списке ссылок — проверьте обход Playwright."
            )
        logger.info("Собрано сообщений (список): %s", stats["messages"])
        return

    logger.info("Собрано сообщений: %s | Страниц пагинации: %s", stats["messages"], stats["pages"])

    # Уникальность по ID сообщения (один документ — один ID; URL может отличаться порядком параметров и т.п.)
    seen_ids: set[str] = set()
    links_to_process: list[tuple[str, str]] = []
    for text, url in collected_links:
        msg_id = _message_id_from_url(url)
        if msg_id is None:
            msg_id = url
        if msg_id not in seen_ids:
            seen_ids.add(msg_id)
            links_to_process.append((text, url))

    logger.info("Уникальных объявлений о проведении торгов: %s", len(links_to_process))

    if skip_links_prompt:
        # Для тестовых прогонов пишем результат в файл (удобно при автоматическом запуске)
        _result_file = __file__.replace(".py", "_last_result.txt")
        with open(_result_file, "w", encoding="utf-8") as f:
            d_from = date_from or ""
            d_to = date_to or ""
            f.write(f"date_from={d_from}\ndate_to={d_to}\nmessages={stats['messages']}\npages={stats['pages']}\nunique={len(links_to_process)}\n")
        return
    if not print_links:
        answer = input("Вывести ссылки на страницы (Да/Нет)? ").strip().lower()
        if answer not in ("да", "yes", "д", "y"):
            return

    for link_text, full_url in links_to_process:
        logger.info("%s", full_url)
    if links_file:
        with open(links_file, "w", encoding="utf-8") as f:
            for _text, full_url in links_to_process:
                f.write(full_url + "\n")
        logger.info("Ссылки сохранены в файл: %s", links_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Сбор объявлений о проведении торгов с Fedresurs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Уже запущенный Chrome (CDP): процесс должен быть стартован с отладкой, например:\n"
            '  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" '
            "--remote-debugging-port=9222 --user-data-dir=%TEMP%\\fedresurs-cdp\n"
            "Затем в окружении: FEDRESURS_CDP_PORT=9222 или полный FEDRESURS_CDP_URL (ws://... из /json/version).\n"
            "Playwright подключается к этому процессу и открывает новый контекст (обычно отдельное окно), "
            "а не «подцепляется» к случайной уже открытой вкладке без CDP.\n\n"
            "Список сообщений: при 401 после StealthyFetcher автоматически делается второй проход голым Playwright; "
            "отключить: FEDRESURS_NO_LIST_PLAYWRIGHT_FALLBACK=1. Сразу без scrapling: FEDRESURS_LIST_USE_PLAYWRIGHT_ONLY=1.\n\n"
            "Карточки: по умолчанию скролл вниз и пауза ~5 с между карточками (FEDRESURS_CARD_GAP_MS). "
            "Быстрый режим без этого: FEDRESURS_CARD_FAST=1.\n\n"
            "Карточка по умолчанию: https://fedresurs.ru/bankruptmessages/{GUID} (JSON /backend/… и DOM в браузере). "
            "Старый MessageWindow: FEDRESURS_CARD_OLD_PORTAL=1. Явно отключить публичный URL без старого портала: "
            "FEDRESURS_CARD_PUBLIC=0."
        ),
    )
    parser.add_argument("--from", dest="date_from", metavar="DD.MM.YYYY", help="Дата с")
    parser.add_argument("--to", dest="date_to", metavar="DD.MM.YYYY", help="Дата по")
    parser.add_argument("--test", action="store_true", help="Тестовый прогон: не спрашивать вывод ссылок")
    parser.add_argument("--visible", action="store_true", help="Видимый браузер")
    parser.add_argument("--manual-type", action="store_true", help="15 с на ручной выбор типа в браузере — даёт 95/133/168")
    parser.add_argument("--open-each", action="store_true", help="После сбора по очереди открывать каждое объявление (Enter — следующее, q — выход)")
    parser.add_argument(
        "--table",
        action="store_true",
        help="Обход карточек → SQLite: url, должник, вид торгов, ИНН, начальная цена, адрес, Описание (строка на каждый лот)",
    )
    parser.add_argument(
        "--table-wide",
        dest="table_wide",
        action="store_true",
        help="Обход карточек → SQLite (широкая схема): каждый найденный ключ становится отдельной колонкой; строка на каждый лот",
    )
    parser.add_argument("--print-links", action="store_true", help="Сразу вывести ссылки (без запроса Да/Нет)")
    parser.add_argument("--links-file", metavar="FILE", help="Сохранить ссылки в файл (по одной на строку)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Подробный лог (уровень DEBUG)")
    parser.add_argument("--log-file", metavar="PATH", help="Дополнительно писать лог в файл (UTF-8)")
    parser.add_argument(
        "--bundled-chromium",
        action="store_true",
        help="Только встроенный Chromium (Playwright/scrapling). По умолчанию берётся системный Chrome или Edge, если сайт в Chromium не открывается.",
    )
    args = parser.parse_args()

    _configure_logging(
        (args.log_file or "").strip() or None,
        bool(args.verbose),
    )

    if args.date_from or args.date_to:
        date_from = (args.date_from or "").strip() or None
        date_to = (args.date_to or "").strip() or None
        if date_from and not date_to:
            date_to = date_from
        elif date_to and not date_from:
            date_from = date_to
    else:
        logger.info("Фильтр по датам (формат DD.MM.YYYY). Enter — без фильтра.")
        date_from = input("Дата с: ").strip()
        date_to = input("Дата по: ").strip() if date_from else ""
        if date_from and not date_to:
            logger.info("Укажите обе даты. Запуск без фильтра.")
            date_from = date_to = None
        elif date_to and not date_from:
            date_from = date_to = None
        date_from = date_from or None
        date_to = date_to or None

    visible = getattr(args, "visible", False)
    manual = getattr(args, "manual_type", False)
    open_each = getattr(args, "open_each", False)
    extract_table = bool(getattr(args, "table", False) or getattr(args, "table_wide", False))
    if manual:
        visible = True
    main(
        date_from=date_from,
        date_to=date_to,
        skip_links_prompt=args.test,
        print_links=getattr(args, "print_links", False),
        links_file=(args.links_file or "").strip() or None,
        visible_browser=visible,
        manual_type=manual,
        open_each=open_each,
        extract_table=extract_table,
        prefer_system_chrome=not bool(getattr(args, "bundled_chromium", False)),
    )
