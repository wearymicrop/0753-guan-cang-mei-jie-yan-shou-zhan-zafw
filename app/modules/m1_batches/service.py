from app.clock import instant, utc
from app.records import issue, report
from app.source import lines
from .policy import parse


def resolve(source, _):
    as_of = instant(source['at'])
    seen, options, problems = set(), [], []
    for record in lines(source, 'catalogs'):
        try:
            row = parse(record)
        except ValueError:
            problems.append(issue(record, 'CATALOG_SCHEMA', '版本或双副本策略无效'))
            continue
        key = (row['version'], row['start'], row['end'])
        if key in seen:
            problems.append(issue(row, 'CATALOG_DUPLICATE', '重复发布相同批次策略'))
            continue
        seen.add(key)
        options.append({**row, 'active': row['start'] <= as_of < row['end']})
    active = [row for row in options if row['active']]
    if len(active) != 1:
        code = 'CATALOG_OVERLAP' if active else 'CATALOG_MISSING'
        affected = active or [{'table': 'catalogs', 'line': None, 'raw': None}]
        problems.extend(issue(row, code, '必须有一份生效策略') for row in affected)
    return report(options, problems, selected=active[0]['version'] if len(active) == 1 else None,
                  as_of=utc(as_of))
