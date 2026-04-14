from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones

CHALLENGE_DAY_PIVOT_HOUR = 14


def local_now(tz_name: str) -> datetime:
    return datetime.now(ZoneInfo(tz_name))


def challenge_day_for(dt_local: datetime) -> date:
    """The challenge-day attributed to a moment in local time.

    A challenge-day runs 14:00 (prev calendar day) → 14:00 (this calendar day).
    That way the evening bed log and the morning wake log share a challenge-day.
    """
    if dt_local.hour < CHALLENGE_DAY_PIVOT_HOUR:
        return dt_local.date()
    return dt_local.date() + timedelta(days=1)


def deadline_passed(now_local: datetime, deadline: time) -> bool:
    return now_local.time() > deadline


def in_bed_window(now_local: datetime) -> bool:
    h = now_local.hour
    return h >= 20 or h < 4


def in_wake_window(now_local: datetime) -> bool:
    h = now_local.hour
    return 4 <= h < CHALLENGE_DAY_PIVOT_HOUR


def bed_on_time(now_local: datetime, deadline: time) -> bool:
    return not deadline_passed(now_local, deadline)


def wake_on_time(now_local: datetime, deadline: time) -> bool:
    return not deadline_passed(now_local, deadline)


def is_valid_tz(name: str) -> bool:
    return name in available_timezones()


def infer_tz_from_offset(local_now_str: str) -> str | None:
    """Given the user's reported local time as 'HH:MM', return a plausible Olson name.

    Strategy: compute the offset vs current UTC, then pick a common zone with that offset.
    """
    try:
        hh, mm = (int(x) for x in local_now_str.strip().split(":"))
    except ValueError:
        return None
    if not (0 <= hh < 24 and 0 <= mm < 60):
        return None

    utc_now = datetime.now(timezone.utc)
    reported_minutes = hh * 60 + mm
    utc_minutes = utc_now.hour * 60 + utc_now.minute
    diff = reported_minutes - utc_minutes
    if diff > 12 * 60:
        diff -= 24 * 60
    elif diff < -12 * 60:
        diff += 24 * 60

    return _offset_to_common_zone(diff)


_COMMON_ZONE_BY_OFFSET_MIN: dict[int, str] = {
    -480: "America/Los_Angeles",
    -420: "America/Denver",
    -360: "America/Chicago",
    -300: "America/New_York",
    -240: "America/Halifax",
    -180: "America/Sao_Paulo",
    0: "UTC",
    60: "Europe/London",
    120: "Europe/Zurich",
    180: "Europe/Moscow",
    210: "Asia/Tehran",
    240: "Asia/Dubai",
    270: "Asia/Kabul",
    300: "Asia/Karachi",
    330: "Asia/Kolkata",
    360: "Asia/Dhaka",
    420: "Asia/Bangkok",
    480: "Asia/Shanghai",
    540: "Asia/Tokyo",
    570: "Australia/Adelaide",
    600: "Australia/Sydney",
    720: "Pacific/Auckland",
}


def _offset_to_common_zone(offset_min: int) -> str | None:
    if offset_min in _COMMON_ZONE_BY_OFFSET_MIN:
        return _COMMON_ZONE_BY_OFFSET_MIN[offset_min]
    nearest = min(_COMMON_ZONE_BY_OFFSET_MIN, key=lambda k: abs(k - offset_min))
    if abs(nearest - offset_min) <= 60:
        return _COMMON_ZONE_BY_OFFSET_MIN[nearest]
    return None


def tz_from_geo(lat: float, lon: float) -> str | None:
    try:
        from timezonefinder import TimezoneFinder
    except ImportError:
        return None
    tf = TimezoneFinder()
    return tf.timezone_at(lat=lat, lng=lon)
