from collections import defaultdict
from math import fsum


def risk_table(history):
    # A hold arrives at its observed shelf age. Include it in the risk set
    # strictly after entry and up to and including the event/censor instant.
    exits = defaultdict(lambda: [0, 0])
    for exit_hour, picked_up, entry_hour in history:
        if exit_hour <= entry_hour:
            raise ValueError('取件或截尾时刻应晚于首次留架观测')
        exits[exit_hour][int(not picked_up)] += 1
    survival = 1.0
    points = []
    entries = iter(sorted(entry for _, _, entry in history))
    next_entry = next(entries, None)
    at_risk = 0
    for hour, (events, censored) in sorted(exits.items()):
        while next_entry is not None and next_entry < hour:
            at_risk += 1
            next_entry = next(entries, None)
        survival *= 1 - events / at_risk
        points.append((hour, survival, at_risk, events, censored))
        at_risk -= events + censored
    return tuple(points)


def restricted_tail(table, passed, horizon=96):
    if horizon <= passed:
        return 0.0
    before = next((value for time, value, *_ in reversed(table) if time <= passed), 1.)
    if before <= 0:
        return 0.0
    cursor = passed
    survival = before
    areas = []
    for hour, probability, *_ in table:
        if not passed < hour < horizon:
            continue
        areas.append((hour - cursor) * survival / before)
        cursor, survival = hour, probability
    areas.append((horizon - cursor) * survival / before)
    return fsum(areas)


def fit_kernel(rows):
    all_records = [(row.outcome, row.observed, row.input_values[5]) for row in rows]
    shelf_types = defaultdict(list)
    for row, followed in zip(rows, all_records, strict=True):
        shelf_types[int(row.input_values[2] >= 4)].append(followed)
    overall = risk_table(all_records)
    conditional = tuple((weekend, risk_table(examples)) for weekend, examples in sorted(shelf_types.items()) if len(examples) >= 12)
    return (overall, conditional), (('总取件样本', len(rows)), ('已取件数', sum(row.observed for row in rows)),
                                    ('分组生存曲线', len(conditional)))


def score_kernel(model, sample):
    overall, curves = model
    weekend = int(sample.input_values[2] >= 4)
    anchor = sample.input_values[5]
    chosen = dict(curves).get(weekend, overall)
    remaining = restricted_tail(chosen, anchor)
    return remaining, (remaining - restricted_tail(overall, anchor), weekend, anchor)
