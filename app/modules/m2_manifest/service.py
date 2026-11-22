from app.codec import digest
from app.records import group_by, integer, issue, report, token
from app.source import lines
from .paths import checksum, normalize


def ingest(source, _):
    candidates, problems = [], []
    for raw in lines(source, 'objects'):
        data = raw['raw']
        ident = data.get('object_id')
        if not token(ident):
            problems.append(issue(raw, 'OBJECT_ID_INVALID', '原件缺少可对账号'))
            continue
        row = {**raw, 'object_id': ident, 'path': None, 'sha256': None, 'bytes': None}
        try:
            row['path'] = normalize(data.get('path'))
            row['sha256'] = checksum(data.get('sha256'))
            if not integer(data.get('bytes'), maximum=2**63-1):
                raise ValueError('字节数格式错误')
            row['bytes'] = str(data['bytes'])
        except ValueError:
            problems.append(issue(row, 'OBJECT_SCHEMA', '原件路径、字节数或摘要无效'))
        candidates.append(row)
    objects = []
    for group in group_by(candidates, 'object_id').values():
        signatures = {(row['path'], row['sha256'], row['bytes']) for row in group}
        first = {**group[0], 'source_lines': [row['line'] for row in group], 'conflict': False,
                 'source_records': [{key: row[key] for key in ('line','raw')} for row in group]}
        if len(signatures) != 1:
            first['conflict'] = True
            problems.extend(issue(row, 'OBJECT_CONFLICT', '相同编号的固化事实不一致') for row in group)
        elif None in next(iter(signatures)):
            first['conflict'] = True
        else:
            problems.extend(issue(row, 'MANIFEST_DUPLICATE', '相同固化清单已采信') for row in group[1:])
        objects.append(first)
    paths = {}
    for row in candidates:
        if row['path'] is not None:
            paths.setdefault(row['path'], set()).add(row['object_id'])
    by_id = {row['object_id']: row for row in objects}
    for row in objects:
        row['shared'] = None
    for path, ids in paths.items():
        if len(ids) < 2:
            continue
        members = [by_id[ident] for ident in sorted(ids)]
        signatures = {(row['sha256'], row['bytes']) for row in members}
        if len(signatures) == 1 and not any(row['conflict'] for row in members):
            key = digest({'path': path, 'sha256': members[0]['sha256'],
                          'bytes': members[0]['bytes']})[:12]
            keeper = members[0]['object_id']
            for row in members:
                row['shared'] = {'key': key, 'path': path, 'keeper': keeper,
                                 'members': [item['object_id'] for item in members],
                                 'holds_copy': row['object_id'] == keeper}
            continue
        for row in members:
            row['conflict'] = True
            problems.append(issue(row, 'CANONICAL_COLLISION', '归并后路径相同但内容不同，不予合并'))
    return report(objects, problems, input_count=len(source['objects']))
