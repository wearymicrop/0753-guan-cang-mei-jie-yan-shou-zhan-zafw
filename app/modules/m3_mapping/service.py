from app.clock import instant
from app.modules.m1_batches.policy import TIERS
from app.records import group_by, issue, report
from app.source import lines
from .rules import parse, pick


def map_targets(source, sections):
    version = sections['batches']['selected']
    as_of = instant(source['at'])
    all_rules, output, problems = [], [], []
    for record in lines(source, 'routes'):
        try:
            row = parse(record)
        except ValueError:
            problems.append(issue(record, 'ROUTE_SCHEMA', '映射前缀、版本或时段无效'))
            continue
        all_rules.append({**row, 'active': row['version'] == version and row['start'] <= as_of < row['end']})
    by_tier = group_by((row for row in all_rules if row['active']), 'tier')
    for row in sections['manifest']['rows']:
        if row['conflict']:
            continue
        for tier in TIERS:
            path, route_lines, code = pick(row['path'], by_tier.get((tier,), []))
            target = {'object_id':row['object_id'], 'source_path':row['path'], 'path':path,
                      'tier':tier, 'route_lines':route_lines, 'source_lines':row['source_lines'], 'code':code,
                      'shared':row['shared'],
                      'table':'objects', 'line':row['line'], 'raw':row['raw']}
            if code:
                problems.append(issue(target, code, '缺少映射或同优先级规则存在冲突'))
            output.append(target)
    found = group_by((row for row in output if row['path'] is not None), 'tier', 'path')
    for group in found.values():
        if len(group) > 1:
            shared = group[0]['shared']
            complete = shared is not None and {row['object_id'] for row in group} == set(shared['members'])
            if complete and all(row['shared'] and row['shared']['key'] == shared['key'] for row in group):
                continue
            for row in group:
                row['code'] = 'TARGET_COLLISION'
                problems.append(issue(row, 'TARGET_COLLISION', '多份原件映射到同一副本路径'))
    return report(output, problems, rules=all_rules, version=version)
