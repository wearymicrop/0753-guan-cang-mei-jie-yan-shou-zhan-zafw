from app.modules.m1_batches.policy import TIERS, period
from app.modules.m2_manifest.paths import normalize
from app.records import token


def parse(record):
    raw = record['raw']
    version, tier = raw.get('version'), raw.get('tier')
    if not token(version) or tier not in TIERS:
        raise ValueError('路由版本或层级无效')
    start, end = period(raw)
    prefix = '' if raw.get('from_prefix') == '' else normalize(raw.get('from_prefix'))
    target = normalize(raw.get('to_prefix'))
    return {**record, 'version':version, 'tier':tier, 'start':start, 'end':end,
            'prefix':prefix, 'target':target, 'depth':len(prefix.split('/')) if prefix else 0}


def pick(path, rules):
    matching = [rule for rule in rules if not rule['prefix'] or path.startswith(rule['prefix'] + '/')]
    if not matching:
        return None, [], 'ROUTE_MISSING'
    depth = max(rule['depth'] for rule in matching)
    eligible = [rule for rule in matching if rule['depth'] == depth]
    candidates = {rule['target'] + '/' + path[len(rule['prefix']):].lstrip('/') for rule in eligible}
    if len(candidates) != 1:
        return None, [rule['line'] for rule in eligible], 'ROUTE_OVERLAP'
    return next(iter(candidates)), [rule['line'] for rule in eligible], None
