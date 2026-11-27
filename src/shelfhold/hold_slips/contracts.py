from dataclasses import dataclass

FIELDS = {'notice_lag': ('通知送达延迟', 'h', 0, 20),
 'walk_mins': ('取件步行估计', 'min', 3, 55),
 'weekday': ('通知星期', '日', 0, 6),
 'renewals': ('延期申请', '次', 0, 4),
 'waiting_readers': ('后续预约户', '户', 0, 32),
 'held_age': ('已留架时间', 'h', 10, 65)}
LIMITS = {'result_max': 96}


class MeasureIssue(ValueError):
    def __init__(self, field: str, code: str):
        super().__init__(f'{field}:{code}')
        self.field = field
        self.code = code


@dataclass(frozen=True, slots=True)
class ShelfholdRecord:
    key: str
    cohort: str
    day: int
    received: int
    revision: int
    result_day: int | None
    outcome: float | None
    observed: bool
    notice_lag: float | None
    walk_mins: float | None
    weekday: float | None
    renewals: float | None
    waiting_readers: float | None
    held_age: float | None

    def signature(self):
        return (self.key, self.cohort, self.day, self.revision, self.result_day, self.outcome, self.observed,
                *(getattr(self, key) for key in FIELDS))


@dataclass(frozen=True, slots=True)
class Issue:
    source_row: int
    key: str
    field: str
    code: str

    def evidence(self):
        return {'行号': self.source_row, '单号': self.key, '字段': FIELDS.get(self.field, (self.field,))[0],
                '原因': self.code}


@dataclass(frozen=True, slots=True)
class DecodeResult:
    entries: tuple[ShelfholdRecord, ...]
    issues: tuple[Issue, ...]
    source_rows: int
