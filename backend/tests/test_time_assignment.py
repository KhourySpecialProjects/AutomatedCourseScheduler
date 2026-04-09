from types import SimpleNamespace

from app.algorithms.models import MatchedAssignment
from app.algorithms.time_assignment import (
    assign_time_blocks,
    department_code_from_course_name,
    max_sections_per_block_for_department,
)
from app.core.enums import Severity, WarningType
from app.schemas.algorithm_params import AlgorithmParameters
from app.schemas.section import MeetingPreferenceInfo


def _block(tid: int, days: str) -> SimpleNamespace:
    return SimpleNamespace(time_block_id=tid, meeting_days=days)


def _prefs(*pairs: tuple[int, str]) -> list[MeetingPreferenceInfo]:
    return [MeetingPreferenceInfo(time_block_id=tb, preference=pref) for tb, pref in pairs]


def test_department_code_from_course_name():
    assert department_code_from_course_name("CS 2500") == "CS"
    assert department_code_from_course_name("DS 4400") == "DS"


def test_prefers_better_time_preference():
    blocks = [_block(1, "MW"), _block(2, "TR")]
    faculty_prefs = {10: _prefs((1, "Willing to teach"), (2, "Eager to teach"))}
    assignments = [
        MatchedAssignment(section_id=1, course_id=100, faculty_nuid=10, department_code="CS")
    ]
    result = assign_time_blocks(assignments, blocks, faculty_prefs)
    placed = result.assignments[0]
    assert placed.time_block_id == 2
    assert placed.time_preference_level == 1


def test_faculty_cannot_double_book_same_time_block():
    blocks = [_block(1, "MW"), _block(2, "TR")]
    faculty_prefs = {10: _prefs((1, "Eager to teach"), (2, "Eager to teach"))}
    assignments = [
        MatchedAssignment(1, 100, 10, "CS"),
        MatchedAssignment(2, 101, 10, "CS"),
    ]
    result = assign_time_blocks(assignments, blocks, faculty_prefs)
    ids = {a.section_id: a.time_block_id for a in result.assignments}
    assert ids[1] != ids[2]
    assert set(ids.values()) == {1, 2}


def test_fifteen_percent_cap_per_department():
    blocks = [_block(1, "MW"), _block(2, "TR"), _block(3, "WF")]
    faculty_prefs = {
        i: _prefs(
            (1, "Eager to teach"),
            (2, "Eager to teach"),
            (3, "Eager to teach"),
        )
        for i in range(10)
    }
    assignments = [
        MatchedAssignment(section_id=i, course_id=200 + i, faculty_nuid=i, department_code="CS")
        for i in range(10)
    ]
    params = AlgorithmParameters(MaxTimeBlockCapacity=0.15)
    result = assign_time_blocks(assignments, blocks, faculty_prefs, parameters=params)
    assert all(w.Type == WarningType.NO_VALID_TIME_BLOCK for w in result.warnings)
    placed = [a for a in result.assignments if a.time_block_id is not None]
    assert len(placed) == 3
    assert len([a for a in result.assignments if a.time_block_id is None]) == 7


def test_tiebreak_prefers_clustering_on_existing_days():
    blocks = [_block(1, "MW"), _block(2, "MWF")]
    faculty_prefs = {10: _prefs((1, "Ready to teach"), (2, "Ready to teach"))}
    assignments = [
        MatchedAssignment(1, 100, 10, "CS"),
        MatchedAssignment(2, 101, 10, "CS"),
    ]
    result = assign_time_blocks(assignments, blocks, faculty_prefs)
    by_sec = {a.section_id: a.time_block_id for a in result.assignments}
    assert by_sec[1] == 1
    assert by_sec[2] == 2


def test_unrated_time_blocks_rank_after_rated():
    blocks = [_block(1, "MW"), _block(2, "TR")]
    faculty_prefs = {10: _prefs((1, "Willing to teach"))}
    assignments = [MatchedAssignment(1, 100, 10, "CS")]
    result = assign_time_blocks(assignments, blocks, faculty_prefs)
    assert result.assignments[0].time_block_id == 1
    assert result.assignments[0].time_preference_level == 3


def test_existing_faculty_time_blocks_respected():
    blocks = [_block(1, "MW"), _block(2, "TR")]
    faculty_prefs = {10: _prefs((1, "Eager to teach"), (2, "Eager to teach"))}
    assignments = [MatchedAssignment(1, 100, 10, "CS")]
    result = assign_time_blocks(
        assignments,
        blocks,
        faculty_prefs,
        existing_faculty_time_blocks={10: {1}},
    )
    assert result.assignments[0].time_block_id == 2


def test_department_section_totals_tighten_cap():
    blocks = [_block(1, "MW"), _block(2, "TR")]
    eager = _prefs((1, "Eager to teach"), (2, "Eager to teach"))
    assignments = [
        MatchedAssignment(1, 100, 10, "CS"),
        MatchedAssignment(2, 101, 11, "CS"),
    ]
    params = AlgorithmParameters(MaxTimeBlockCapacity=0.15)
    result = assign_time_blocks(
        assignments,
        blocks,
        {10: eager, 11: eager},
        parameters=params,
        department_section_totals={"CS": 10},
    )
    by_tb: dict[int, int] = {}
    for a in result.assignments:
        if a.time_block_id is not None:
            by_tb[a.time_block_id] = by_tb.get(a.time_block_id, 0) + 1
    assert max(by_tb.values(), default=0) <= 1


def test_max_sections_per_block_helper():
    assert (
        max_sections_per_block_for_department(10, AlgorithmParameters(MaxTimeBlockCapacity=0.15))
        == 1
    )
    assert (
        max_sections_per_block_for_department(20, AlgorithmParameters(MaxTimeBlockCapacity=0.15))
        == 3
    )
    assert (
        max_sections_per_block_for_department(1, AlgorithmParameters(MaxTimeBlockCapacity=0.15))
        == 1
    )


def test_warning_severity_and_metadata():
    blocks = [_block(1, "MW")]
    assignments = [
        MatchedAssignment(1, 100, 10, "CS"),
        MatchedAssignment(2, 101, 11, "CS"),
    ]
    result = assign_time_blocks(
        assignments,
        blocks,
        {10: _prefs((1, "Eager to teach")), 11: _prefs((1, "Eager to teach"))},
        department_section_totals={"CS": 10},
        parameters=AlgorithmParameters(MaxTimeBlockCapacity=0.15),
    )
    assert len(result.warnings) == 1
    w = result.warnings[0]
    assert w.Type == WarningType.NO_VALID_TIME_BLOCK
    assert w.SeverityRank == Severity.MEDIUM
    assert w.FacultyID in (10, 11)
    assert w.CourseID in (100, 101)
