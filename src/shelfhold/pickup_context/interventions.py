from dataclasses import replace
from statistics import median

from .contracts import PickupContext, Proposal


def measure_pickup_context(values) -> PickupContext:
    notice_lag, walk_mins, weekday, renewals, waiting_readers, held_age = values
    return PickupContext(
        contactable=max(0,held_age-notice_lag),
        queue_per_trip=waiting_readers*(walk_mins+notice_lag*5)/60,
        carry_hours=96-held_age,
        renewal_credit=min(31,8*renewals),
        weekend_notice=(weekday>=4)*max(0,held_age-notice_lag),
        reader_stall=waiting_readers*held_age,
        shelf_pressure=waiting_readers/max(1,96-held_age),
        notice_delay_share=min(1,notice_lag/held_age),
    )


def propose_release_review(values, missing=()):
    notice_lag, walk_mins, weekday, renewals, waiting_readers, held_age = values
    if 'held_age' not in missing and (held_age<=57):
        yield Proposal('按回执更新留架年龄', 'held_age', held_age, min(65,held_age+8), 0)
    if 'notice_lag' not in missing and (notice_lag>=5):
        yield Proposal('二次通知后时窗对照', 'notice_lag', notice_lag, max(0,notice_lag-5), 1)
    if 'renewals' not in missing and (renewals>=1):
        yield Proposal('延期申请已撤回', 'renewals', renewals, max(0,renewals-1), 1)
    if 'waiting_readers' not in missing and (waiting_readers>=3):
        yield Proposal('核对下游预约变动', 'waiting_readers', waiting_readers, max(0,waiting_readers-3), 0)
