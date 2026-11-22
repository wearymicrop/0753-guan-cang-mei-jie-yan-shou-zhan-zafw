from app.modules.m6_reconcile.totals import count
from app.pipeline import evaluate


def test_sample_conservation(dirty_result):
    result=dirty_result['reconcile']
    assert result['status']=='MATCHED'
    assert result['totals']=={'originals':26,'verified':10,'pending':2,'conflict':14,'difference':0,'expected_bytes':'3558','verified_copies':32}


def test_clean_dual_copies(clean_result):
    totals=clean_result['reconcile']['totals']
    assert totals['originals']==totals['verified']==24 and totals['verified_copies']==48


def test_matching_counts_do_not_hide_duplicate_id():
    source=[{'object_id':key,'bytes':'4','conflict':False} for key in ('0001','0002')]
    outcome=[{'object_id':'0001','state':'verified'}]*2
    totals, identity=count(source,outcome)
    assert totals['difference']==0 and not identity


def test_absent_manifest_requires_attention(clean):
    clean['objects']=[]
    result=evaluate(clean)['reconcile']
    assert result['status']=='CHECK_REQUIRED' and result['totals']['originals']==0


def test_id_stays_unique_after_conflicts(dirty_result):
    rows=dirty_result['reconcile']['rows']
    assert len({row['object_id'] for row in rows})==len(rows)==26


def test_unaddressable_manifest_row_counted_as_issue(dirty_result):
    assert dirty_result['manifest']['input_count']==29
    assert sum(row['code']=='OBJECT_ID_INVALID' for row in dirty_result['reconcile']['issues'])==1
