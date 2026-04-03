from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import calendar


class RecurrenceEngine:
    def generate_due_datetimes(
        self,
        recurrence_type: str,
        recurrence_rule: dict,
        due_time: time,
        timezone: str,
        start_date: date,
        horizon_days: int,
    ) -> list[datetime]:
        tz = ZoneInfo(timezone)
        horizon_end = start_date + timedelta(days=horizon_days)
        current = start_date
        out: list[datetime] = []

        while current <= horizon_end:
            if self._matches(current, recurrence_type, recurrence_rule, start_date):
                local_dt = datetime.combine(current, due_time, tzinfo=tz)
                out.append(local_dt.astimezone(ZoneInfo("UTC")))
            current += timedelta(days=1)
        return out

    def _matches(self, d: date, recurrence_type: str, rule: dict, anchor: date) -> bool:
        if recurrence_type == "daily":
            return True
        if recurrence_type == "weekly":
            weekdays = set(rule.get("weekdays", [anchor.weekday()]))
            interval = int(rule.get("interval", 1))
            weeks = (d - anchor).days // 7
            return d.weekday() in weekdays and weeks % interval == 0
        if recurrence_type in {"monthly", "quarterly"}:
            month_diff = (d.year - anchor.year) * 12 + (d.month - anchor.month)
            interval = 3 if recurrence_type == "quarterly" else int(rule.get("interval", 1))
            if month_diff < 0 or month_diff % interval != 0:
                return False
            day = int(rule.get("day_of_month", anchor.day))
            last_day = calendar.monthrange(d.year, d.month)[1]
            return d.day == min(day, last_day)
        if recurrence_type == "yearly":
            interval = int(rule.get("interval", 1))
            years = d.year - anchor.year
            return years >= 0 and years % interval == 0 and d.month == anchor.month and d.day == anchor.day
        if recurrence_type == "custom":
            every_n_days = int(rule.get("every_n_days", 1))
            return (d - anchor).days % every_n_days == 0
        return False
