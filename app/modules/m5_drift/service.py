from app.records import group_by, issue, report
from .classify import compare

DETAIL = {'REPLICA_MISSING':'目标层未收到副本', 'SIZE_DRIFT':'字节数与固化清单不等',
          'HASH_DRIFT':'同字节数下摘要已变化', 'DRIFT_RECOVERED':'早期漂移已修复',
          'PAYLOAD_INVALID':'副本字节无法读取', 'OBSERVATION_CONFLICT':'当前字节证据互斥'}


def compare_copies(_source, sections):
    targets = group_by(sections['mapping']['rows'], 'object_id')
    present = {(row['tier'], row['path']):row for row in sections['fixity']['rows']}
    expected, output, problems = set(), [], []
    for original in sections['manifest']['rows']:
        copies = []
        for target in targets.get((original['object_id'],), []):
            key = (target['tier'], target['path'])
            if target['path'] is not None:
                expected.add(key)
            current = present.get(key)
            state, code = compare(original, target, current)
            copies.append({**target, 'state':state, 'code':code,
                           'sha256':current['sha256'] if current else None, 'bytes':current['bytes'] if current else None,
                           'observed':current['observed'] if current else None,
                           'replica_lines':current['observation_lines'] if current else [],
                           'history':current['history'] if current else []})
            if code in DETAIL:
                problems.append(issue(current or target, code, DETAIL[code]))
        states = {copy['state'] for copy in copies}
        state = 'conflict' if original['conflict'] or 'conflict' in states else 'pending' if 'pending' in states else 'verified'
        output.append({**original, 'state':state, 'copies':copies})
    for key, row in present.items():
        if key not in expected:
            problems.append(issue(row, 'ORPHAN_REPLICA', '副本未归属到当前合法映射'))
    return report(output, problems)
