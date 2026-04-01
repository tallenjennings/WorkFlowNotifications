from datetime import date, time

from app.services.recurrence import RecurrenceEngine


def test_monthly_day_of_month_generation():
    engine = RecurrenceEngine()
    out = engine.generate_due_datetimes(
        recurrence_type="monthly",
        recurrence_rule={"day_of_month": 15},
        due_time=time(9, 0),
        timezone="UTC",
        start_date=date(2026, 1, 1),
        horizon_days=90,
    )
    assert len(out) >= 3
    assert out[0].day == 15
