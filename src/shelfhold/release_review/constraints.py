from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Callable

from .contracts import Job


@dataclass(frozen=True, slots=True)
class WorkOrder:
    job: Job
    assessment: Any

    def __post_init__(self):
        if self.job.key != self.assessment.raw.key:
            raise ValueError('处置工位与单据不匹配')


def apply_release_review(appointments, admit: Callable, wait: Callable):
    held_shelves = set()
    for appointment in appointments:
        lag, walk, weekday, renewals, readers, age = appointment.assessment.raw.input_values
        shelf_key = appointment.job.cohort, int(weekday), int(age//24)
        if lag >= age and readers < 5:
            wait(appointment, 'CONTACT_WINDOW_NOT_OPEN', '回执未确认，先保留架位')
            continue
        if readers == 0 and shelf_key in held_shelves:
            wait(appointment, 'KEEP_READER_PRIORITY', '同架有后续预约优先核对')
            continue
        if admit(appointment) and renewals == 0:
            held_shelves.add(shelf_key)
