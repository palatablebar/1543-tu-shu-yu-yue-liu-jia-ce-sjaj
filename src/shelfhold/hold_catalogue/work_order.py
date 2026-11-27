def collect_notice_watch(measures, missing, estimate):
    notice_lag = measures['notice_lag']
    held_age = measures['held_age']
    if not (notice_lag>=10):
        return None
    value=held_age-notice_lag
    return {'现场复核':'短信回执','可复查值':round(value,3),'单位':'小时','归档要求':'核对通知是否送达可用手机号',
            '需补测':not set(missing).isdisjoint(('notice_lag', 'held_age'))}


def collect_extension_appointment(measures, missing, estimate):
    renewals = measures['renewals']
    if not (renewals>=2):
        return None
    value=renewals*8
    return {'现场复核':'延期核查','可复查值':round(value,3),'单位':'小时','归档要求':'检查延期记录并与借阅者核对',
            '需补测':not set(missing).isdisjoint(('renewals',))}


def collect_reader_queue(measures, missing, estimate):
    waiting_readers = measures['waiting_readers']
    if not (waiting_readers>=10):
        return None
    value=waiting_readers
    return {'现场复核':'队列登记','可复查值':round(value,3),'单位':'户','归档要求':'登记需要补发通知的读者数',
            '需补测':not set(missing).isdisjoint(('waiting_readers',))}


def collect_shelf_budget(measures, missing, estimate):
    held_age = measures['held_age']
    if not (held_age>=46):
        return None
    value=96-held_age
    return {'现场复核':'副馆闭架','可复查值':round(value,3),'单位':'小时','归档要求':'比对剩余保留时间与营业档',
            '需补测':not set(missing).isdisjoint(('held_age',))}


def check_hold_catalogue(records):
    guide = []
    for ticket in records:
        if ticket['state'] not in ('已分派','暂停','人工判读'):
            continue
        measures=ticket['measurements']
        absent=ticket['unmeasured']
        estimate=ticket['estimate']
        checks = (
            collect_notice_watch(measures,absent,estimate),
            collect_extension_appointment(measures,absent,estimate),
            collect_reader_queue(measures,absent,estimate),
            collect_shelf_budget(measures,absent,estimate),
        )
        required=tuple(check for check in checks if check is not None)
        if not required:
            continue
        review=ticket['key']
        for check in required:
            guide.append({'签收单':review,'作业区':ticket['zone'],'处置':ticket['state'],**check})
    return guide
