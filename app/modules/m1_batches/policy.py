from app.clock import instant
from app.records import token

TIERS = ('online', 'vault')


def period(raw):
    start = instant(raw.get('start'))
    end = instant(raw.get('end'))
    if start >= end:
        raise ValueError('版本有效期逆序')
    return start, end


def parse(record):
    raw = record['raw']
    if not token(raw.get('version')) or raw.get('tiers') != list(TIERS):
        raise ValueError('版本必须声明阅览与冷存两层')
    start, end = period(raw)
    return {**record, 'version': raw['version'], 'start': start, 'end': end, 'tiers': list(TIERS)}
