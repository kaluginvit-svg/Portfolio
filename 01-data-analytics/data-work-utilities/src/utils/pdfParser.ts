import * as pdfjsLib from 'pdfjs-dist';
import { Row } from '../types';

// Настройка worker для pdf.js
if (typeof window !== 'undefined') {
  pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.js`;
}

interface TableCell {
  text: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface TableRow {
  cells: TableCell[];
}

/**
 * Извлекает первую таблицу из первой страницы PDF
 */
export function parsePDFFile(file: File): Promise<{ headers: string[]; rows: Row[]; sheetName: string }> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = async (e) => {
      try {
        const arrayBuffer = e.target?.result as ArrayBuffer;
        
        if (!arrayBuffer) {
          reject(new Error('Не удалось прочитать файл'));
          return;
        }

        // Загружаем PDF документ
        const loadingTask = pdfjsLib.getDocument({ data: arrayBuffer });
        const pdf = await loadingTask.promise;

        if (pdf.numPages === 0) {
          reject(new Error('PDF файл не содержит страниц'));
          return;
        }

        // Получаем первую страницу
        const page = await pdf.getPage(1);

        // Получаем текстовое содержимое страницы
        const textContent = await page.getTextContent();
        
        // Пытаемся извлечь таблицу из текста
        const table = extractTableFromTextContent(textContent, page.view);

        if (!table || table.length === 0) {
          reject(new Error('На первой странице PDF не найдено таблиц. Попробуйте другой файл или убедитесь, что таблица присутствует на первой странице.'));
          return;
        }

        // Преобразуем таблицу в нужный формат
        const headers = table[0].map(cell => cell.trim() || `Column ${table[0].indexOf(cell) + 1}`);
        const rows: Row[] = table.slice(1).map((row) => {
          const obj: Row = {};
          headers.forEach((header, index) => {
            const value = row[index]?.trim() || '';
            // Пытаемся преобразовать в число
            const numValue = parseFloat(value);
            obj[header] = value === '' ? null : (!isNaN(numValue) && isFinite(numValue) ? numValue : value);
          });
          return obj;
        });

        if (headers.length === 0 || rows.length === 0) {
          reject(new Error('Не удалось извлечь данные из таблицы. Таблица может быть пустой или иметь нестандартный формат.'));
          return;
        }

        resolve({ headers, rows, sheetName: 'PDF Page 1' });
      } catch (error) {
        console.error('Ошибка при парсинге PDF:', error);
        if (error instanceof Error) {
          reject(new Error(`Ошибка при чтении PDF файла: ${error.message}`));
        } else {
          reject(new Error('Неизвестная ошибка при чтении PDF файла'));
        }
      }
    };

    reader.onerror = () => reject(new Error('Ошибка чтения файла'));
    reader.readAsArrayBuffer(file);
  });
}

/**
 * Извлекает таблицу из текстового содержимого страницы PDF
 * Использует эвристику для определения структуры таблицы
 */
function extractTableFromTextContent(textContent: any, view: number[]): string[][] | null {
  if (!textContent || !textContent.items || textContent.items.length === 0) {
    return null;
  }

  // В pdf.js textContent.items имеет структуру: { str: string, transform: number[] }
  // transform - это матрица преобразования [a, b, c, d, e, f], где:
  // - transform[4] (e) - X координата
  // - transform[5] (f) - Y координата
  const items = textContent.items as Array<{
    str: string;
    transform: number[];
    width?: number;
    height?: number;
  }>;

  if (items.length === 0) {
    return null;
  }

  // Фильтруем пустые элементы и вычисляем координаты
  const itemsWithCoords = items
    .filter(item => item.str && item.str.trim() !== '')
    .map(item => ({
      str: item.str,
      transform: item.transform,
      x: item.transform[4],
      y: item.transform[5],
      width: item.width || 0,
    }));

  if (itemsWithCoords.length === 0) {
    return null;
  }

  // Сортируем элементы по Y координате (сверху вниз), затем по X (слева направо)
  // В PDF координатах Y увеличивается снизу вверх, поэтому используем обратный порядок
  itemsWithCoords.sort((a, b) => {
    const yDiff = Math.abs(b.y - a.y);
    if (yDiff > 5) {
      return b.y - a.y; // Больше Y = выше на странице
    }
    return a.x - b.x; // Меньше X = левее
  });

  // Группируем элементы в строки по Y координате
  const rowGroups: { y: number; items: typeof itemsWithCoords }[] = [];
  const rowTolerance = 8; // Допуск для определения строки

  for (const item of itemsWithCoords) {
    const existingGroup = rowGroups.find(g => Math.abs(g.y - item.y) <= rowTolerance);
    
    if (existingGroup) {
      existingGroup.items.push(item);
    } else {
      rowGroups.push({ y: item.y, items: [item] });
    }
  }

  // Сортируем группы по Y (сверху вниз)
  rowGroups.sort((a, b) => b.y - a.y);

  // Для каждой группы сортируем элементы по X (слева направо) и группируем в ячейки
  const rows: string[][] = [];

  for (const group of rowGroups) {
    // Сортируем элементы группы по X
    group.items.sort((a, b) => a.x - b.x);
    
    // Группируем элементы в ячейки (если они близко по X, считаем одной ячейкой)
    const cells: string[] = [];
    let currentCell = '';
    let lastX = -Infinity;
    const cellTolerance = 30; // Допуск для определения ячейки

    for (const item of group.items) {
      const itemText = item.str.trim();

      if (item.x - lastX > cellTolerance && currentCell !== '') {
        // Новая ячейка
        cells.push(currentCell.trim());
        currentCell = itemText;
      } else {
        // Продолжение текущей ячейки
        currentCell = currentCell ? currentCell + ' ' + itemText : itemText;
      }
      lastX = item.x + item.width;
    }

    if (currentCell) {
      cells.push(currentCell.trim());
    }

    if (cells.length > 0) {
      rows.push(cells);
    }
  }

  if (rows.length === 0) {
    return null;
  }

  // Определяем максимальное количество столбцов
  const maxCols = Math.max(...rows.map(row => row.length));

  // Нормализуем строки - добавляем пустые ячейки, если нужно
  const normalizedRows = rows.map(row => {
    const normalized = [...row];
    while (normalized.length < maxCols) {
      normalized.push('');
    }
    return normalized.slice(0, maxCols);
  });

  // Если все строки имеют одинаковое количество столбцов и их больше 1, считаем это таблицей
  if (normalizedRows.length >= 1 && maxCols >= 2) {
    return normalizedRows;
  }

  return null;
}
