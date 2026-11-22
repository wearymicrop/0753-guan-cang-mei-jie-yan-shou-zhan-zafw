from app.records import report
from .totals import count


def reconcile(_source, sections):
    rows = sections['drift']['rows']
    totals, identity = count(sections['manifest']['rows'], rows)
    totals['verified_copies'] = sum(copy['state'] == 'verified' for row in rows for copy in row['copies'])
    exceptions = [problem for section in ('batches','manifest','mapping','fixity','drift')
                  for problem in sections[section]['issues']]
    matched = bool(rows) and not totals['difference'] and identity
    sharing = sections['drift'].get('sharing', [])
    summary = {'groups': len(sharing), 'objects': sum(len(group['members']) for group in sharing)}
    for state in ('verified', 'pending', 'conflict'):
        summary[state] = sum(group['state'] == state for group in sharing)
    return report([{'object_id':row['object_id'],'state':row['state'],'path':row['path'],
                    'source_lines':row['source_lines']} for row in rows], exceptions,
                  totals=totals, status='MATCHED' if matched else 'CHECK_REQUIRED', sharing=summary)
