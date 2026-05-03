#!/usr/bin/env python3
"""
Добавляет BPMNEdge (стрелки/связи) в BPMN-файлы.
Рекомендуется запускать после создания/изменения процесса.
Использование: python add_bpmn_edges.py [файл.bpmn ...]
"""

import xml.etree.ElementTree as ET
import sys
import os

NS = {
    'bpmn': 'http://www.omg.org/spec/BPMN/20100524/MODEL',
    'bpmndi': 'http://www.omg.org/spec/BPMN/20100524/DI',
    'dc': 'http://www.omg.org/spec/DD/20100524/DC',
    'di': 'http://www.omg.org/spec/DD/20100524/DI',
}

# Регистрация namespace для корректного вывода
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


def get_bounds(plane):
    """Собирает bpmnElement -> (x, y, width, height), центр (cx, cy)."""
    bounds = {}
    for shape in plane.findall('bpmndi:BPMNShape', NS):
        ref = shape.get('bpmnElement')
        b = shape.find('dc:Bounds', NS)
        if ref and b is not None:
            x = float(b.get('x', 0))
            y = float(b.get('y', 0))
            w = float(b.get('width', 100))
            h = float(b.get('height', 80))
            bounds[ref] = (x, y, w, h)
    return bounds


def get_flow_center(bounds_dict, element_id):
    """Центр фигуры для waypoint."""
    if element_id not in bounds_dict:
        return None
    x, y, w, h = bounds_dict[element_id]
    return (x + w / 2, y + h / 2)


def get_flow_exit_entry(bounds_dict, source_id, target_id):
    """
    Точки выхода от source и входа в target.
    Используем сторону, обращённую к другой фигуре (правый/левый центр или верх/низ).
    """
    if source_id not in bounds_dict or target_id not in bounds_dict:
        return None, None
    sx, sy, sw, sh = bounds_dict[source_id]
    tx, ty, tw, th = bounds_dict[target_id]
    scx, scy = sx + sw / 2, sy + sh / 2
    tcx, tcy = tx + tw / 2, ty + th / 2
    # Выход: та грань source, которая ближе к target
    dx = tcx - scx
    dy = tcy - scy
    if abs(dx) >= abs(dy):
        if dx >= 0:
            exit_pt = (sx + sw, scy)
            entry_pt = (tx, tcy)
        else:
            exit_pt = (sx, scy)
            entry_pt = (tx + tw, tcy)
    else:
        if dy >= 0:
            exit_pt = (scx, sy + sh)
            entry_pt = (tcx, ty)
        else:
            exit_pt = (scx, sy)
            entry_pt = (tcx, ty + th)
    return exit_pt, entry_pt


def add_edges_to_bpmn(path):
    tree = ET.parse(path)
    root = tree.getroot()
    plane = root.find('.//bpmndi:BPMNPlane', NS)
    process = root.find('.//bpmn:process', NS)
    if plane is None or process is None:
        print(f'Пропуск {path}: нет BPMNPlane или process')
        return

    bounds = get_bounds(plane)
    flows = []
    for flow in process.findall('bpmn:sequenceFlow', NS):
        fid = flow.get('id')
        src = flow.get('sourceRef')
        tgt = flow.get('targetRef')
        if fid and src and tgt and src in bounds and tgt in bounds:
            flows.append((fid, src, tgt))

    if not flows:
        print(f'Нет связей для отрисовки в {path}')
        return

    # Проверяем, есть ли уже BPMNEdge
    existing = plane.findall('bpmndi:BPMNEdge', NS)
    if existing:
        print(f'В {path} уже есть {len(existing)} BPMNEdge, пропуск')
        return

    # Создаём BPMNEdge для каждого sequenceFlow
    # Нам нужно вставить XML после последнего BPMNShape. Работаем с файлом как с текстом,
    # т.к. ET не сохраняет порядок и namespace префиксы как в оригинале.
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    edge_lines = []
    for fid, src, tgt in flows:
        exit_pt, entry_pt = get_flow_exit_entry(bounds, src, tgt)
        if exit_pt is None:
            continue
        x1, y1 = exit_pt
        x2, y2 = entry_pt
        # Иногда нужна промежуточная точка для обхода (ортогональный вид)
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        edge_lines.append(
            f'      <bpmndi:BPMNEdge bpmnElement="{fid}">\n'
            f'        <di:waypoint x="{x1:.0f}" y="{y1:.0f}" />\n'
            f'        <di:waypoint x="{mid_x:.0f}" y="{mid_y:.0f}" />\n'
            f'        <di:waypoint x="{x2:.0f}" y="{y2:.0f}" />\n'
            f'      </bpmndi:BPMNEdge>'
        )

    insert_block = '\n'.join(edge_lines)
    # Вставляем перед закрывающим тегом </bpmndi:BPMNPlane>
    marker = '</bpmndi:BPMNPlane>'
    if marker not in content:
        print(f'Не найден </bpmndi:BPMNPlane> в {path}')
        return
    new_content = content.replace(
        marker,
        '\n' + insert_block + '\n    ' + marker
    )
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f'Добавлено {len(edge_lines)} связей (BPMNEdge) в {path}')


def main():
    if len(sys.argv) > 1:
        for path in sys.argv[1:]:
            if path.endswith('.bpmn') and os.path.isfile(path):
                add_edges_to_bpmn(path)
    else:
        folder = os.path.dirname(os.path.abspath(__file__))
        for name in ('case1-telegram-bot-studio.bpmn', 'case2-it-recruiting.bpmn'):
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                add_edges_to_bpmn(path)


if __name__ == '__main__':
    main()
