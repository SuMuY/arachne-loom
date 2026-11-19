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


def test_parse_nested_list_levels(tmp_path):
    source = tmp_path / 'nested.md'
    source.write_text('1. Parent\n  1. Child one\n  2. Child two\n2. Next parent\n', encoding='utf-8')
    block = parse_markdown(source)['blocks'][0]
    assert [(item['level'], item['start'], item['kind']) for item in block['items']] == [
        (0, 1, 'ordered'), (1, 1, 'ordered'), (1, 1, 'ordered'), (0, 1, 'ordered')]


def test_parse_rejects_mixed_list_kinds_at_same_level(tmp_path):
    from arachne_loom.parser import ParseError
    source = tmp_path / 'mixed-siblings.md'
    source.write_text('- Bullet\n1. Number\n', encoding='utf-8')
    with pytest.raises(ParseError, match='list kind cannot change'):
        parse_markdown(source)


def test_nested_numbering_uses_native_levels_and_restarts_children(tmp_path):
    model, profile, task = fixture()
    model['blocks'] = [{'type': 'list', 'kind': 'ordered', 'start': 1, 'items': [
        {'level': 0, 'start': 1, 'kind': 'ordered', 'inlines': [{'type': 'text', 'text': 'Parent one'}]},
        {'level': 1, 'start': 1, 'kind': 'ordered', 'inlines': [{'type': 'text', 'text': 'Child one'}]},
        {'level': 1, 'start': 2, 'kind': 'ordered', 'inlines': [{'type': 'text', 'text': 'Child two'}]},
        {'level': 0, 'start': 2, 'kind': 'ordered', 'inlines': [{'type': 'text', 'text': 'Parent two'}]},
        {'level': 1, 'start': 1, 'kind': 'ordered', 'inlines': [{'type': 'text', 'text': 'Child restarted'}]},
    ]}]
    profile['listStyle'] = {'ordered': {'markerPt': 18, 'textPt': 42},
                            'unordered': {'markerPt': 18, 'textPt': 42}}
    output = compile_document(model, profile, task, tmp_path / 'nested-build')
    doc = Document(output / 'document.docx')
    assert [p.text for p in doc.paragraphs] == ['Parent one', 'Child one', 'Child two', 'Parent two', 'Child restarted']
    levels = [int(p._p.xpath('./w:pPr/w:numPr/w:ilvl')[0].get(qn('w:val'))) for p in doc.paragraphs]
    assert levels == [0, 1, 1, 0, 1]
    num_ids = [p._p.xpath('./w:pPr/w:numPr/w:numId')[0].get(qn('w:val')) for p in doc.paragraphs]
    assert len(set(num_ids)) == 1
    numbering = doc.part.numbering_part.element
    abstract_id = numbering.xpath(f'./w:num[@w:numId="{num_ids[0]}"]/w:abstractNumId')[0].get(qn('w:val'))
    abstract = numbering.xpath(f'./w:abstractNum[@w:abstractNumId="{abstract_id}"]')[0]
    assert abstract.find(qn('w:multiLevelType')).get(qn('w:val')) == 'multilevel'
    assert [lvl.find(qn('w:numFmt')).get(qn('w:val')) for lvl in abstract.findall(qn('w:lvl'))] == ['decimal', 'decimal']
    assert [lvl.find(qn('w:lvlText')).get(qn('w:val')) for lvl in abstract.findall(qn('w:lvl'))] == ['%1.', '%1.%2.']


def test_nested_levels_can_mix_ordered_and_unordered(tmp_path):
    model, profile, task = fixture()
    model['blocks'] = [{'type': 'list', 'kind': 'ordered', 'items': [
        {'level': 0, 'kind': 'ordered', 'inlines': [{'type': 'text', 'text': 'Parent'}]},
        {'level': 1, 'kind': 'unordered', 'inlines': [{'type': 'text', 'text': 'Child'}]},
    ]}]
    output = compile_document(model, profile, task, tmp_path / 'mixed-build')
    doc = Document(output / 'document.docx')
    num_id = doc.paragraphs[0]._p.xpath('./w:pPr/w:numPr/w:numId')[0].get(qn('w:val'))
    abstract_id = doc.part.numbering_part.element.xpath(f'./w:num[@w:numId="{num_id}"]/w:abstractNumId')[0].get(qn('w:val'))
    levels = doc.part.numbering_part.element.xpath(f'./w:abstractNum[@w:abstractNumId="{abstract_id}"]/w:lvl')
    assert [lvl.find(qn('w:numFmt')).get(qn('w:val')) for lvl in levels] == ['decimal', 'bullet']


@pytest.mark.parametrize('items', [
    [{'level': 0, 'inlines': [{'type': 'text', 'text': 'Parent'}]},
     {'level': 2, 'inlines': [{'type': 'text', 'text': 'Skipped level'}]}],
    [{'level': 9, 'inlines': [{'type': 'text', 'text': 'Too deep'}]}],
    [{'level': 1, 'inlines': [{'type': 'text', 'text': 'Missing parent'}]}],
    [{'level': 0, 'kind': 'ordered', 'inlines': [{'type': 'text', 'text': 'Parent'}]},
     {'level': 0, 'kind': 'unordered', 'inlines': [{'type': 'text', 'text': 'Different kind'}]}],
])
def test_invalid_nested_list_levels_rejected(items):
    model, profile, task = fixture()
    model['blocks'] = [{'type': 'list', 'kind': 'ordered', 'items': items}]
    assert any('list level' in error or 'list kind' in error for error in validate(model, profile, task))


def test_numbering_definitions_precede_instances(tmp_path):
    model, profile, task = fixture()
    profile['headingStyle']['indentation'] = {'basePt': 0, 'incrementPt': 18, 'hangingPt': 72}
    model['blocks'].insert(0, {'type': 'heading', 'id': 'h', 'level': 1, 'content': 'Heading', 'numberPath': ['1']})
    output = compile_document(model, profile, task, tmp_path / 'build')
    numbering = Document(output / 'document.docx').part.numbering_part.element
    seen_instance = False
    for child in numbering:
        if child.tag == qn('w:num'):
            seen_instance = True
        if child.tag == qn('w:abstractNum'):
            assert not seen_instance, 'abstractNum after num violates CT_Numbering order'


def test_list_jump_after_return_to_parent_is_rejected(tmp_path):
    from arachne_loom.parser import ParseError

    source = tmp_path / 'jump.md'
    source.write_text('1. Parent\n  1. Child\n    1. Grandchild\n2. Parent\n    1. Missing child\n')
    with pytest.raises(ParseError, match='list level jumps'):
        parse_markdown(source)


def test_model_list_jump_after_return_to_parent_is_rejected():
    model, profile, task = fixture()
    model['blocks'] = [{'type': 'list', 'kind': 'ordered', 'items': [
        {'level': level, 'inlines': [{'type': 'text', 'text': 'Item'}]}
        for level in [0, 1, 2, 0, 2]
    ]}]
    assert any('list level jumps' in error for error in validate(model, profile, task))
