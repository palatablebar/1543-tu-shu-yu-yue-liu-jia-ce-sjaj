from collections import Counter, defaultdict
from dataclasses import dataclass
from math import ceil

OPEN_HOUR = 10
CLOSE_HOUR = 19
BASE_HOLD = 48


@dataclass(frozen=True, slots=True)
class PickupClock:
    before_contact: int
    horizon: int
    active_hours: int
    receipt_required: bool
    waiting: int


def next_contact_hour(hour, weekday):
    # Noon snapshots, with the pickup desk closed on Mondays.
    until_open = 0
    while True:
        total = hour + until_open + 12
        day, local = divmod(total, 24)
        if (weekday + day) % 7 and OPEN_HOUR <= local < CLOSE_HOUR:
            return hour + until_open
        until_open += 1


def estimate_retention(row):
    source = row['measurements']
    elapsed = round(source['held_age'])
    weekday = round(source['weekday'])
    queue = int(source['waiting_readers'])
    notice = ceil(source['notice_lag'])
    grace = max(0, BASE_HOLD + notice + 6 * source['renewals'] - elapsed)
    first_contact = next_contact_hour(0, weekday)
    no_contact = (notice >= 13 and elapsed >= 34) or first_contact > 0
    handoff = next_contact_hour(ceil(grace), weekday)
    if no_contact:
        handoff = max(handoff, next_contact_hour(first_contact + 6, weekday))
    forecast = min(120, max(0, ceil(row['estimate'])))
    age = max(handoff, forecast)
    working = sum(next_contact_hour(hr, weekday) == hr for hr in range(age))
    return PickupClock(first_contact, handoff, working, no_contact, queue)


def operating_ledger(rows):
    retained = defaultdict(Counter)
    actions = []
    for hold in sorted(rows, key=lambda item: (item['zone'], item['key'])):
        shelf = retained[hold['zone']]
        if hold['unmeasured']:
            shelf['回执待补'] += 1
            actions.append({'业务安排': '补齐留架凭证', '关联单据': hold['key'], '是否占架': True})
            continue
        clock = estimate_retention(hold)
        if hold['state'] == '暂停' or clock.receipt_required:
            desk = '核对送达或延期'
        elif clock.horizon == 0 and clock.waiting:
            desk = '允许馆员核对顺位'
        elif clock.waiting >= 14:
            desk = '通知后续预约者等待'
        else:
            desk = '留架复核'
        shelf[desk] += 1
        shelf['留架工作小时'] += clock.active_hours
        if clock.receipt_required or clock.waiting or hold['state'] == '暂停':
            actions.append({'业务安排': desk, '关联单据': hold['key'], '开放复核间隔小时': clock.horizon,
                            '下次回访间隔小时': clock.before_contact, '顺位待取户': clock.waiting,
                            '占架开放小时': clock.active_hours, '经馆员核对': True})
    for zone, tally in sorted(retained.items()):
        actions.append({'业务安排': '架区占用小计', '架区': zone, **dict(sorted(tally.items()))})
    return actions
