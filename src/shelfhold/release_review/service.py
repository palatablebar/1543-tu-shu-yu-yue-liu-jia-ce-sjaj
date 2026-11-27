from .operating_ledger import operating_ledger
from collections import Counter, defaultdict
from math import exp, isfinite

from .contracts import RuleNotice, Job, Plan, Policy, RISK_CUTOFF
from .constraints import WorkOrder, apply_release_review


def measures(raw):
    return tuple(raw)


def signals(data, estimate, missing=()):
    absent=frozenset(missing)
    notice_lag, walk_mins, weekday, renewals, waiting_readers, held_age = data
    hits = []
    if not absent.intersection(('renewals', 'held_age')) and (renewals >= 3 and held_age < 44):
        hits.append(RuleNotice('EXTENSION_OPEN', '延期未处理，保持留架', hard=True))
    if not absent.intersection(('waiting_readers',)) and (waiting_readers >= 14 and estimate >= 30):
        hits.append(RuleNotice('CROWDED_SHELF', '优先核实架位', hard=False))
    if not absent.intersection(('notice_lag', 'held_age')) and (notice_lag >= 13 and held_age >= 34):
        hits.append(RuleNotice('NOTICE_LATE', '核对通知回执', hard=False))
    return tuple(hits)


def expected_load(measurements):
    notice_lag, walk_mins, weekday, renewals, waiting_readers, held_age = measurements
    return 1 + int(waiting_readers < 3)


def dispatch_pressure(values, estimate):
    notice_lag, walk_mins, weekday, renewals, waiting_readers, held_age = values
    return waiting_readers*(1+max(0,estimate-12)/30)/24 + held_age/120


def confidence_weight(estimate, cutoff):
    shifted = (estimate - cutoff) / max(.5, abs(cutoff) * .35)
    if shifted >= 0:
        return 1 / (1 + exp(-shifted))
    bounded = exp(shifted)
    return bounded / (1 + bounded)


def recommend(assessment, attention, policy):
    raw = assessment.raw
    data = measures(raw.input_values)
    estimate = assessment.estimate
    domain_codes = signals(data, estimate, raw.missing)
    level = confidence_weight(estimate, policy.trigger)
    cost = expected_load(data)
    if not isfinite(estimate) or not 1 <= cost <= 12:
        raise ValueError('处置量不在有效范围')
    if domain_codes and domain_codes[0].hard:
        state = '暂停'
        reason = domain_codes[0].rule_id
        summary = domain_codes[0].meaning
    elif raw.key in attention or assessment.uncertain:
        state = '人工判读'
        reason = 'OUT_OF_REFERENCE' if raw.key in attention else 'INSUFFICIENT_CALIBRATION'
        summary = '分布偏移或校准量不足，需核对原始单据'
    elif domain_codes or estimate >= policy.trigger:
        state = '候选'
        reason = domain_codes[0].rule_id if domain_codes else 'ABOVE_TRIGGER'
        summary = domain_codes[0].meaning if domain_codes else '达到本班复核阈值'
    else:
        state = '观察'
        reason = 'BELOW_TRIGGER'
        summary = '保留记录并等待下一次巡查'
    return Job(raw.key, raw.cohort, round(estimate, 4), assessment.lower, assessment.upper, cost,
               state, reason, summary, round(level, 5), tuple(item.rule_id for item in domain_codes))


def allocate(assessments, attention, policy):
    indexed = {}
    for document in assessments:
        work = recommend(document,attention,policy)
        if work.key in indexed:
            raise ValueError('待裁决单重复登记')
        indexed[work.key] = WorkOrder(work,document)
    account = {key:action.job for key,action in indexed.items()}
    spent = Counter()
    slots = policy.capacity
    def record(event, code, reason):
        first = event.job
        account[first.key] = first.change('候补',code,reason)

    def reserve(event):
        nonlocal slots
        original = event.job
        amount = original.cost
        group_total = spent[original.cohort] + amount
        if group_total > policy.group_quota:
            record(event,'GROUP_CAP_REACHED','本作业区额度使用完毕')
            return False
        if amount > slots:
            record(event,'CAPACITY_REACHED','准备候补，当前班次已达上限')
            return False
        spent[original.cohort] = group_total
        slots -= amount
        account[original.key] = original.change('已分派',original.reason,original.summary)
        return True

    candidates = [ticket for ticket in indexed.values() if ticket.job.state=='候选']
    def key(ticket):
        operation = counter_window(ticket.assessment.raw.input_values)
        return (not bool(ticket.job.rule_hits), -dispatch_pressure(ticket.assessment.raw.input_values,ticket.job.estimate),
                operation,-ticket.job.priority,ticket.job.key)
    apply_release_review(sorted(candidates,key=key),reserve,record)
    if any(record.state=='候选' for record in account.values()):
        raise ArithmeticError('派发工位未明确')
    status_order={'已分派':0,'暂停':1,'候补':2,'人工判读':3,'观察':4}
    handoff=tuple(sorted(account.values(),key=lambda item:(status_order[item.state],-item.priority,item.key)))
    return Plan(handoff,policy.capacity,slots,tuple(sorted(spent.items())))


def plan_jobs(assessments, attention, capacity, mode='balanced'):
    return allocate(assessments, frozenset(attention), Policy.select(capacity, mode))


def action_evidence(plan):
    counts = Counter(job.state for job in plan.jobs)
    status = [{'处置': state, '单量': count} for state, count in sorted(counts.items())]
    status.extend({'处置': '分区 ' + group, '额度': cost} for group, cost in plan.used_by_group)
    status += [{'处置': '剩余额度', '额度': plan.balance}]
    return status


def counter_window(raw):
    held_age = raw[5]
    return int(held_age//12)


def operating_group(assessments, progression):
    source={line.raw.key:line.raw.input_values for line in assessments}
    cells=Counter()
    for work in progression.jobs:
        if work.state != '已分派':
            continue
        band=counter_window(source[work.key])
        cells[work.cohort,band] += work.cost
    return [{ '作业区': zone, '馆员台': band, '班组用量': total } for (zone,band),total in sorted(cells.items())]
