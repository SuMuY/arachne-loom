import json
from pathlib import Path

import pytest
from docx import Document
from docx.oxml.ns import qn

from arachne_loom.parser import parse_markdown
from arachne_loom.generator import compile_document
from arachne_loom.validator import validate

ROOT = Path(__file__).resolve().parents[2]


def test_parse_native_lists_and_start(tmp_path):
    source = tmp_path / 'lists.md'
    source.write_text('# 1 Heading\n\n- First\n- Second\n\nText\n\n9. Nine\n10. Ten\n', encoding='utf-8')
    blocks = parse_markdown(source)['blocks']
    assert [b['type'] for b in blocks] == ['heading', 'list', 'paragraph', 'list']
    assert blocks[1]['kind'] == 'unordered'
    assert blocks[3]['kind'] == 'ordered'
    assert blocks[3]['start'] == 9
    assert len(blocks[1]['items']) == 2


def fixture():
    profile = json.loads((ROOT / 'profiles/ctd/zh-CN/config.json').read_text())
    model = {'schemaVersion': '0.0.1-provisional', 'language': 'zh-CN', 'metadata': {},
             'resourceRoot': str(ROOT), 'blocks': [
                 {'type': 'list', 'kind': kind, 'start': 9, 'items': [
                     {'inlines': [{'type': 'text', 'text': text}]} for text in ['First', 'Second']]}
                 for kind in ['unordered', 'ordered', 'ordered']]}
    task = {'taskId': 'lists', 'resourceRoot': str(ROOT),
            'baseTemplate': str(ROOT / 'compiler/templates/base.docx')}
    return model, profile, task


def test_list_numbering_geometry_and_independent_sequences(tmp_path):
    model, profile, task = fixture()
    profile['listStyle'] = {'unordered': {'markerPt': 12, 'textPt': 30},
                            'ordered': {'markerPt': 18, 'textPt': 54}}
    output = compile_document(model, profile, task, tmp_path / 'build')
    doc = Document(output / 'document.docx')
    assert [p.text for p in doc.paragraphs] == ['First', 'Second'] * 3
    ids = []
    for index, p in enumerate(doc.paragraphs):
        group = index // 2
        marker, text = (12, 30) if group == 0 else (18, 54)
        num_id = p._p.xpath('./w:pPr/w:numPr/w:numId')[0].get(qn('w:val'))
        ids.append(num_id)
        abstract_id = doc.part.numbering_part.element.xpath(f'./w:num[@w:numId="{num_id}"]/w:abstractNumId')[0].get(qn('w:val'))
        lvl = doc.part.numbering_part.element.xpath(f'./w:abstractNum[@w:abstractNumId="{abstract_id}"]/w:lvl')[0]
        assert lvl.find(qn('w:numFmt')).get(qn('w:val')) == ('bullet' if group == 0 else 'decimal')
        assert lvl.find(qn('w:suff')).get(qn('w:val')) == 'tab'
        assert lvl.find(qn('w:pPr')).find(qn('w:ind')).get(qn('w:left')) == str(text * 20)
        assert lvl.find(qn('w:pPr')).find(qn('w:ind')).get(qn('w:hanging')) == str((text-marker) * 20)
        assert p.paragraph_format.left_indent.pt == text
        assert p.paragraph_format.first_line_indent.pt == marker-text
        assert p.paragraph_format.tab_stops[0].position.pt == text
    assert ids[0] == ids[1]
    assert len(set(ids[::2])) == 3


@pytest.mark.parametrize('setting', [None, {'ordered': {'markerPt': 20, 'textPt': 10}},
    {'unordered': {'markerPt': True, 'textPt': 30}}, {'ordered': {'markerPt': 0}},
    {'unordered': {'markerPt': 0, 'textPt': float('inf')}}, {'typo': {}}])
def test_bad_list_style_rejected(setting):
    model, profile, task = fixture()
    profile['listStyle'] = setting
    assert any('listStyle' in e for e in validate(model, profile, task))


def test_list_reference_is_counted_and_validated(tmp_path):
    model, profile, task = fixture()
    model['blocks'].insert(0, {'type': 'heading', 'id': 'h3', 'level': 3, 'content': 'Chapter', 'numberPath': ['1', '1', '1']})
    model['blocks'].append({'type': 'table', 'id': 'tbl', 'title': 'Table', 'headerRows': 1, 'rows': [['Header'], ['Value']]})
    model['blocks'][1]['items'][0]['inlines'].append({'type': 'crossReference', 'targetId': 'tbl'})
    output = compile_document(model, profile, task, tmp_path / 'build')
    expected = json.loads((output / 'expected-manifest.json').read_text())
    assert expected['expectedFieldCount'] == 3
    assert expected['crossReferences'][0]['targetId'] == 'tbl'


@pytest.mark.parametrize('items', [None, [], [None], [{'inlines': None}]])
def test_invalid_list_items_rejected(items):
    model, profile, task = fixture()
    model['blocks'][0]['items'] = items
    assert any('list' in error for error in validate(model, profile, task))


def test_nested_list_is_rejected(tmp_path):
    from arachne_loom.parser import ParseError
    source = tmp_path / 'nested.md'
    source.write_text('- Parent\n  - Child\n', encoding='utf-8')
    with pytest.raises(ParseError, match='nested lists'):
        parse_markdown(source)
