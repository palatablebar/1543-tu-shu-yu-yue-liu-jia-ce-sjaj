from collections import defaultdict
from math import fabs, fsum
from statistics import mean, median

from .survival_model import score_kernel


def complete_pickups(archive):
    sections = defaultdict(list)
    for note in archive:
        if note.observed:
            sections[int(note.input_values[2]>=4)].append(note.outcome)
    known = [hour for shifts in sections.values() for hour in shifts]
    return {lane:median(hours) for lane,hours in sections.items()}, median(known) if known else 96.


def legacy_hold(reference,note):
    lookup, pooled = reference
    total = lookup.get(int(note.input_values[2]>=4),pooled)
    return max(0,total-note.input_values[5])


def baseline_review(fit, training, replay):
    convention = complete_pickups(training)
    production = defaultdict(list)
    for sample in replay:
        if not sample.observed or sample.outcome is None:
            continue
        estimate, _ = score_kernel(fit.parameters,sample)
        baseline = legacy_hold(convention, sample)
        actual = max(0.,sample.outcome - sample.input_values[5])
        loss, prior = abs(actual-estimate),abs(actual-baseline)
        production[sample.cohort].append((loss,prior,estimate-actual,baseline-actual))
    reports = []
    for sector, comparison in sorted(production.items()):
        model_loss, base_loss, error, original = zip(*comparison,strict=True)
        paired = tuple(old-new for old,new in zip(base_loss,model_loss,strict=True))
        n = len(comparison)
        reports.append({'回放组':sector,'实绩数':n,'基线':'仅按成熟取件时数估计','估计代价':round(mean(model_loss),4),
                        '业务基线代价':round(mean(base_loss),4),'模型偏误中位':round(median(error),4),
                        '参照偏误中位':round(median(original),4),'同单误差减少中位':round(median(paired),4),
                        '改善单数':sum(delta>0 for delta in paired),'恶化单数':sum(delta<0 for delta in paired)})
    return reports
