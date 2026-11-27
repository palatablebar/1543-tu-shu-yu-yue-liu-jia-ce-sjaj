from collections import Counter, defaultdict
from math import fsum


def groups_for_tail_replay(raw):
    notice_lag, walk_mins, weekday, renewals, waiting_readers, held_age = raw
    if held_age>=51:
        yield '近闭架的预约'
    if weekday>=4:
        yield '周末通知'
    if walk_mins>=39:
        yield '长距离到馆'
    if waiting_readers>=14:
        yield '多人排队'
    if renewals>=2:
        yield '延期未决'

def release_evidence(rows, boundary):
    checked = Counter()
    delays = []
    for ticket in rows:
        wait = ticket.raw.outcome
        if wait is None:
            checked['缺返读'] += 1
        elif not ticket.raw.observed:
            checked['未结束留架'] += 1
            if ticket.estimate < min(wait,boundary):
                checked['预测过早'] += 1
        else:
            checked['归档取件'] += 1
            if ticket.estimate < min(wait,boundary):
                delays.append(wait-ticket.estimate)
                checked['预测过早'] += 1
            elif ticket.estimate>=boundary and wait<boundary:
                checked['延留建议'] += 1
    return {'实绩数':checked['归档取件'],'右截尾数':checked['未结束留架'],'缺返读':checked['缺返读'],
            '提前释放风险数':checked['预测过早'],'延留建议数':checked['延留建议'],
            '确认提前释放小时':round(fsum(delays),2)}


def replay_slices(points, threshold, *, risk_model=False):
    history = defaultdict(list)
    for sample in points:
        for segment in groups_for_tail_replay(sample.raw.input_values):
            history[segment].append(sample)
    return [{'难点':area,**release_evidence(history[area],threshold)} for area in ('近闭架的预约', '周末通知', '长距离到馆', '多人排队', '延期未决')]
