import enum


class PreferenceLevel(enum.Enum):
    """Represents a faculty member's level of preference."""

    EAGER = "Eager to teach"
    WILLING = "Willing to teach"
    NOT_INTERESTED = "Not my cup of tea"


class Semester(enum.Enum):
    FALL = "Fall"
    SPRING = "Spring"
    SUMMER_1 = "Summer 1"
    SUMMER_2 = "Summer 2"
