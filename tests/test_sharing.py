from app.pipeline import evaluate


def row_of(result, ident):
    return next(row for row in result['drift']['rows'] if row['object_id'] == ident)


def group_of(result, ident):
    return next(group for group in result['drift']['sharing'] if ident in group['members'])


def test_same_content_same_path_forms_share_group(shared_result):  # TRAP-27
    first, second = (row_of(shared_result, '0101'), row_of(shared_result, '0102'))
    assert first['shared'] is not None and first['shared']['key'] == second['shared']['key']
    assert first['shared']['members'] == ['0101', '0102']
    assert first['shared']['keeper'] == '0101'
    assert first['shared']['holds_copy'] and not second['shared']['holds_copy']
    assert not first['conflict'] and not second['conflict']
    assert not [row for row in shared_result['manifest']['issues']
                if row['code'] == 'CANONICAL_COLLISION' and row['object_id'] in ('0101', '0102')]


def test_same_name_different_content_is_never_merged(shared_result):
    for ident in ('0103', '0104'):
        item = row_of(shared_result, ident)
        assert item['shared'] is None and item['state'] == 'conflict'
    collisions = [row for row in shared_result['manifest']['issues'] if row['code'] == 'CANONICAL_COLLISION']
    assert [row['object_id'] for row in collisions] == ['0103', '0104']
    assert {row['sha256'] for row in collisions} == {row_of(shared_result, '0103')['sha256'],
                                                     row_of(shared_result, '0104')['sha256']}
    assert all(ident not in ('0103', '0104') for group in shared_result['drift']['sharing']
               for ident in group['members'])


def test_shared_target_is_not_a_collision(shared_result):
    targets = [row for row in shared_result['mapping']['rows'] if row['object_id'] in ('0101', '0102')]
    assert len(targets) == 4 and not [row for row in targets if row['code'] == 'TARGET_COLLISION']
    for tier in ('online', 'vault'):
        assert len({row['path'] for row in targets if row['tier'] == tier}) == 1


def test_group_verified_with_single_physical_copy(shared_result):
    group = group_of(shared_result, '0101')
    assert group['state'] == 'verified' and group['members'] == ['0101', '0102']
    assert group['copies'] == {'online': '阅览池/北港/照片/灯塔/白光.tif',
                               'vault': '永久库/磁带-02/照片/灯塔/白光.tif'}
    observed = [row for row in shared_result['fixity']['rows'] if row['path'] in group['copies'].values()]
    assert len(observed) == 2
    assert row_of(shared_result, '0101')['state'] == row_of(shared_result, '0102')['state'] == 'verified'


def test_missing_copy_keeps_group_pending_and_loses_no_record(shared_result):
    group = group_of(shared_result, '0105')
    assert group['state'] == 'pending'
    assert group['copies'] == {'online': '阅览池/北港/文书/登记/潮汐表.pdf',
                               'vault': '永久库/磁带-02/文书/登记/潮汐表.pdf'}
    for ident in ('0105', '0106'):
        item = row_of(shared_result, ident)
        assert item['state'] == 'pending'
        assert [(copy['tier'], copy['state']) for copy in item['copies']] == [('online', 'verified'),
                                                                              ('vault', 'pending')]


def test_reconcile_keeps_every_identifier_and_counts_sharing(shared_result):
    result = shared_result['reconcile']
    assert result['status'] == 'MATCHED'
    assert len({row['object_id'] for row in result['rows']}) == len(result['rows']) == 7
    assert result['totals'] == {'originals': 7, 'verified': 3, 'pending': 2, 'conflict': 2,
                                'difference': 0, 'expected_bytes': str(
                                    2 * int(row_of(shared_result, '0101')['bytes'])
                                    + 2 * int(row_of(shared_result, '0105')['bytes'])
                                    + int(row_of(shared_result, '0107')['bytes'])),
                                'verified_copies': 8}
    assert result['sharing'] == {'groups': 2, 'objects': 4, 'verified': 1, 'pending': 1, 'conflict': 0}


def test_signed_result_traces_both_directions(shared_result):
    sharing = shared_result['drift']['sharing']
    for ident in ('0101', '0102', '0105', '0106'):
        assert any(ident in group['members'] for group in sharing)
    by_path = {path: group for group in sharing for path in group['copies'].values()}
    assert by_path['阅览池/北港/照片/灯塔/白光.tif']['members'] == ['0101', '0102']
    assert by_path['阅览池/北港/文书/登记/潮汐表.pdf']['members'] == ['0105', '0106']


def test_unclear_facts_keep_records_unmerged(shared):
    shared['objects'].append({'object_id': '0101', 'path': '照片/灯塔/白光.tif',
                              'sha256': 'f' * 64, 'bytes': 999})
    result = evaluate(shared)
    for ident in ('0101', '0102'):
        item = row_of(result, ident)
        assert item['shared'] is None and item['state'] == 'conflict'
    assert not [group for group in result['drift']['sharing']
                if {'0101', '0102'} & set(group['members'])]
    assert group_of(result, '0105')['state'] == 'pending'
    assert result['reconcile']['status'] == 'MATCHED'
    assert len(result['reconcile']['rows']) == 7


def start(client):
    response = client.post('/api/runs', json={'sample': 'shared'})
    assert response.status_code == 200, response.text
    return response.json()


def test_rerun_and_signature_preserve_confirmed_sharing(client):
    run = start(client)
    sharing = run['result']['drift']['sharing']
    assert client.post(f'/api/runs/{run["id"]}/sign',
                       json={'reviewer': '周洁', 'digest': run['manifest']['digest']}).status_code == 200
    replay = client.post(f'/api/runs/{run["id"]}/rerun').json()
    assert replay['reused'] and replay['result']['drift']['sharing'] == sharing
    assert replay['result']['reconcile']['sharing'] == run['result']['reconcile']['sharing']
    again = client.post('/api/runs', json={'sample': 'shared'}).json()
    assert again['reused'] and again['result']['drift']['sharing'] == sharing


def test_export_matches_workbench_view(client):
    run = start(client)
    exported = client.get(f'/api/runs/{run["id"]}/export').json()
    assert exported['result'] == run['result']
    assert exported['result']['drift']['sharing'] == run['result']['drift']['sharing']
    preview = client.get('/api/drift/shared').json()
    assert preview == run['result']['drift']
    assert client.get('/api/reconcile/shared').json() == run['result']['reconcile']


def test_shared_sample_previews_match_archived_run(client):
    run = start(client)
    for stage in ('batches', 'manifest', 'mapping', 'fixity', 'drift', 'reconcile'):
        answer = client.get(f'/api/{stage}/shared')
        assert answer.status_code == 200 and answer.json() == run['result'][stage]
