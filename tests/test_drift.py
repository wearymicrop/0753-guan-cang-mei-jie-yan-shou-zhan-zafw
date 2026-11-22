def copies(result, ident):
    return next(row for row in result['drift']['rows'] if row['object_id']==ident)


def test_same_size_digest_mismatch(dirty_result):
    item=copies(dirty_result,'0003')
    actual=item['copies'][0]
    assert actual['bytes']==item['bytes'] and actual['sha256']!=item['sha256'] and actual['code']=='HASH_DRIFT'


def test_missing_cold_copy_stays_pending(dirty_result):  # TRAP-21
    item=copies(dirty_result,'0002')
    assert item['state']=='pending' and [(copy['tier'],copy['state']) for copy in item['copies']]==[('online','verified'),('vault','pending')]


def test_historical_drift_repaired(dirty_result):
    item=copies(dirty_result,'0007')
    assert item['state']=='verified' and item['copies'][1]['code']=='DRIFT_RECOVERED'


def test_invalid_payload_keeps_conflict(dirty_result):
    item=copies(dirty_result,'0010')
    assert item['state']=='conflict' and item['copies'][0]['code']=='PAYLOAD_INVALID'


def test_orphan_replica_keeps_source_line(dirty_result):
    issue=next(row for row in dirty_result['drift']['issues'] if row.get('path')=='散件/暂存/未登记.txt')
    assert issue['code']=='ORPHAN_REPLICA' and issue['line']>40


def test_byte_difference_precedes_hash_drift(dirty_result):
    item=copies(dirty_result,'0004')
    assert int(item['bytes'])-int(item['copies'][1]['bytes'])==7 and item['copies'][1]['code']=='SIZE_DRIFT'
