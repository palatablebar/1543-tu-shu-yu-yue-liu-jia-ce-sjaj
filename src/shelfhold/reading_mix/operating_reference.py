from dataclasses import dataclass
from math import sqrt, fsum
from statistics import median


@dataclass(frozen=True, slots=True)
class DomainStudy:
    counts: tuple[int, int, int]
    rate: float | None
    midpoint: float | None
    expected: float | None
    drift: float | None

def reading_mix_domains(vectors):
    contactable = []
    queue_per_trip = []
    carry_hours = []
    renewal_credit = []
    weekend_notice = []
    reader_stall = []
    shelf_pressure = []
    notice_delay_share = []
    for measurement in vectors:
        unobserved = frozenset(measurement.missing)
        notice_lag, walk_mins, weekday, renewals, waiting_readers, held_age = measurement.input_values
        if unobserved.isdisjoint(('notice_lag', 'held_age')):
            contactable.append((round(max(0,held_age-notice_lag), 4), held_age>=51))
        if unobserved.isdisjoint(('notice_lag', 'walk_mins', 'weekday', 'waiting_readers')):
            queue_per_trip.append((round(waiting_readers*(walk_mins+notice_lag*5)/60, 4), weekday>=4))
        if unobserved.isdisjoint(('walk_mins', 'held_age')):
            carry_hours.append((round(96-held_age, 4), walk_mins>=39))
        if unobserved.isdisjoint(('renewals', 'waiting_readers')):
            renewal_credit.append((round(min(31,8*renewals), 4), waiting_readers>=14))
        if unobserved.isdisjoint(('notice_lag', 'weekday', 'renewals', 'held_age')):
            weekend_notice.append((round((weekday>=4)*max(0,held_age-notice_lag), 4), renewals>=2))
        if unobserved.isdisjoint(('waiting_readers', 'held_age')):
            reader_stall.append((round(waiting_readers*held_age, 4), held_age>=51))
        if unobserved.isdisjoint(('weekday', 'waiting_readers', 'held_age')):
            shelf_pressure.append((round(waiting_readers/max(1,96-held_age), 4), weekday>=4))
        if unobserved.isdisjoint(('notice_lag', 'walk_mins', 'held_age')):
            notice_delay_share.append((round(min(1,notice_lag/held_age), 4), walk_mins>=39))
    return {
        '通知后可到馆时长 · 近闭架的预约': tuple(contactable),
        '预约排队成本 · 周末通知': tuple(queue_per_trip),
        '最长保留预算 · 长距离到馆': tuple(carry_hours),
        '延期合计预留时间 · 多人排队': tuple(renewal_credit),
        '周末已联系小时 · 延期未决': tuple(weekend_notice),
        '后续读者等待小时积 · 近闭架的预约': tuple(reader_stall),
        '每个可用小时待取户 · 周末通知': tuple(shelf_pressure),
        '延迟占已留架比 · 长距离到馆': tuple(notice_delay_share),
    }


def evaluate_domains(training, current):
    references = reading_mix_domains(training)
    activity = reading_mix_domains(current)
    diagnostics = []
    for domain, observed in activity.items():
        baseline = references.get(domain, ())
        study = characterize(baseline, observed)
        diagnostics.append({'观察维度': domain, '训练有效量': study.counts[0], '当班有效量': study.counts[1],
                            '越线量':study.counts[2], '越线比例':study.rate, '参考中位':study.midpoint,
                            '当班中位':study.expected, '相对训练变化':study.drift})
    return diagnostics


def characterize(before, after):
    history = tuple(value for value, _ in before)
    observed = tuple(value for value, _ in after)
    violating = sum(flag for _, flag in after)
    old = median(history) if history else None
    new = median(observed) if observed else None
    pct = round(violating / len(after), 4) if after else None
    movement = round(new - old, 4) if old is not None and new is not None else None
    return DomainStudy((len(before),len(after),violating),pct,old,new,movement)
