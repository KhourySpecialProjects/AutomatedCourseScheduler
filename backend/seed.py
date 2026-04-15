"""Seed the database with realistic course scheduling data.

Usage:
    From the backend/ directory:
        python seed.py

    Or with a custom DATABASE_URL:
        DATABASE_URL=postgresql://... python seed.py
"""

import os
import sys
from datetime import time

from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine
from app.core.enums import PreferenceLevel
from app.models.campus import Campus
from app.models.course import Course
from app.models.course_preference import CoursePreference
from app.models.faculty import Faculty
from app.models.faculty_assignment import FacultyAssignment
from app.models.meeting_preference import MeetingPreference
from app.models.schedule import Schedule
from app.models.schedule_log import ScheduleLog
from app.models.section import Section
from app.models.semester import Semester
from app.models.time_block import TimeBlock
from app.models.user import User

# Allow running from the backend/ directory without installing the package.
sys.path.insert(0, os.path.dirname(__file__))


def seed(db: Session) -> None:
    # ------------------------------------------------------------------
    # Guard: skip if data already exists
    # ------------------------------------------------------------------
    if db.query(Schedule).count() > 0:
        print("Database already contains data — skipping seed.")
        return

    # ------------------------------------------------------------------
    # Campus
    # ------------------------------------------------------------------
    boston = Campus(name="Boston")
    db.add(boston)
    db.flush()

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------
    courses = [
        Course(
            subject="CS",
            code=2500,
            name="Fundamentals of CS 1",
            description="Introduction to programming using Python.",
            credits=4,
        ),
        Course(
            subject="CS",
            code=2510,
            name="Fundamentals of CS 2",
            description="Object-oriented programming and data structures.",
            credits=4,
        ),
        Course(
            subject="CS",
            code=3500,
            name="Object-Oriented Design",
            description="Design patterns and OO principles.",
            credits=4,
        ),
        Course(
            subject="CS",
            code=3000,
            name="Algorithms and Data",
            description="Core algorithms, complexity, and data structures.",
            credits=4,
        ),
        Course(
            subject="CS",
            code=3650,
            name="Computer Systems",
            description="Memory, OS concepts, and systems programming in C.",
            credits=4,
        ),
        Course(
            subject="CS",
            code=4500,
            name="Software Development",
            description="Agile practices, version control, and team projects.",
            credits=4,
        ),
        Course(
            subject="CS",
            code=3800,
            name="Theory of Computation",
            description="Automata, formal languages, and computability.",
            credits=4,
        ),
        Course(
            subject="CS",
            code=4100,
            name="Foundations of AI",
            description="Search, knowledge representation, and machine learning.",
            credits=4,
        ),
        Course(
            subject="CS",
            code=3200,
            name="Database Design",
            description="Relational databases, SQL, and normalization.",
            credits=4,
        ),
        Course(
            subject="CS",
            code=3700,
            name="Networks and Distributed Systems",
            description="Protocols, sockets, and distributed computing.",
            credits=4,
        ),
        Course(
            subject="CS",
            code=4400,
            name="Programming Languages",
            description="Language paradigms, type systems, and interpreters.",
            credits=4,
        ),
        Course(
            subject="CS",
            code=4970,
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
            campus=boston.campus_id,
            active=True,
        ),
        Faculty(
            nuid=100002,
            first_name="Bob",
            last_name="Martinez",
            email="b.martinez@univ.edu",
            campus=boston.campus_id,
            active=True,
        ),
        Faculty(
            nuid=100003,
            first_name="Carol",
            last_name="Okafor",
            email="c.okafor@univ.edu",
            campus=boston.campus_id,
            active=True,
        ),
        Faculty(
            nuid=100004,
            first_name="David",
            last_name="Kim",
            email="d.kim@univ.edu",
            campus=boston.campus_id,
            active=True,
        ),
        Faculty(
            nuid=100005,
            first_name="Eve",
            last_name="Patel",
            email="e.patel@univ.edu",
            campus=boston.campus_id,
            active=True,
        ),
        Faculty(
            nuid=100006,
            first_name="Frank",
            last_name="Torres",
            email="f.torres@univ.edu",
            campus=boston.campus_id,
            active=True,
        ),
        Faculty(
            nuid=100007,
            first_name="Grace",
            last_name="Liu",
            email="g.liu@univ.edu",
            campus=boston.campus_id,
            active=True,
        ),
        Faculty(
            nuid=100008,
            first_name="Henry",
            last_name="Nguyen",
            email="h.nguyen@univ.edu",
            campus=boston.campus_id,
            active=True,
        ),
    ]
    db.add_all(faculty_list)
    db.flush()

    # ------------------------------------------------------------------
    # Seed admins (representative dev data — emails are fake so Auth0
    # login won't work for these. Run bootstrap_admin.py to insert a
    # real admin with your own NUID and email for end-to-end testing.)
    # ------------------------------------------------------------------
    seed_admins = [
        User(
            nuid=faculty_list[0].nuid,
            first_name=faculty_list[0].first_name,
            last_name=faculty_list[0].last_name,
            email=faculty_list[0].email,
            role="ADMIN",
            auth0_sub=None,
            active=True,
        ),
        User(
            nuid=faculty_list[1].nuid,
            first_name=faculty_list[1].first_name,
            last_name=faculty_list[1].last_name,
            email=faculty_list[1].email,
            role="ADMIN",
            auth0_sub=None,
            active=True,
        ),
        User(
            nuid=faculty_list[2].nuid,
            first_name=faculty_list[2].first_name,
            last_name=faculty_list[2].last_name,
            email=faculty_list[2].email,
            role="ADMIN",
            auth0_sub=None,
            active=True,
        ),
    ]
    db.add_all(seed_admins)

    # ------------------------------------------------------------------
    # Time blocks
    # ------------------------------------------------------------------
    # time_block indices: 0=MWR 8:00, 1=MWR 9:15, 2=MWR 10:30,
    #                     3=MR 11:45, 4=MR 1:35,
    #                     5=WF 11:45, 6=WF 1:35, 7=WF 2:50
    time_blocks = [
        TimeBlock(
            meeting_days="MWR",
            start_time=time(8, 0),
            end_time=time(9, 5),
            campus=boston.campus_id,
        ),  # idx 0  MWR 8:00–9:05
        TimeBlock(
            meeting_days="MWR",
            start_time=time(9, 15),
            end_time=time(10, 20),
            campus=boston.campus_id,
        ),  # idx 1  MWR 9:15–10:20
        TimeBlock(
            meeting_days="MWR",
            start_time=time(10, 30),
            end_time=time(11, 35),
            campus=boston.campus_id,
        ),  # idx 2  MWR 10:30–11:35
        TimeBlock(
            meeting_days="MR",
            start_time=time(11, 45),
            end_time=time(13, 25),
            campus=boston.campus_id,
        ),  # idx 3  MR 11:45–1:25
        TimeBlock(
            meeting_days="MR",
            start_time=time(13, 35),
            end_time=time(15, 15),
            campus=boston.campus_id,
        ),  # idx 4  MR 1:35–3:15
        TimeBlock(
            meeting_days="WF",
            start_time=time(11, 45),
            end_time=time(13, 25),
            campus=boston.campus_id,
        ),  # idx 5  WF 11:45–1:25
        TimeBlock(
            meeting_days="WF",
            start_time=time(13, 35),
            end_time=time(15, 15),
            campus=boston.campus_id,
        ),  # idx 6  WF 1:35–3:15
        TimeBlock(
            meeting_days="WF",
            start_time=time(14, 50),
            end_time=time(16, 30),
            campus=boston.campus_id,
        ),  # idx 7  WF 2:50–4:30
    ]
    db.add_all(time_blocks)
    db.flush()

    # ------------------------------------------------------------------
    # Schedule
    # ------------------------------------------------------------------
    semester = Semester(
        season="FALL",
        year=2026,
    )
    schedule = Schedule(
        name="Fall 2026 Draft",
        semester=semester,
        schedule_id=1,
        campus=boston.campus_id,
        draft=True,
    )
    db.add(schedule)
    db.flush()

    schedule_log = ScheduleLog(
        schedule_id=schedule.schedule_id,
        content="Initial seed — auto-generated draft schedule.",
        updated_by=1,
    )
    db.add(schedule_log)

    # ------------------------------------------------------------------
    # Sections  (30+ spread across courses and time blocks)
    # ------------------------------------------------------------------
    # (course_index, time_block_index, section_number, capacity)
    # time_block indices: 0=MWR 8:00, 1=MWR 9:15, 2=MWR 10:30,
    #                     3=MR 11:45, 4=MR 1:35,
    #                     5=WF 11:45, 6=WF 1:35, 7=WF 2:50
    section_specs = [
        # CS1 — 4 sections
        (0, 0, 1, 60),
        (0, 1, 2, 60),
        (0, 5, 3, 60),
        (0, 7, 4, 60),
        # CS2 — 4 sections
        (1, 1, 1, 50),
        (1, 3, 2, 50),
        (1, 5, 3, 50),
        (1, 6, 4, 50),
        # OOD — 4 sections
        (2, 2, 1, 40),
        (2, 4, 2, 40),
        (2, 6, 3, 40),
        (2, 7, 4, 40),
        # Algorithms — 2 sections
        (3, 3, 1, 40),
        (3, 4, 2, 40),
        # Computer Systems — 2 sections
        (4, 1, 1, 35),
        (4, 4, 2, 35),
        # Software Dev — 2 sections
        (5, 5, 1, 30),
        (5, 7, 2, 30),
        # Theory of Computation — 2 sections
        (6, 0, 1, 30),
        (6, 1, 2, 30),
        # Foundations of AI — 2 sections
        (7, 2, 1, 35),
        (7, 3, 2, 35),
        # Database Design — 2 sections
        (8, 0, 1, 35),
        (8, 6, 2, 35),
        # Networks — 2 sections
        (9, 3, 1, 30),
        (9, 7, 2, 30),
        # Programming Languages — 2 sections
        (10, 2, 1, 25),
        (10, 4, 2, 25),
        # Capstone — 3 sections
        (11, 5, 1, 20),
        (11, 3, 2, 20),
        (11, 6, 3, 20),
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
    section_to_course_idx = {s: spec[0] for s, spec in zip(sections, section_specs, strict=True)}
    section_to_sec_num = {s: spec[2] for s, spec in zip(sections, section_specs, strict=True)}

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
    # time_blocks: 0=MWR 8:00, 1=MWR 9:15, 2=MWR 10:30,
    #              3=MR 11:45,  4=MR 13:35,
    #              5=WF 11:45,  6=WF 13:35,  7=WF 14:50
    meeting_prefs = [
        MeetingPreference(
            faculty_nuid=100001,
            meeting_time=time_blocks[1].time_block_id,  # MWR 9:15
            preference=PreferenceLevel.EAGER,
        ),
        MeetingPreference(
            faculty_nuid=100001,
            meeting_time=time_blocks[4].time_block_id,  # MR 13:35
            preference=PreferenceLevel.WILLING,
        ),
        MeetingPreference(
            faculty_nuid=100002,
            meeting_time=time_blocks[3].time_block_id,  # MR 11:45
            preference=PreferenceLevel.EAGER,
        ),
        MeetingPreference(
            faculty_nuid=100002,
            meeting_time=time_blocks[6].time_block_id,  # WF 13:35
            preference=PreferenceLevel.NOT_INTERESTED,
        ),
        MeetingPreference(
            faculty_nuid=100003,
            meeting_time=time_blocks[6].time_block_id,  # WF 13:35
            preference=PreferenceLevel.EAGER,
        ),
        MeetingPreference(
            faculty_nuid=100004,
            meeting_time=time_blocks[3].time_block_id,  # MR 11:45
            preference=PreferenceLevel.WILLING,
        ),
        MeetingPreference(
            faculty_nuid=100004,
            meeting_time=time_blocks[6].time_block_id,  # WF 13:35
            preference=PreferenceLevel.NOT_INTERESTED,
        ),
        MeetingPreference(
            faculty_nuid=100005,
            meeting_time=time_blocks[1].time_block_id,  # MWR 9:15
            preference=PreferenceLevel.EAGER,
        ),
        MeetingPreference(
            faculty_nuid=100005,
            meeting_time=time_blocks[5].time_block_id,  # WF 11:45
            preference=PreferenceLevel.WILLING,
        ),
        MeetingPreference(
            faculty_nuid=100006,
            meeting_time=time_blocks[4].time_block_id,  # MR 13:35
            preference=PreferenceLevel.EAGER,
        ),
        MeetingPreference(
            faculty_nuid=100007,
            meeting_time=time_blocks[6].time_block_id,  # WF 13:35
            preference=PreferenceLevel.WILLING,
        ),
        MeetingPreference(
            faculty_nuid=100008,
            meeting_time=time_blocks[1].time_block_id,  # MWR 9:15
            preference=PreferenceLevel.WILLING,
        ),
        MeetingPreference(
            faculty_nuid=100008,
            meeting_time=time_blocks[7].time_block_id,  # WF 14:50
            preference=PreferenceLevel.EAGER,
        ),
    ]
    db.add_all(meeting_prefs)

    db.commit()
    print("Seed complete.")
    print(f"  1 campus ('{boston.name}')")
    print(f"  {len(courses)} courses")
    print(f"  {len(faculty_list)} faculty")
    print(f"  {len(time_blocks)} time blocks")
    print(f"  1 schedule ('{schedule.name}')")
    print(f"  {len(sections)} sections")
    print(f"  {len(assignments)} faculty assignments")
    print(f"  {len(preferences)} course preferences")
    print(f"  {len(meeting_prefs)} meeting preferences")
    print(
        f"  {len(seed_admins)} seed admin users (fake emails"
        f" — run bootstrap_admin.py for real login)"
    )


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed(db)
