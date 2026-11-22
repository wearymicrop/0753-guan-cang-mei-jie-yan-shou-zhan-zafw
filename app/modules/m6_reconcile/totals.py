from collections import Counter


def count(originals, outcomes):
    states = Counter(row['state'] for row in outcomes)
    original_ids = Counter(row['object_id'] for row in originals)
    outcome_ids = Counter(row['object_id'] for row in outcomes)
    totals = {'originals':len(originals), 'verified':states['verified'],
              'pending':states['pending'], 'conflict':states['conflict']}
    totals['difference'] = totals['originals'] - sum(totals[key] for key in ('verified','pending','conflict'))
    totals['expected_bytes'] = str(sum(int(row['bytes']) for row in originals if row['bytes'] is not None and not row['conflict']))
    return totals, original_ids == outcome_ids and all(amount == 1 for amount in outcome_ids.values())
