from collections.abc import Mapping
from decimal import Decimal

from .contracts import MeasureIssue


from dataclasses import dataclass


def form_number(form, sheet, name, minimum, maximum):
    from .service import number

    table = form.get(sheet)
    if not isinstance(table, Mapping):
        raise MeasureIssue(sheet, 'FORM_SECTION_REQUIRED')
    return Decimal(str(number(table.get(name), name, minimum, maximum)))


@dataclass(frozen=True, slots=True)
class HoldSlipsSheet:
    message_lag_minutes: Decimal
    walk_seconds: Decimal
    iso_weekday: Decimal
    extension_tallies: Decimal
    pending_accounts: Decimal
    shelf_age_minutes: Decimal

    def fields(self):
        return {
            'notice_lag': float(self.message_lag_minutes) / 60,
            'walk_mins': float(self.walk_seconds) / 60,
            'weekday': float(self.iso_weekday) - 1,
            'renewals': float(self.extension_tallies),
            'waiting_readers': float(self.pending_accounts),
            'held_age': float(self.shelf_age_minutes) / 60,
        }

    def validation(self):
        fields = self.fields()
        notice_lag = fields['notice_lag']
        walk_mins = fields['walk_mins']
        weekday = fields['weekday']
        renewals = fields['renewals']
        waiting_readers = fields['waiting_readers']
        held_age = fields['held_age']
        read_window = held_age-notice_lag
        approach_time = walk_mins/60
        promise = renewals*8+held_age
        transfer_cost = waiting_readers*(approach_time+1)
        alerts = []
        if read_window < 0:
            alerts.append(('message_lag_minutes', 'NOTICE_AFTER_SHELF_AGE'))
        if promise>94 and waiting_readers>10:
            alerts.append(('extension_tallies', 'EXTENSION_NEEDS_REVIEW'))
        if transfer_cost>=54:
            alerts.append(('pending_accounts', 'CHECK_LINKED_READERS'))
        return tuple(alerts)


def read_hold_slips(form):
    return HoldSlipsSheet(
        message_lag_minutes=form_number(form, '短信回执', 'message_lag_minutes', 0, 1200),
        walk_seconds=form_number(form, '短信回执', 'walk_seconds', 180, 3300),
        iso_weekday=form_number(form, '读者预约', 'iso_weekday', 1, 7),
        extension_tallies=form_number(form, '读者预约', 'extension_tallies', 0, 4),
        pending_accounts=form_number(form, '留架巡查', 'pending_accounts', 0, 32),
        shelf_age_minutes=form_number(form, '留架巡查', 'shelf_age_minutes', 600, 3900),
    )


def explicit_rows(form):
    if not isinstance(form, Mapping):
        raise MeasureIssue('form', 'FORM_OBJECT_REQUIRED')
    note = read_hold_slips(form)
    return note.fields(), note.validation()


def check_native_history(source):
    if not isinstance(source, Mapping) or 'form' not in source:
        return source
    if any(key in source for key in ('notice_lag', 'walk_mins', 'weekday', 'renewals', 'waiting_readers', 'held_age')):
        raise MeasureIssue('form','MIXED_FORM_AND_FLAT_READING')
    converted, flags = explicit_rows(source['form'])
    if flags:
        raise MeasureIssue(*flags[0])
    return {**source, **converted}
