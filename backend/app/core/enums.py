import enum


class PreferenceLevel(enum.StrEnum):
    FIRST = "Eager to teach"
    SECOND = "Ready to teach"
    THIRD = "Willing to teach"
    NO = "Not my cup of tea"

    def to_int(self) -> int:
        mapping = {
            PreferenceLevel.FIRST: 1,
            PreferenceLevel.SECOND: 2,
            PreferenceLevel.THIRD: 3,
            PreferenceLevel.NO: 4,
        }

        return mapping[self]


class Semester(enum.Enum):
    FALL = "Fall"
    SPRING = "Spring"
    SUMMER_1 = "Summer 1"
    SUMMER_2 = "Summer 2"


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
