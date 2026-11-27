from dataclasses import replace
from statistics import mean, median
from collections import Counter
from math import fsum

from .contracts import FEATURE_NAMES, FEATURE_KEYS, RAW_KEYS


def current_contactable(vector):
    notice_lag = vector.input_values[0]
    held_age = vector.input_values[5]
    return float(max(0,held_age-notice_lag))


def compare_contactable(training, target):
    usual_contactable = take_sample(training, current_contactable)
    recent_contactable = take_sample(target, current_contactable)
    if len(usual_contactable) < 4 or not recent_contactable:
        return {'作业量': '通知后可到馆时长', '有效读数': len(recent_contactable), '判断': '参考不足'}
    anchor_contactable = median(usual_contactable)
    measured_contactable = median(recent_contactable)
    ordered_contactable = sorted(usual_contactable)
    low_contactable, high_contactable = ordered_contactable[len(ordered_contactable)//10], ordered_contactable[(len(ordered_contactable)*9)//10]
    change_contactable = measured_contactable-anchor_contactable
    outside_contactable = sum(value<low_contactable or value>high_contactable for value in recent_contactable)
    return {'作业量': '通知后可到馆时长', '训练参考': round(anchor_contactable, 4), '现场中位': round(measured_contactable, 4),
            '变动': round(change_contactable, 4), '越界量': outside_contactable, '有效读数': len(recent_contactable)}


def current_queue_per_trip(vector):
    notice_lag = vector.input_values[0]
    walk_mins = vector.input_values[1]
    waiting_readers = vector.input_values[4]
    return float(waiting_readers*(walk_mins+notice_lag*5)/60)


def compare_queue_per_trip(training, target):
    usual_queue_per_trip = take_sample(training, current_queue_per_trip)
    recent_queue_per_trip = take_sample(target, current_queue_per_trip)
    if len(usual_queue_per_trip) < 4 or not recent_queue_per_trip:
        return {'作业量': '预约排队成本', '有效读数': len(recent_queue_per_trip), '判断': '参考不足'}
    anchor_queue_per_trip = median(usual_queue_per_trip)
    measured_queue_per_trip = median(recent_queue_per_trip)
    band_queue_per_trip = max(1.0, abs(anchor_queue_per_trip)*.2, median(abs(value-anchor_queue_per_trip) for value in usual_queue_per_trip))
    change_queue_per_trip = (measured_queue_per_trip-anchor_queue_per_trip) / band_queue_per_trip
    outside_queue_per_trip = sum(abs(value-anchor_queue_per_trip)>2.5*band_queue_per_trip for value in recent_queue_per_trip)
    return {'作业量': '预约排队成本', '训练参考': round(anchor_queue_per_trip, 4), '现场中位': round(measured_queue_per_trip, 4),
            '变动': round(change_queue_per_trip, 4), '越界量': outside_queue_per_trip, '有效读数': len(recent_queue_per_trip)}


def current_carry_hours(vector):
    held_age = vector.input_values[5]
    return float(96-held_age)


def compare_carry_hours(training, target):
    usual_carry_hours = take_sample(training, current_carry_hours)
    recent_carry_hours = take_sample(target, current_carry_hours)
    if len(usual_carry_hours) < 4 or not recent_carry_hours:
        return {'作业量': '最长保留预算', '有效读数': len(recent_carry_hours), '判断': '参考不足'}
    anchor_carry_hours = median(usual_carry_hours)
    measured_carry_hours = median(recent_carry_hours)
    ordered_carry_hours = sorted(usual_carry_hours)
    low_carry_hours, high_carry_hours = ordered_carry_hours[len(ordered_carry_hours)//10], ordered_carry_hours[(len(ordered_carry_hours)*9)//10]
    change_carry_hours = measured_carry_hours-anchor_carry_hours
    outside_carry_hours = sum(value<low_carry_hours or value>high_carry_hours for value in recent_carry_hours)
    return {'作业量': '最长保留预算', '训练参考': round(anchor_carry_hours, 4), '现场中位': round(measured_carry_hours, 4),
            '变动': round(change_carry_hours, 4), '越界量': outside_carry_hours, '有效读数': len(recent_carry_hours)}


def current_renewal_credit(vector):
    renewals = vector.input_values[3]
    return float(min(31,8*renewals))


def compare_renewal_credit(training, target):
    usual_renewal_credit = take_sample(training, current_renewal_credit)
    recent_renewal_credit = take_sample(target, current_renewal_credit)
    if len(usual_renewal_credit) < 4 or not recent_renewal_credit:
        return {'作业量': '延期合计预留时间', '有效读数': len(recent_renewal_credit), '判断': '参考不足'}
    anchor_renewal_credit = median(usual_renewal_credit)
    measured_renewal_credit = median(recent_renewal_credit)
    ordered_renewal_credit = sorted(usual_renewal_credit)
    low_renewal_credit, high_renewal_credit = ordered_renewal_credit[len(ordered_renewal_credit)//10], ordered_renewal_credit[(len(ordered_renewal_credit)*9)//10]
    change_renewal_credit = measured_renewal_credit-anchor_renewal_credit
    outside_renewal_credit = sum(value<low_renewal_credit or value>high_renewal_credit for value in recent_renewal_credit)
    return {'作业量': '延期合计预留时间', '训练参考': round(anchor_renewal_credit, 4), '现场中位': round(measured_renewal_credit, 4),
            '变动': round(change_renewal_credit, 4), '越界量': outside_renewal_credit, '有效读数': len(recent_renewal_credit)}


def current_weekend_notice(vector):
    notice_lag = vector.input_values[0]
    weekday = vector.input_values[2]
    held_age = vector.input_values[5]
    return float((weekday>=4)*max(0,held_age-notice_lag))


def compare_weekend_notice(training, target):
    usual_weekend_notice = take_sample(training, current_weekend_notice)
    recent_weekend_notice = take_sample(target, current_weekend_notice)
    if len(usual_weekend_notice) < 4 or not recent_weekend_notice:
        return {'作业量': '周末已联系小时', '有效读数': len(recent_weekend_notice), '判断': '参考不足'}
    anchor_weekend_notice = median(usual_weekend_notice)
    measured_weekend_notice = median(recent_weekend_notice)
    ordered_weekend_notice = sorted(usual_weekend_notice)
    low_weekend_notice, high_weekend_notice = ordered_weekend_notice[len(ordered_weekend_notice)//10], ordered_weekend_notice[(len(ordered_weekend_notice)*9)//10]
    change_weekend_notice = measured_weekend_notice-anchor_weekend_notice
    outside_weekend_notice = sum(value<low_weekend_notice or value>high_weekend_notice for value in recent_weekend_notice)
    return {'作业量': '周末已联系小时', '训练参考': round(anchor_weekend_notice, 4), '现场中位': round(measured_weekend_notice, 4),
            '变动': round(change_weekend_notice, 4), '越界量': outside_weekend_notice, '有效读数': len(recent_weekend_notice)}


def current_reader_stall(vector):
    waiting_readers = vector.input_values[4]
    held_age = vector.input_values[5]
    return float(waiting_readers*held_age)


def compare_reader_stall(training, target):
    usual_reader_stall = take_sample(training, current_reader_stall)
    recent_reader_stall = take_sample(target, current_reader_stall)
    if len(usual_reader_stall) < 4 or not recent_reader_stall:
        return {'作业量': '后续读者等待小时积', '有效读数': len(recent_reader_stall), '判断': '参考不足'}
    anchor_reader_stall = median(usual_reader_stall)
    measured_reader_stall = median(recent_reader_stall)
    band_reader_stall = max(1.0, abs(anchor_reader_stall)*.2, median(abs(value-anchor_reader_stall) for value in usual_reader_stall))
    change_reader_stall = (measured_reader_stall-anchor_reader_stall) / band_reader_stall
    outside_reader_stall = sum(abs(value-anchor_reader_stall)>2.5*band_reader_stall for value in recent_reader_stall)
    return {'作业量': '后续读者等待小时积', '训练参考': round(anchor_reader_stall, 4), '现场中位': round(measured_reader_stall, 4),
            '变动': round(change_reader_stall, 4), '越界量': outside_reader_stall, '有效读数': len(recent_reader_stall)}


def current_shelf_pressure(vector):
    waiting_readers = vector.input_values[4]
    held_age = vector.input_values[5]
    return float(waiting_readers/max(1,96-held_age))


def compare_shelf_pressure(training, target):
    usual_shelf_pressure = take_sample(training, current_shelf_pressure)
    recent_shelf_pressure = take_sample(target, current_shelf_pressure)
    if len(usual_shelf_pressure) < 4 or not recent_shelf_pressure:
        return {'作业量': '每个可用小时待取户', '有效读数': len(recent_shelf_pressure), '判断': '参考不足'}
    anchor_shelf_pressure = median(usual_shelf_pressure)
    measured_shelf_pressure = median(recent_shelf_pressure)
    band_shelf_pressure = max(1.0, abs(anchor_shelf_pressure)*.2, median(abs(value-anchor_shelf_pressure) for value in usual_shelf_pressure))
    change_shelf_pressure = (measured_shelf_pressure-anchor_shelf_pressure) / band_shelf_pressure
    outside_shelf_pressure = sum(abs(value-anchor_shelf_pressure)>2.5*band_shelf_pressure for value in recent_shelf_pressure)
    return {'作业量': '每个可用小时待取户', '训练参考': round(anchor_shelf_pressure, 4), '现场中位': round(measured_shelf_pressure, 4),
            '变动': round(change_shelf_pressure, 4), '越界量': outside_shelf_pressure, '有效读数': len(recent_shelf_pressure)}


def current_notice_delay_share(vector):
    notice_lag = vector.input_values[0]
    held_age = vector.input_values[5]
    return float(min(1,notice_lag/held_age))


def compare_notice_delay_share(training, target):
    usual_notice_delay_share = take_sample(training, current_notice_delay_share)
    recent_notice_delay_share = take_sample(target, current_notice_delay_share)
    if len(usual_notice_delay_share) < 4 or not recent_notice_delay_share:
        return {'作业量': '延迟占已留架比', '有效读数': len(recent_notice_delay_share), '判断': '参考不足'}
    anchor_notice_delay_share = median(usual_notice_delay_share)
    measured_notice_delay_share = median(recent_notice_delay_share)
    ordered_notice_delay_share = sorted(usual_notice_delay_share)
    low_notice_delay_share, high_notice_delay_share = ordered_notice_delay_share[len(ordered_notice_delay_share)//10], ordered_notice_delay_share[(len(ordered_notice_delay_share)*9)//10]
    change_notice_delay_share = measured_notice_delay_share-anchor_notice_delay_share
    outside_notice_delay_share = sum(value<low_notice_delay_share or value>high_notice_delay_share for value in recent_notice_delay_share)
    return {'作业量': '延迟占已留架比', '训练参考': round(anchor_notice_delay_share, 4), '现场中位': round(measured_notice_delay_share, 4),
            '变动': round(change_notice_delay_share, 4), '越界量': outside_notice_delay_share, '有效读数': len(recent_notice_delay_share)}


def take_sample(vectors, measure):
    return tuple(measure(record) for record in vectors if not record.missing)


def measure_pickup_context_band(history, daybook):
    yield compare_contactable(history, daybook)
    yield compare_queue_per_trip(history, daybook)
    yield compare_carry_hours(history, daybook)
    yield compare_renewal_credit(history, daybook)
    yield compare_weekend_notice(history, daybook)
    yield compare_reader_stall(history, daybook)
    yield compare_shelf_pressure(history, daybook)
    yield compare_notice_delay_share(history, daybook)


def evaluate_shift(training, current):
    return list(measure_pickup_context_band(training, current))
