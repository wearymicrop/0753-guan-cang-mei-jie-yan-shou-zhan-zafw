from app.modules.m1_batches.service import resolve


def test_current_catalog_version(clean_result):
    assert clean_result['batches']['selected'] == '馆规-02'
    assert clean_result['batches']['as_of'] == '2026-11-20T08:30:00Z'


def test_half_open_boundary_selects_new_release(clean):  # TRAP-23
    clean['at'] = '2026-10-31T16:00:00Z'
    assert resolve(clean,{})['selected'] == '馆规-02'


def test_catalog_overlap_has_no_winner(clean):  # TRAP-25
    clean['catalogs'][1]['end'] = '2026-11-30T00:00:00+08:00'
    result = resolve(clean,{})
    assert result['selected'] is None and result['reasons'] == {'CATALOG_OVERLAP': 2}


def test_duplicate_release_is_not_overlap(dirty_result):
    assert dirty_result['batches']['reasons'] == {'CATALOG_DUPLICATE':1}
    assert dirty_result['batches']['selected'] == '馆规-02'


def test_missing_catalog_gives_explicit_state(clean):  # TRAP-18
    clean['catalogs'] = []
    assert resolve(clean,{})['reasons'] == {'CATALOG_MISSING':1}


def test_catalog_requires_both_replica_tiers(clean):
    clean['catalogs'][0]['tiers'].pop()
    assert resolve(clean,{})['reasons'] == {'CATALOG_MISSING':1,'CATALOG_SCHEMA':1}
