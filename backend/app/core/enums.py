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
    TIME_BLOCK_OVERLOAD = "Time block surpasses threshold"
    UNPREFERENCED_COURSE = "Faculty assigned unpreferenced course"
    UNPREFERENCED_TIME = "Faculty assigned unpreferenced time"
    CONFLICT_GROUP_VIOLATION = "Conflict group courses overlap"
    FACULTY_OVERLOAD = "Faculty overloaded with assignments"
    INSUFFICIENT_FACULTY_SUPPLY = "Insufficient faculty supply for section"


class Campus(enum.StrEnum):
    BOSTON = "Boston"
    OAKLAND = "Oakland"
    LONDON = "London"
