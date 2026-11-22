from app.modules.m3_mapping.rules import pick
from app.pipeline import evaluate


def test_longest_annex_determines_target(clean_result):  # TRAP-19
    first = clean_result['mapping']['rows'][0]
    assert first['path']=='阅览池/冬港底片/Café-底片.tif' and first['route_lines']==[3]


def test_longest_is_segment_aware():
    rule = {'prefix':'照片/冬港','depth':2,'target':'阅览','line':24}
    assert pick('照片/冬港支线/001.tif',[rule]) == (None,[],'ROUTE_MISSING')


def test_inactive_version_not_selected(clean_result):
    active = [row['line'] for row in clean_result['mapping']['rules'] if row['active']]
    assert active == [1,2,3]


def test_ambiguous_routes_preserve_candidates(dirty_result):
    row = next(row for row in dirty_result['mapping']['issues'] if row['code']=='ROUTE_OVERLAP')
    assert row['object_id']=='0011' and row['route_lines']==[7,8]


def test_target_collision_is_tier_specific(dirty_result):
    rows = [row for row in dirty_result['mapping']['rows'] if row['code']=='TARGET_COLLISION']
    assert [(row['object_id'],row['tier']) for row in rows] == [('0023','online'),('0024','online')]
    assert len({row['path'] for row in rows})==1


def test_missing_routing_enters_conflict(clean):
    clean['routes']=[row for row in clean['routes'] if row['tier']=='online']
    result=evaluate(clean)
    assert result['mapping']['reasons']=={'ROUTE_MISSING':24}
    assert result['reconcile']['totals']['conflict']==24
