from math import exp, log, fsum, sqrt
from statistics import median, mean, quantiles

from .survival_model import score_kernel
from .survival_model import restricted_tail


def explain_shelf_survival(fit, calibration, replay, live):
    total, segments = fit.parameters
    lines = []
    display_curves = [('全馆',total),*((('周末' if group else '工作日'),curve) for group,curve in segments)]
    for label, curve in display_curves:
        count = sum(observed for _,_,_,observed,_ in curve)
        unobserved = sum(censored for _,_,_,_,censored in curve)
        for age in (24,36,48,60,72):
            at_risk = next((n for time,_,n,_,_ in curve if time>=age),0)
            surviving = next((s for time,s,_,_,_ in reversed(curve) if time<=age),1.)
            lines.append({'预约段':label,'留架时数':age,'已取件':count,'右截尾':unobserved,'后续可比单':at_risk,
                          '尚未取件比例':round(surviving,4),'后续保留积分':round(restricted_tail(curve,age),2)})
    return lines
