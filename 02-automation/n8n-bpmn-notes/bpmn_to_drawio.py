#!/usr/bin/env python3
"""
Конвертер BPMN 2.0 XML в формат draw.io (.drawio).
Использует координаты из BPMNDiagram и создаёт mxGraphModel.
Запуск: python bpmn_to_drawio.py [файл.bpmn]
По умолчанию конвертирует оба кейса в папке.
"""

import xml.etree.ElementTree as ET
import sys
import os
import re

# BPMN namespaces
NS = {
    'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
    'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
    'dc': 'http://www.omg.org/spec/DD/20100524/DC',
}


def get_text(el, default=''):
    return (el.text or '').strip() or default


def escape_xml(s):
    if not s:
        return ''
    return (s
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))


def parse_bpmn(path):
    tree = ET.parse(path)
    root = tree.getroot()
    process = root.find('.//bpmn:process', NS)
    if process is None:
        raise SystemExit(f'В файле {path} не найден bpmn:process')
    plane = root.find('.//bpmndi:BPMNPlane', NS)
    if plane is None:
        raise SystemExit(f'В файле {path} не найден bpmndi:BPMNPlane')

    # id -> (name, tag)
    names = {}
    for el in process:
        tag = el.tag
        if '}' in tag:
            tag = tag.split('}', 1)[1]
        bid = el.get('id')
        name = el.get('name') or ''
        if bid:
            names[bid] = (name, tag)

    # bpmnElement -> bounds (x, y, w, h)
    bounds = {}
    for shape in plane.findall('bpmndi:BPMNShape', NS):
        ref = shape.get('bpmnElement')
        bounds_el = shape.find('dc:Bounds', NS)
        if ref and bounds_el is not None:
            x = float(bounds_el.get('x', 0))
            y = float(bounds_el.get('y', 0))
            w = float(bounds_el.get('width', 100))
            h = float(bounds_el.get('height', 80))
            bounds[ref] = (x, y, w, h)

    # sequenceFlow
    flows = []
    for flow in process.findall('bpmn:sequenceFlow', NS):
        src = flow.get('sourceRef')
        tgt = flow.get('targetRef')
        if src and tgt:
            flows.append((src, tgt))

    return names, bounds, flows


def drawio_style(tag, name):
    """Стиль draw.io по типу BPMN-элемента."""
    if tag == 'startEvent' or tag == 'endEvent':
        return 'ellipse;whiteSpace=wrap;html=1;aspect=fixed;'
    if tag == 'exclusiveGateway':
        return 'rhombus;whiteSpace=wrap;html=1;'
    # task, serviceTask, userTask, receiveTask
    return 'rounded=1;whiteSpace=wrap;html=1;'


def bpmn_to_drawio(path, out_path=None):
    names, bounds, flows = parse_bpmn(path)
    if out_path is None:
        out_path = path.replace('.bpmn', '.drawio')

    # Маппинг bpmn id -> draw.io id (только элементы с координатами)
    shape_ids = sorted(bounds.keys())
    id_map = {bid: str(i + 2) for i, bid in enumerate(shape_ids)}  # 0 и 1 зарезервированы
    edge_ids = {}
    for i, (src, tgt) in enumerate(flows):
        edge_ids[(src, tgt)] = str(1000 + i)

    cells = []
    # Родительский слой
    cells.append('<mxCell id="1" parent="0" />')
    # Фигуры (только элементы с координатами)
    for bpmn_id in shape_ids:
        name, tag = names.get(bpmn_id, ('', 'task'))
        cid = id_map[bpmn_id]
        x, y, w, h = bounds[bpmn_id]
        style = drawio_style(tag, name)
        label = escape_xml(name)
        cells.append(
            f'<mxCell id="{cid}" value="{label}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />'
            f'</mxCell>'
        )
    # Рёбра
    for (src, tgt), eid in edge_ids.items():
        if src not in id_map or tgt not in id_map:
            continue
        cells.append(
            f'<mxCell id="{eid}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" '
            f'edge="1" parent="1" source="{id_map[src]}" target="{id_map[tgt]}">'
            f'<mxGeometry relative="1" as="geometry" />'
            f'</mxCell>'
        )

    title = os.path.splitext(os.path.basename(path))[0]
    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="1" agent="bpmn_to_drawio" version="22.0.0" etag="" type="device">
  <diagram id="{title}" name="{title}">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="3000" pageHeight="2400" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        {chr(10).join('        ' + c for c in cells)}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(xml)
    print(f'Записано: {out_path}')
    return out_path


def main():
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            if path.endswith('.bpmn') and os.path.isfile(path):
                bpmn_to_drawio(path)
            else:
                print(f'Пропуск (не .bpmn или не файл): {path}')
    else:
        folder = os.path.dirname(os.path.abspath(__file__))
        for name in ('case1-telegram-bot-studio.bpmn', 'case2-it-recruiting.bpmn'):
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                bpmn_to_drawio(path)


if __name__ == '__main__':
    main()
