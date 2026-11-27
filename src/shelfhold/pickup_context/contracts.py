from dataclasses import dataclass
from math import isfinite
from ..hold_slips.contracts import ShelfholdRecord as RawObservation

RAW_KEYS = ('notice_lag', 'walk_mins', 'weekday', 'renewals', 'waiting_readers', 'held_age')
FEATURE_KEYS = ('trip_friction', 'weekend_span', 'renewal_load', 'queue_days', 'contact_recency')
FEATURE_NAMES = ('到馆时间成本', '周末标记', '当前延期负担', '预约等待小时积', '通知后已过去')


@dataclass(frozen=True, slots=True)
class FeatureState:
    fill: tuple[float, ...]
    offsets: tuple[float, ...]
    scales: tuple[float, ...]
    floor: tuple[float, ...]
    ceil: tuple[float, ...]
    fingerprint: str

    def __post_init__(self):
        if len(self.fill) != len(RAW_KEYS):
            raise ValueError('补值向量维数与字段表不匹配')
        if any(len(column) != len(FEATURE_KEYS) for column in (self.offsets, self.scales, self.floor, self.ceil)):
            raise ValueError('特征状态维数不匹配')
        if min(self.scales) <= 0:
            raise ValueError('特征尺度必须为正')


@dataclass(frozen=True, slots=True)
class FeatureVector:
    key: str
    cohort: str
    day: int
    values: tuple[float, ...]
    factors: tuple[float, ...]
    missing: tuple[str, ...]
    excursions: tuple[str, ...]
    outcome: float | None
    observed: bool
    input_values: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class PreparedRuns:
    train: tuple[FeatureVector, ...]
    calibration: tuple[FeatureVector, ...]
    replay: tuple[FeatureVector, ...]
    live: tuple[FeatureVector, ...]

    def segments(self):
        return tuple((name, getattr(self, name)) for name in ('train', 'calibration', 'replay', 'live'))


@dataclass(frozen=True, slots=True)
class Proposal:
    name: str
    field: str
    before: float
    after: float
    work: int

    def __post_init__(self):
        if self.before == self.after or not isfinite(self.after) or self.work < 0:
            raise ValueError('推演动作需要实质变动和有效额度')

    def evidence(self):
        return {'情形': self.name, '变更项': self.field, '原值': self.before,
                '置换值': self.after, '用量': self.work}

@dataclass(frozen=True, slots=True)
class PickupContext:
    contactable: float
    queue_per_trip: float
    carry_hours: float
    renewal_credit: float
    weekend_notice: float
    reader_stall: float
    shelf_pressure: float
    notice_delay_share: float

    def __post_init__(self):
        if not all(isfinite(amount) for amount in (self.contactable, self.queue_per_trip, self.carry_hours, self.renewal_credit, self.weekend_notice, self.reader_stall, self.shelf_pressure, self.notice_delay_share)):
            raise ValueError('预约单存在无效的作业量测')

    def explain(self, labels=None):
        return (
            ('通知后可到馆时长', round(self.contactable, 4)),
            ('预约排队成本', round(self.queue_per_trip, 4)),
            ('最长保留预算', round(self.carry_hours, 4)),
            ('延期合计预留时间', round(self.renewal_credit, 4)),
            ('周末已联系小时', round(self.weekend_notice, 4)),
            ('后续读者等待小时积', round(self.reader_stall, 4)),
            ('每个可用小时待取户', round(self.shelf_pressure, 4)),
            ('延迟占已留架比', round(self.notice_delay_share, 4)),
        )
