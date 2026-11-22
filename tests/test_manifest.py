import pytest

from app.modules.m2_manifest.paths import normalize
from app.modules.m2_manifest.service import ingest


def test_unicode_alias_collision_keeps_both_objects(dirty_result):  # TRAP-22
    result = dirty_result['manifest']
    rows = [row for row in result['issues'] if row['code']=='CANONICAL_COLLISION']
    assert [row['object_id'] for row in rows] == ['0001','0025']
    assert {row['path'] for row in rows} == {'照片/冬港/Café-底片.tif'}


def test_duplicate_manifest_retains_all_source_rows(dirty_result):
    assert dirty_result['manifest']['rows'][0]['source_lines'] == [1,25]
    assert dirty_result['manifest']['reasons']['MANIFEST_DUPLICATE'] == 1


def test_source_identifier_keeps_leading_zeros(clean_result):  # TRAP-08
    assert clean_result['manifest']['rows'][0]['object_id'] == '0001'


def test_conflicting_fact_is_not_last_wins(dirty_result):  # TRAP-14
    relevant = [row for row in dirty_result['manifest']['issues'] if row['code']=='OBJECT_CONFLICT']
    assert [row['line'] for row in relevant] == [5,27]
    assert len({row['sha256'] for row in relevant}) == 2


def test_relative_path_contract():
    assert normalize('照片\\冬港//./Cafe\u0301.tif') == '照片/冬港/Café.tif'
    with pytest.raises(ValueError):
        normalize('照片/../封存.tif')


def test_large_exact_bytes_are_strings(clean):  # TRAP-09
    clean['objects'][0]['bytes'] = 9_007_199_254_740_993
    assert ingest(clean,{})['rows'][0]['bytes'] == '9007199254740993'
