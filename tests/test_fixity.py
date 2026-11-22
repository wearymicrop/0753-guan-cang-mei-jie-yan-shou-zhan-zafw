import pytest

from app.modules.m4_fixity.bytes import measure


def test_sha256_from_actual_empty_bytes():
    assert measure('')==('0','e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')


def test_current_copy_matches_manifest(clean_result):
    copy=clean_result['fixity']['rows'][0]
    assert copy['sha256']==clean_result['manifest']['rows'][0]['sha256']


def test_invalid_payload_is_quarantined(dirty_result):  # TRAP-16
    row=next(row for row in dirty_result['fixity']['issues'] if row['code']=='PAYLOAD_INVALID')
    assert row['sha256'] is None and row['raw']['data_b64']=='***损坏***'
    with pytest.raises(ValueError):
        measure('aGVsbG8')


def test_same_instant_has_same_key(dirty_result):  # TRAP-11
    result=dirty_result['fixity']
    assert result['reasons']['OBSERVATION_DUPLICATE']==1
    assert next(row for row in result['rows'] if row['path'].endswith('/机房侧视.tif') and row['tier']=='vault')['observed']=='2026-11-20T08:00:00Z'


def test_future_scan_cannot_replace_current(dirty_result):  # TRAP-13
    result=dirty_result['fixity']
    assert result['reasons']['FUTURE_OBSERVATION']==1
    row=next(row for row in result['rows'] if row['path'].endswith('/仓门.tif') and row['tier']=='online')
    assert len(row['history'])==1 and row['observed']=='2026-11-20T08:00:00Z'


def test_same_time_disagreement_loses_no_evidence(dirty_result):
    row=next(row for row in dirty_result['fixity']['rows'] if row['code']=='OBSERVATION_CONFLICT')
    assert row['sha256'] is None and len({record['sha256'] for record in row['history']})==2
