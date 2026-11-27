from hashlib import sha256
from math import isfinite
from statistics import median

from .contracts import MODEL_NAME, Fit, Prediction
from .baseline import baseline_review
from .diagnostics import explain_shelf_survival
from .survival_model import fit_kernel, score_kernel


def fit_model(history, feature_stamp):
    periods = tuple(sorted(history,key=lambda holding:(holding.day,holding.key)))
    if len(periods)<8 or not feature_stamp:
        raise ValueError('记录不足以估计预约留架时间')
    if len({row.key for row in periods}) != len(periods):
        raise ValueError('预约模型不可重复加入同一张留架单')
    seen_events = []
    right_censored = []
    for ledger in periods:
        age = ledger.input_values[5]
        if ledger.outcome is None or not isfinite(ledger.outcome) or not all(map(isfinite,ledger.values)):
            raise ValueError('借阅留架时长与向量必须有限')
        if ledger.outcome <= age:
            raise ValueError('留架事件时标必须晚于观察时点')
        target = seen_events if ledger.observed else right_censored
        target.append(ledger.outcome-age)
    survival, evidence = fit_kernel(periods)
    stamp = tuple((row.key,row.cohort,row.values,row.input_values[5],row.outcome,row.observed) for row in periods)
    signed = sha256(repr((feature_stamp,MODEL_NAME,stamp)).encode()).hexdigest()[:16]
    windows = (('右截尾样本',len(right_censored)),('已取件样本',len(seen_events)))
    if seen_events:
        windows += (('取件剩余小时中位',median(seen_events)),)
    return Fit(MODEL_NAME,feature_stamp,signed,survival,(*evidence,*windows))


def predict_one(fit, observation):
    hours, impacts = score_kernel(fit.parameters,observation)
    if not isfinite(hours) or hours<0 or not all(map(isfinite,impacts)):
        raise ArithmeticError('留架时长估计无法核验')
    elapsed = observation.input_values[5]
    remaining = None if observation.outcome is None else max(0.,observation.outcome-elapsed)
    return Prediction(observation.key,observation.cohort,observation.day,hours,tuple(impacts),observation.missing,
                      observation.excursions,remaining,observation.observed,observation.input_values)


def predict(fit, observations, feature_stamp):
    if fit.feature!=feature_stamp:
        raise ValueError('预约册必须使用同一版次的留架特征版本')
    return tuple(predict_one(fit,holding) for holding in observations)


def compare_batches(fit, groups, feature_stamp):
    separate = tuple(prediction for group in groups for prediction in predict(fit, group, feature_stamp))
    return separate == predict(fit, (row for group in groups for row in group), feature_stamp)


def inspection_rows(fit, sections):
    """Return model-specific evidence for the current run without retraining."""
    return (explain_shelf_survival(fit, sections.calibration, sections.replay, sections.live)
            + baseline_review(fit, sections.train, sections.replay))
