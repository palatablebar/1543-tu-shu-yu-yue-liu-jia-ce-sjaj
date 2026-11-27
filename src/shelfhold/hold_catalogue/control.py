from collections import Counter
from math import isfinite


def accountable_plan(rows, actual_balance, starting_capacity):
    seen = set()
    counts = Counter()
    total = 0
    for row in rows:
        if row['key'] in seen:
            raise ArithmeticError('复核凭证的关联单号不唯一')
        key = row['key']
        seen.add(key)
        state = row['state']
        counts[state] += 1
        if state == '已分派':
            total += row['cost']
        if not isfinite(row['estimate']):
            raise ArithmeticError('非有限估计不能签发')
    if total + actual_balance != starting_capacity:
        raise ArithmeticError('处置清册与工位余额不符')
    return counts, total


def register_hold_catalogue(measurements, estimate):
    notice_lag = measurements['notice_lag']
    walk_mins = measurements['walk_mins']
    weekday = measurements['weekday']
    renewals = measurements['renewals']
    waiting_readers = measurements['waiting_readers']
    held_age = measurements['held_age']
    return {
        '通知后可到馆时长': round(max(0,held_age-notice_lag), 3),
        '最长保留预算': round(96-held_age, 3),
        '每个可用小时待取户': round(waiting_readers/max(1,96-held_age), 3),
        '延迟占已留架比': round(min(1,notice_lag/held_age), 3),
        '复核代价指标': round(waiting_readers*(1+max(0,estimate-12)/30)/24 + held_age/120, 4),
    }


def document_control(rows):
    register = []
    for row in rows:
        if row['state'] not in {'已分派', '暂停', '人工判读'}:
            continue
        note = register_hold_catalogue(row['measurements'], row['estimate'])
        register.append({'单号': row['key'], '区段': row['zone'], '处置': row['state'], **note})
    return register
