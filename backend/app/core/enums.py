import enum


class PreferenceLevel(enum.StrEnum):
    EAGER = "Eager to teach"
    READY = "Ready to teach"
    WILLING = "Willing to teach"
    NOT_INTERESTED = "Not my cup of tea"

    def to_int(self) -> int:
        mapping = {
            PreferenceLevel.EAGER: 1,
            PreferenceLevel.READY: 2,
            PreferenceLevel.WILLING: 3,
            PreferenceLevel.NOT_INTERESTED: 4,
        }

        return mapping[self]


class Severity(int, enum.Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class WarningType(enum.StrEnum):
    """Each member carries a human-readable message and a default severity.

    Usage:
        WarningType.FACULTY_OVERLOAD.value    # → "Faculty overloaded with assignments"
        WarningType.FACULTY_OVERLOAD.severity # → Severity.HIGH
    """

    def __new__(cls, message: str, severity: "Severity"):
        obj = str.__new__(cls, message)
        obj._value_ = message
        obj.severity = severity
        return obj

    TIME_BLOCK_OVERLOAD = ("Time block surpasses threshold", Severity.MEDIUM)
    NO_VALID_TIME_BLOCK = ("No valid time block for section-faculty pair", Severity.HIGH)
    UNPREFERENCED_COURSE = ("Faculty assigned unpreferenced course", Severity.LOW)
    UNPREFERENCED_TIME = ("Faculty assigned unpreferenced time", Severity.LOW)
    CONFLICT_GROUP_VIOLATION = ("Conflict group courses overlap", Severity.HIGH)
    FACULTY_OVERLOAD = ("Faculty overloaded with assignments", Severity.HIGH)
    INSUFFICIENT_FACULTY_SUPPLY = ("Insufficient faculty supply for section", Severity.HIGH)
    FACULTY_DOUBLE_BOOKED = ("Faculty double booked in time block", Severity.HIGH)


class Campus(enum.StrEnum):
    BOSTON = "Boston"
    OAKLAND = "Oakland"
    LONDON = "London"


class ScheduleStatus(enum.StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    GENERATED = "generated"
    FAILED = "failed"
    FINALIZED = "finalized"
