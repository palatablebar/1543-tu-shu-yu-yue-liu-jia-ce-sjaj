from shelfhold.pipeline import preview
from shelfhold.release_review.service import operating_ledger


def note(key, measures, *, zone='甲区', state='已分派', estimate=0, hits=(), missing=()):
    return {'key':key,'zone':zone,'state':state,'estimate':estimate,'hits':hits,
            'unmeasured':missing,'measurements':dict(zip(('notice_lag', 'walk_mins', 'weekday', 'renewals', 'waiting_readers', 'held_age'),measures,strict=True))}


def test_field_plan_is_visible_and_references_real_tickets():
    desk = preview()
    plan = desk['sections'][6]
    assert plan['operating_title'] == '留架回访安排'
    assert plan['operating_rows']
    scoped = {item['关联单据'] for item in plan['operating_rows'] if '关联单据' in item}
    assert scoped and scoped <= {row['key'] for row in desk['rows']}
    assert all(item['业务安排'] for item in plan['operating_rows'])


def test_closed_monday_moves_followup_to_tuesday_open():
    monday = note('RS-1',(8,23,0,1,15,58),estimate=7)
    records = operating_ledger([monday])
    receipt = records[0]
    assert receipt['下次回访间隔小时']==22
    assert receipt['开放复核间隔小时']>=28
    assert receipt['经馆员核对']
