"""Seed the database with realistic course scheduling data.

Usage:
    From the backend/ directory:
        python seed.py

    Or with a custom DATABASE_URL:
        DATABASE_URL=postgresql://... python seed.py
"""

import os
import sys

# Allow running from the backend/ directory without installing the package.
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime

from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.enums import PreferenceLevel, Semester
from app.models.course import Course
from app.models.course_preference import CoursePreference
from app.models.faculty import Faculty
from app.models.faculty_assignment import FacultyAssignment
from app.models.meeting_preference import MeetingPreference
from app.models.schedule import Schedule
from app.models.schedule_log import ScheduleLog
from app.models.section import Section
from app.models.time_block import TimeBlock


def seed(db: Session) -> None:
    # ------------------------------------------------------------------
    # Guard: skip if data already exists
    # ------------------------------------------------------------------
    if db.query(Schedule).count() > 0:
        print("Database already contains data — skipping seed.")
        return

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------
    courses = [
        Course(
            name="Fundamentals of CS 1",
            description="Introduction to programming using Python.",
            credits=4,
        ),
        Course(
            name="Fundamentals of CS 2",
            description="Object-oriented programming and data structures.",
            credits=4,
        ),
        Course(
            name="Object-Oriented Design",
            description="Design patterns and OO principles.",
            credits=4,
        ),
        Course(
            name="Algorithms and Data",
            description="Core algorithms, complexity, and data structures.",
            credits=4,
        ),
        Course(
            name="Computer Systems",
            description="Memory, OS concepts, and systems programming in C.",
            credits=4,
        ),
        Course(
            name="Software Development",
            description="Agile practices, version control, and team projects.",
            credits=4,
        ),
        Course(
            name="Theory of Computation",
            description="Automata, formal languages, and computability.",
            credits=4,
        ),
        Course(
            name="Foundations of AI",
            description="Search, knowledge representation, and machine learning.",
            credits=4,
        ),
        Course(
            name="Database Design",
            description="Relational databases, SQL, and normalization.",
            credits=4,
        ),
        Course(
            name="Networks and Distributed Systems",
            description="Protocols, sockets, and distributed computing.",
            credits=4,
        ),
        Course(
            name="Programming Languages",
            description="Language paradigms, type systems, and interpreters.",
            credits=4,
        ),
        Course(
            name="Capstone Project",
            description="Year-long software engineering capstone.",
            credits=4,
        ),
    ]
    db.add_all(courses)
    db.flush()  # populate PKs

    # ------------------------------------------------------------------
    # Faculty
    # ------------------------------------------------------------------
    faculty_list = [
        Faculty(
            nuid=100001,
            first_name="Alice",
            last_name="Chen",
            email="a.chen@univ.edu",
            phone_number="617-555-0101",
            title="Associate Professor",
            campus="Boston",
            active=True,
        ),
        Faculty(
            nuid=100002,
            first_name="Bob",
            last_name="Martinez",
            email="b.martinez@univ.edu",
            phone_number="617-555-0102",
            title="Professor",
            campus="Boston",
            active=True,
        ),
        Faculty(
            nuid=100003,
            first_name="Carol",
            last_name="Okafor",
            email="c.okafor@univ.edu",
            phone_number="617-555-0103",
            title="Assistant Professor",
            campus="Boston",
            active=True,
        ),
        Faculty(
            nuid=100004,
            first_name="David",
            last_name="Kim",
            email="d.kim@univ.edu",
            phone_number="617-555-0104",
            title="Associate Professor",
            campus="Boston",
            active=True,
        ),
        Faculty(
            nuid=100005,
            first_name="Eve",
            last_name="Patel",
            email="e.patel@univ.edu",
            phone_number="617-555-0105",
            title="Lecturer",
            campus="Boston",
            active=True,
        ),
        Faculty(
            nuid=100006,
            first_name="Frank",
            last_name="Torres",
            email="f.torres@univ.edu",
            phone_number="617-555-0106",
            title="Professor",
            campus="Boston",
            active=True,
        ),
        Faculty(
            nuid=100007,
            first_name="Grace",
            last_name="Liu",
            email="g.liu@univ.edu",
            phone_number="617-555-0107",
            title="Assistant Professor",
            campus="Boston",
            active=True,
        ),
        Faculty(
            nuid=100008,
            first_name="Henry",
            last_name="Nguyen",
            email="h.nguyen@univ.edu",
            phone_number="617-555-0108",
            title="Lecturer",
            campus="Boston",
            active=True,
        ),
    ]
    db.add_all(faculty_list)
    db.flush()

    # ------------------------------------------------------------------
    # Time blocks  (Fall 2026 semester start date used for day encoding;
    # start/end datetime objects store the wall-clock time on a Monday
    # or Tuesday anchor so the day-of-week is meaningful.)
    # ------------------------------------------------------------------
    # Monday = 2026-09-07, Tuesday = 2026-09-08, Wednesday = 2026-09-09
    # Thursday = 2026-09-10, Friday = 2026-09-11
    def dt(day: int, hour: int, minute: int = 0) -> datetime:
        """Return a datetime for the given day-of-month in Sep 2026."""
        return datetime(2026, 9, day, hour, minute)

    # MWF blocks (anchor to Mon Sep 7 / Wed Sep 9 / Fri Sep 11 — stored as one row each)
    # TTh blocks (anchor to Tue Sep 8 / Thu Sep 10)
    time_blocks = [
        TimeBlock(
            start_time=dt(7, 8, 0),
            end_time=dt(7, 9, 5),
            timezone="EST",
            campus="Boston",
        ),  # MWF 8–9:05
        TimeBlock(
            start_time=dt(7, 9, 15),
            end_time=dt(7, 10, 20),
            timezone="EST",
            campus="Boston",
        ),  # MWF 9:15–10:20
        TimeBlock(
            start_time=dt(7, 10, 30),
            end_time=dt(7, 11, 35),
            timezone="EST",
            campus="Boston",
        ),  # MWF 10:30–11:35
        TimeBlock(
            start_time=dt(7, 11, 45),
            end_time=dt(7, 12, 50),
            timezone="EST",
            campus="Boston",
        ),  # MWF 11:45–12:50
        TimeBlock(
            start_time=dt(7, 13, 35),
            end_time=dt(7, 14, 40),
            timezone="EST",
            campus="Boston",
        ),  # MWF 1:35–2:40
        TimeBlock(
            start_time=dt(7, 14, 50),
            end_time=dt(7, 15, 55),
            timezone="EST",
            campus="Boston",
        ),  # MWF 2:50–3:55
        TimeBlock(
            start_time=dt(8, 8, 0),
            end_time=dt(8, 9, 40),
            timezone="EST",
            campus="Boston",
        ),  # TTh 8–9:40
        TimeBlock(
            start_time=dt(8, 9, 50),
            end_time=dt(8, 11, 30),
            timezone="EST",
            campus="Boston",
        ),  # TTh 9:50–11:30
        TimeBlock(
            start_time=dt(8, 11, 45),
            end_time=dt(8, 13, 25),
            timezone="EST",
            campus="Boston",
        ),  # TTh 11:45–1:25
        TimeBlock(
            start_time=dt(8, 13, 35),
            end_time=dt(8, 15, 15),
            timezone="EST",
            campus="Boston",
        ),  # TTh 1:35–3:15
        TimeBlock(
            start_time=dt(8, 15, 30),
            end_time=dt(8, 17, 10),
            timezone="EST",
            campus="Boston",
        ),  # TTh 3:30–5:10
        TimeBlock(
            start_time=dt(7, 18, 0),
            end_time=dt(7, 21, 0),
            timezone="EST",
            campus="Boston",
        ),  # Mon eve 6–9
    ]
    db.add_all(time_blocks)
    db.flush()

    # ------------------------------------------------------------------
    # Schedule
    # ------------------------------------------------------------------
    schedule = Schedule(
        name="Fall 2026 Draft", semester=Semester.FALL, year=2026, draft=True
    )
    db.add(schedule)
    db.flush()

    schedule_log = ScheduleLog(
        schedule_id=schedule.schedule_id,
        content="Initial seed — auto-generated draft schedule.",
    )
    db.add(schedule_log)

    # ------------------------------------------------------------------
    # Sections  (30+ spread across courses and time blocks)
    # ------------------------------------------------------------------
    # (course_index, time_block_index, section_number, capacity, enrollment)
    section_specs = [
        # CS1 — 3 sections
        (0, 0, 1, 60),
        (0, 2, 2, 60),
        (0, 6, 3, 60),
        # CS2 — 3 sections
        (1, 1, 1, 50),
        (1, 3, 2, 50),
        (1, 7, 3, 50),
        # OOD — 3 sections
        (2, 2, 1, 40),
        (2, 4, 2, 40),
        (2, 8, 3, 40),
        # Algorithms — 2 sections
        (3, 3, 1, 40),
        (3, 9, 2, 40),
        # Computer Systems — 2 sections
        (4, 4, 1, 35),
        (4, 7, 2, 35),
        # Software Dev — 2 sections
        (5, 5, 1, 30),
        (5, 10, 2, 30),
        # Theory of Computation — 2 sections
        (6, 1, 1, 30),
        (6, 6, 2, 30),
        # Foundations of AI — 2 sections
        (7, 2, 1, 35),
        (7, 9, 2, 35),
        # Database Design — 2 sections
        (8, 0, 1, 35),
        (8, 8, 2, 35),
        # Networks — 2 sections
        (9, 3, 1, 30),
        (9, 10, 2, 30),
        # Programming Languages — 2 sections
        (10, 4, 1, 25),
        (10, 11, 2, 25),
        # Capstone — 3 sections
        (11, 5, 1, 20),
        (11, 9, 2, 20),
        (11, 11, 3, 20),
        # Additional CS1 / CS2 sections to exceed 30
        (0, 5, 4, 60),
        (1, 8, 4, 50),
        (2, 10, 4, 40),
        (3, 11, 3, 40),
    ]

    sections = []
    for course_idx, tb_idx, sec_num, cap in section_specs:
        sections.append(
            Section(
                section_number=sec_num,
                capacity=cap,
                schedule_id=schedule.schedule_id,
                time_block_id=time_blocks[tb_idx].time_block_id,
                course_id=courses[course_idx].course_id,
            )
        )
    db.add_all(sections)
    db.flush()

    print(f"Created {len(sections)} sections.")

    # ------------------------------------------------------------------
    # Faculty assignments  (assign one faculty per section, cycling)
    # ------------------------------------------------------------------
    # Map courses to primary faculty
    course_faculty = {
        0: faculty_list[4],  # CS1 → Eve Patel
        1: faculty_list[4],  # CS2 → Eve Patel
        2: faculty_list[2],  # OOD → Carol Okafor
        3: faculty_list[1],  # Algorithms → Bob Martinez
        4: faculty_list[5],  # Systems → Frank Torres
        5: faculty_list[3],  # Software Dev → David Kim
        6: faculty_list[1],  # Theory → Bob Martinez
        7: faculty_list[0],  # AI → Alice Chen
        8: faculty_list[3],  # DB → David Kim
        9: faculty_list[6],  # Networks → Grace Liu
        10: faculty_list[7],  # PL → Henry Nguyen
        11: faculty_list[6],  # Capstone → Grace Liu
    }

    # Secondary faculty for large courses with multiple sections
    secondary_faculty = {
        0: faculty_list[7],  # CS1 extra → Henry Nguyen
        1: faculty_list[2],  # CS2 extra → Carol Okafor
        2: faculty_list[0],  # OOD extra → Alice Chen
        3: faculty_list[6],  # Algorithms extra → Grace Liu
    }

    assignments = []
    section_to_course_idx = {
        s: spec[0] for s, spec in zip(sections, section_specs, strict=True)
    }
    section_to_sec_num = {
        s: spec[2] for s, spec in zip(sections, section_specs, strict=True)
    }

    for section in sections:
        course_idx = section_to_course_idx[section]
        sec_num = section_to_sec_num[section]
        if sec_num >= 4 and course_idx in secondary_faculty:
            faculty = secondary_faculty[course_idx]
        else:
            faculty = course_faculty[course_idx]
        assignments.append(
            FacultyAssignment(
                faculty_nuid=faculty.nuid,
                section_id=section.section_id,
            )
        )
    db.add_all(assignments)

    # ------------------------------------------------------------------
    # Course preferences
    # ------------------------------------------------------------------
    preferences = [
        # Alice Chen loves AI, is willing to teach OOD
        CoursePreference(
            faculty_nuid=100001,
            course_id=courses[7].course_id,
            preference=PreferenceLevel.EAGER,
        ),
        CoursePreference(
            faculty_nuid=100001,
            course_id=courses[2].course_id,
            preference=PreferenceLevel.WILLING,
        ),
        # Bob Martinez loves Theory and Algorithms
        CoursePreference(
            faculty_nuid=100002,
            course_id=courses[6].course_id,
            preference=PreferenceLevel.EAGER,
        ),
        CoursePreference(
            faculty_nuid=100002,
            course_id=courses[3].course_id,
            preference=PreferenceLevel.EAGER,
        ),
        CoursePreference(
            faculty_nuid=100002,
            course_id=courses[0].course_id,
            preference=PreferenceLevel.NOT_INTERESTED,
        ),
        # Carol Okafor loves OOD, willing CS2
        CoursePreference(
            faculty_nuid=100003,
            course_id=courses[2].course_id,
            preference=PreferenceLevel.EAGER,
        ),
        CoursePreference(
            faculty_nuid=100003,
            course_id=courses[1].course_id,
            preference=PreferenceLevel.WILLING,
        ),
        # David Kim loves DB and Software Dev
        CoursePreference(
            faculty_nuid=100004,
            course_id=courses[8].course_id,
            preference=PreferenceLevel.EAGER,
        ),
        CoursePreference(
            faculty_nuid=100004,
            course_id=courses[5].course_id,
            preference=PreferenceLevel.EAGER,
        ),
        # Eve Patel loves intro courses
        CoursePreference(
            faculty_nuid=100005,
            course_id=courses[0].course_id,
            preference=PreferenceLevel.EAGER,
        ),
        CoursePreference(
            faculty_nuid=100005,
            course_id=courses[1].course_id,
            preference=PreferenceLevel.EAGER,
        ),
        CoursePreference(
            faculty_nuid=100005,
            course_id=courses[6].course_id,
            preference=PreferenceLevel.NOT_INTERESTED,
        ),
        # Frank Torres loves Systems, willing Networks
        CoursePreference(
            faculty_nuid=100006,
            course_id=courses[4].course_id,
            preference=PreferenceLevel.EAGER,
        ),
        CoursePreference(
            faculty_nuid=100006,
            course_id=courses[9].course_id,
            preference=PreferenceLevel.WILLING,
        ),
        # Grace Liu loves Networks and Capstone
        CoursePreference(
            faculty_nuid=100007,
            course_id=courses[9].course_id,
            preference=PreferenceLevel.EAGER,
        ),
        CoursePreference(
            faculty_nuid=100007,
            course_id=courses[11].course_id,
            preference=PreferenceLevel.EAGER,
        ),
        # Henry Nguyen loves PL
        CoursePreference(
            faculty_nuid=100008,
            course_id=courses[10].course_id,
            preference=PreferenceLevel.EAGER,
        ),
        CoursePreference(
            faculty_nuid=100008,
            course_id=courses[0].course_id,
            preference=PreferenceLevel.WILLING,
        ),
    ]
    db.add_all(preferences)

    # ------------------------------------------------------------------
    # Meeting preferences
    # ------------------------------------------------------------------
    meeting_prefs = [
        MeetingPreference(
            faculty_nuid=100001,
            meeting_time="MWF Morning",
            preference=PreferenceLevel.EAGER,
        ),
        MeetingPreference(
            faculty_nuid=100001,
            meeting_time="TTh Afternoon",
            preference=PreferenceLevel.WILLING,
        ),
        MeetingPreference(
            faculty_nuid=100002,
            meeting_time="TTh Morning",
            preference=PreferenceLevel.EAGER,
        ),
        MeetingPreference(
            faculty_nuid=100002,
            meeting_time="Evening",
            preference=PreferenceLevel.NOT_INTERESTED,
        ),
        MeetingPreference(
            faculty_nuid=100003,
            meeting_time="MWF Afternoon",
            preference=PreferenceLevel.EAGER,
        ),
        MeetingPreference(
            faculty_nuid=100004,
            meeting_time="TTh Morning",
            preference=PreferenceLevel.WILLING,
        ),
        MeetingPreference(
            faculty_nuid=100004,
            meeting_time="Evening",
            preference=PreferenceLevel.NOT_INTERESTED,
        ),
        MeetingPreference(
            faculty_nuid=100005,
            meeting_time="MWF Morning",
            preference=PreferenceLevel.EAGER,
        ),
        MeetingPreference(
            faculty_nuid=100005,
            meeting_time="MWF Afternoon",
            preference=PreferenceLevel.WILLING,
        ),
        MeetingPreference(
            faculty_nuid=100006,
            meeting_time="TTh Afternoon",
            preference=PreferenceLevel.EAGER,
        ),
        MeetingPreference(
            faculty_nuid=100007,
            meeting_time="Evening",
            preference=PreferenceLevel.WILLING,
        ),
        MeetingPreference(
            faculty_nuid=100008,
            meeting_time="MWF Morning",
            preference=PreferenceLevel.WILLING,
        ),
        MeetingPreference(
            faculty_nuid=100008,
            meeting_time="Evening",
            preference=PreferenceLevel.EAGER,
        ),
    ]
    db.add_all(meeting_prefs)

    db.commit()
    print("Seed complete.")
    print(f"  {len(courses)} courses")
    print(f"  {len(faculty_list)} faculty")
    print(f"  {len(time_blocks)} time blocks")
    print(f"  1 schedule ('{schedule.name}')")
    print(f"  {len(sections)} sections")
    print(f"  {len(assignments)} faculty assignments")
    print(f"  {len(preferences)} course preferences")
    print(f"  {len(meeting_prefs)} meeting preferences")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
