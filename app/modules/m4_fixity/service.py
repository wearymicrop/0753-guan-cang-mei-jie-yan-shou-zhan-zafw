from app.clock import instant, utc
from app.modules.m1_batches.policy import TIERS
from app.modules.m2_manifest.paths import normalize
from app.records import group_by, issue, report
from app.source import lines
from .bytes import measure


def scan(source, _):
    observations, output, problems = [], [], []
    as_of = instant(source['at'])
    for record in lines(source, 'replicas'):
        raw = record['raw']
        try:
            path = normalize(raw.get('path'))
            when = instant(raw.get('observed'))
            tier = raw.get('tier')
            if tier not in TIERS:
                raise ValueError('副本层级不明')
        except ValueError:
            problems.append(issue(record, 'REPLICA_SCHEMA', '副本路径、层级或时间无效'))
            continue
        row = {**record, 'path':path, 'tier':tier, 't':when, 'observed':utc(when), 'bytes':None, 'sha256':None}
        if when > as_of:
            problems.append(issue(row, 'FUTURE_OBSERVATION', '观察时间超出验收截止'))
            continue
        try:
            row['bytes'], row['sha256'] = measure(raw.get('data_b64'))
        except ValueError:
            problems.append(issue(row, 'PAYLOAD_INVALID', '副本字节载荷无法验签'))
        observations.append(row)
    for group in group_by(observations, 'tier', 'path').values():
        history = sorted(group, key=lambda row: (row['t'], row['line']))
        latest = [row for row in history if row['t'] == history[-1]['t']]
        distinct = {(row['bytes'], row['sha256']) for row in latest}
        current = {**latest[0], 'observation_lines':[row['line'] for row in latest],
                   'history':[{key: row[key] for key in ('line','bytes','sha256','observed','t')} for row in history]}
        if len(distinct) > 1:
            problems.extend(issue(row, 'OBSERVATION_CONFLICT', '同层同路径的当前观察相互矛盾') for row in latest)
            current.update(sha256=None, bytes=None, code='OBSERVATION_CONFLICT')
        else:
            problems.extend(issue(row, 'OBSERVATION_DUPLICATE', '同路径同一时刻为重复验签') for row in latest[1:])
            current['code'] = 'PAYLOAD_INVALID' if current['sha256'] is None else None
        output.append(current)
    return report(output, problems, observed_rows=len(observations))
