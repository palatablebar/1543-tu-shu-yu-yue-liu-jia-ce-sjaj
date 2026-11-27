from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class JointAction:
    case: str
    work_units: int
    notes: str
    changes: dict[str, tuple[float, float]]

    def evidence(self, old_value, new_value, extrapolates):
        return {'联动推演':self.case, '用量':self.work_units, '先决条件':self.notes,
                '原预测':round(old_value,4), '替换预测':round(new_value,4),
                '变化':round(new_value-old_value,4), '超训练域':bool(extrapolates),
                '联动量测':{item:{'原值':before,'替换值':after} for item,(before,after) in self.changes.items()}}


def simulate_manual_contact(readings, invalid):
    notice_lag, held_age = readings[0], readings[5]
    if invalid.intersection(('notice_lag', 'held_age')):
        return None
    if not (notice_lag>=5 and held_age<=56):
        return None
    notice_lag_adjusted = notice_lag-5
    held_age_adjusted = held_age+8
    inspected = {
        'notice_lag': (notice_lag, notice_lag_adjusted),
        'held_age': (held_age, held_age_adjusted),
    }
    if any(new != old for old,new in inspected.values()):
        return JointAction('通知复发后复查', 1, '模拟修正晚报回执并等待后续取件', inspected)
    return None


def simulate_release_extensions(readings, invalid):
    renewals, waiting_readers = readings[3], readings[4]
    if invalid.intersection(('renewals', 'waiting_readers')):
        return None
    if not (renewals>=2 and waiting_readers>=4):
        return None
    renewals_adjusted = renewals-2
    waiting_readers_adjusted = waiting_readers-3
    inspected = {
        'renewals': (renewals, renewals_adjusted),
        'waiting_readers': (waiting_readers, waiting_readers_adjusted),
    }
    if any(new != old for old,new in inspected.values()):
        return JointAction('回收未激活延期', 1, '对延期状态和下游预约一并签回', inspected)
    return None


def simulate_after_hours_notice(readings, invalid):
    walk_mins, weekday = readings[1], readings[2]
    if invalid.intersection(('walk_mins', 'weekday')):
        return None
    if not (weekday>=4 and walk_mins>=14):
        return None
    weekday_adjusted = weekday-3
    walk_mins_adjusted = walk_mins-10
    inspected = {
        'weekday': (weekday, weekday_adjusted),
        'walk_mins': (walk_mins, walk_mins_adjusted),
    }
    if any(new != old for old,new in inspected.values()):
        return JointAction('开新取件窗', 2, '转交开门时段更近的分馆', inspected)
    return None


def simulate_move_reserved_book(readings, invalid):
    notice_lag, walk_mins = readings[0], readings[1]
    if invalid.intersection(('notice_lag', 'walk_mins')):
        return None
    if not (walk_mins>=20 and notice_lag>=3):
        return None
    walk_mins_adjusted = walk_mins-14
    notice_lag_adjusted = notice_lag-3
    inspected = {
        'walk_mins': (walk_mins, walk_mins_adjusted),
        'notice_lag': (notice_lag, notice_lag_adjusted),
    }
    if any(new != old for old,new in inspected.values()):
        return JointAction('换架补通知', 2, '近馆接手并转发短信', inspected)
    return None


def simulate_extend_high_queue(readings, invalid):
    renewals, held_age = readings[3], readings[5]
    if invalid.intersection(('renewals', 'held_age')):
        return None
    if not (renewals<4 and held_age<=56):
        return None
    renewals_adjusted = renewals+1
    held_age_adjusted = held_age+8
    inspected = {
        'renewals': (renewals, renewals_adjusted),
        'held_age': (held_age, held_age_adjusted),
    }
    if any(new != old for old,new in inspected.values()):
        return JointAction('二次留架', 1, '记录有效续留并计划下一次核查', inspected)
    return None


def options(values, missing):
    measurements=tuple(values)
    unobserved=frozenset(missing)
    cases=(
        simulate_manual_contact(measurements, unobserved),
        simulate_release_extensions(measurements, unobserved),
        simulate_after_hours_notice(measurements, unobserved),
        simulate_move_reserved_book(measurements, unobserved),
        simulate_extend_high_queue(measurements, unobserved),
    )
    return tuple(action for action in cases if action is not None)
