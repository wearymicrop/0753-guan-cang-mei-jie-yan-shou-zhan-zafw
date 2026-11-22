def compare(original, target, current):
    if target['code']:
        return 'conflict', target['code']
    if current is None:
        return 'pending', 'REPLICA_MISSING'
    if current['code']:
        return 'conflict', current['code']
    if current['bytes'] != original['bytes']:
        return 'conflict', 'SIZE_DRIFT'
    if current['sha256'] != original['sha256']:
        return 'conflict', 'HASH_DRIFT'
    if any(item['sha256'] not in (None, original['sha256']) for item in current['history'] if item['t'] < current['t']):
        return 'verified', 'DRIFT_RECOVERED'
    return 'verified', None
