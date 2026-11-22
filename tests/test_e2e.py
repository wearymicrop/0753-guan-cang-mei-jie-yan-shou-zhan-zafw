def test_module_previews_match_archived_run(client):
    run=client.post('/api/runs',json={'sample':'dirty'}).json()
    for stage in ('batches','manifest','mapping','fixity','drift','reconcile'):
        answer=client.get(f'/api/{stage}/dirty')
        assert answer.status_code==200 and answer.json()==run['result'][stage]


def test_index_loads_clean_sample(client):
    response=client.get('/?sample=clean')
    assert response.status_code==200 and '馆藏迁移矩阵' in response.text
    assert client.get('/api/previews/clean').json()['reconcile']['totals']['verified']==24


def test_unknown_sample_error(client):
    response=client.get('/api/mapping/invalid')
    assert response.status_code==404 and response.json()['code']=='UNKNOWN_SAMPLE'
