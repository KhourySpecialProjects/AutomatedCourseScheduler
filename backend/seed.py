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
    satellite_campuses = [Campus(name="Arlington"),
                          Campus(name="London"),
                          Campus(name="Miami"),
                          Campus(name="Oakland"),
                          Campus(name="Portland"),
                          Campus(name="San Francisco"),
                          Campus(name="Seattle"),
                          Campus(name="Sillicon Valley"),
                          Campus(name="Vancouver")]
    db.add_all(satellite_campuses)
    db.flush()

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------
    courses = [
        Course(course_id=1, subject="CS", code=142, name="Product Design with Machine Learning",
               description="", credits=4, priority=False),
        Course(course_id=2, subject="CS", code=180, name="Special Topics in Professional Development",
               description="", credits=4, priority=False),
        Course(course_id=3, subject="CS", code=1100, name="Computer Science and Its Applications",
               description="", credits=4, priority=False),
        Course(course_id=4, subject="CS", code=1101, name="Lab for CS 1100",
               description="", credits=4, priority=False),
        Course(course_id=5, subject="CS", code=1200, name="First Year Seminar",
               description="", credits=4, priority=False),
        Course(course_id=6, subject="CS", code=1210, name="Professional Development for Khoury Co-op",
               description="", credits=4, priority=False),
        Course(course_id=7, subject="CS", code=1800, name="Discrete Structures",
               description="", credits=4, priority=False),
        Course(course_id=8, subject="CS", code=1802, name="Seminar for CS 1800",
               description="", credits=4, priority=False),
        Course(course_id=9, subject="CS", code=2000, name="Introduction to Program Design and Implementation",
               description="", credits=4, priority=False),
        Course(course_id=10, subject="CS", code=2001, name="Lab for CS 2000",
               description="", credits=4, priority=False),
        Course(course_id=11, subject="CS", code=2100, name="Program Design and Implementation 1",
               description="", credits=4, priority=False),
        Course(course_id=12, subject="CS", code=2101, name="Lab for CS 2100",
               description="", credits=4, priority=False),
        Course(course_id=13, subject="CS", code=2386, name="Game Programming 1",
               description="", credits=4, priority=False),
        Course(course_id=14, subject="CS", code=2484, name="Principles of Human-Computer Interaction",
               description="", credits=4, priority=False),
        Course(course_id=15, subject="CS", code=2500, name="Fundamentals of Computer Science 1",
               description="", credits=4, priority=False),
        Course(course_id=16, subject="CS", code=2501, name="Lab for CS 2500",
               description="", credits=4, priority=False),
        Course(course_id=17, subject="CS", code=2535, name="Professional Practicum",
               description="", credits=4, priority=False),
        Course(course_id=18, subject="CS", code=2800, name="Logic and Computation",
               description="", credits=4, priority=False),
        Course(course_id=19, subject="CS", code=2801, name="Lab for CS 2800",
               description="", credits=4, priority=False),
        Course(course_id=20, subject="CS", code=2810, name="Mathematics of Data Models",
               description="", credits=4, priority=False),
        Course(course_id=21, subject="CS", code=3000, name="Algorithms and Data",
               description="", credits=4, priority=False),
        Course(course_id=22, subject="CS", code=3001, name="Recitation for CS 3000",
               description="", credits=4, priority=False),
        Course(course_id=23, subject="CS", code=3100, name="Program Design and Implementation 2",
               description="", credits=4, priority=False),
        Course(course_id=24, subject="CS", code=3101, name="Lab for CS 3100",
               description="", credits=4, priority=False),
        Course(course_id=25, subject="CS", code=3200, name="Introduction to Databases",
               description="", credits=4, priority=False),
        Course(course_id=26, subject="CS", code=3386, name="Game Programming 2",
               description="", credits=4, priority=False),
        Course(course_id=27, subject="CS", code=3500, name="Object-Oriented Design",
               description="", credits=4, priority=False),
        Course(course_id=28, subject="CS", code=3501, name="Lab for CS 3500",
               description="", credits=4, priority=False),
        Course(course_id=29, subject="CS", code=3520, name="Programming in C++",
               description="", credits=4, priority=False),
        Course(course_id=30, subject="CS", code=3540, name="Game Programming",
               description="", credits=4, priority=False),
        Course(course_id=31, subject="CS", code=3620, name="Building Extensible Systems",
               description="", credits=4, priority=False),
        Course(course_id=32, subject="CS", code=3650, name="Computer Systems",
               description="", credits=4, priority=False),
        Course(course_id=33, subject="CS", code=3700, name="Networks and Distributed Systems",
               description="", credits=4, priority=False),
        Course(course_id=34, subject="CS", code=3800, name="Theory of Computation",
               description="", credits=4, priority=False),
        Course(course_id=35, subject="CS", code=3950, name="Introduction to Computer Science Research",
               description="", credits=4, priority=False),
        Course(course_id=36, subject="CS", code=4050, name="Artificial Intelligence and Society",
               description="", credits=4, priority=False),
        Course(course_id=37, subject="CS", code=4097, name="Mixed Reality",
               description="", credits=4, priority=False),
        Course(course_id=38, subject="CS", code=4100, name="Artificial Intelligence",
               description="", credits=4, priority=False),
        Course(course_id=39, subject="CS", code=4120, name="Natural Language Processing",
               description="", credits=4, priority=False),
        Course(course_id=40, subject="CS", code=4130, name="Engineering LLM-Integrated Systems",
               description="", credits=4, priority=False),
        Course(course_id=41, subject="CS", code=4150, name="Game Artificial Intelligence",
               description="", credits=4, priority=False),
        Course(course_id=42, subject="CS", code=4180, name="Reinforcement Learning",
               description="", credits=4, priority=False),
        Course(course_id=43, subject="CS", code=4200, name="Database Internals",
               description="", credits=4, priority=False),
        Course(course_id=44, subject="CS", code=4240, name="Special Topics (varies by semester)",
               description="", credits=4, priority=False),
        Course(course_id=45, subject="CS", code=4300, name="Computer Graphics",
               description="", credits=4, priority=False),
        Course(course_id=46, subject="CS", code=4350, name="Empirical Research Methods",
               description="", credits=4, priority=False),
        Course(course_id=47, subject="CS", code=4360, name="Non-Interactive Computer Graphics",
               description="", credits=4, priority=False),
        Course(course_id=48, subject="CS", code=4400, name="Programming Languages",
               description="", credits=4, priority=False),
        Course(course_id=49, subject="CS", code=4410, name="Compilers",
               description="", credits=4, priority=False),
        Course(course_id=50, subject="CS", code=4500, name="Software Development",
               description="", credits=4, priority=False),
        Course(course_id=51, subject="CS", code=4520, name="Mobile Application Development",
               description="", credits=4, priority=False),
        Course(course_id=52, subject="CS", code=4530, name="Fundamentals of Software Engineering",
               description="", credits=4, priority=False),
        Course(course_id=53, subject="CS", code=4535, name="Professional Practicum Capstone",
               description="", credits=4, priority=False),
        Course(course_id=54, subject="CS", code=4545, name="Research Practicum",
               description="", credits=4, priority=False),
        Course(course_id=55, subject="CS", code=4550, name="Web Development",
               description="", credits=4, priority=False),
        Course(course_id=56, subject="CS", code=4610, name="Robotic Science and Systems",
               description="", credits=4, priority=False),
        Course(course_id=57, subject="CS", code=4700, name="Network Fundamentals",
               description="", credits=4, priority=False),
        Course(course_id=58, subject="CS", code=4710, name="Mobile and Wireless Systems",
               description="", credits=4, priority=False),
        Course(course_id=59, subject="CS", code=4730, name="Distributed Systems",
               description="", credits=4, priority=False),
        Course(course_id=60, subject="CS", code=4805, name="Fundamentals of Complexity Theory",
               description="", credits=4, priority=False),
        Course(course_id=61, subject="CS", code=4810, name="Advanced Algorithms",
               description="", credits=4, priority=False),
        Course(course_id=62, subject="CS", code=4820, name="Computer-Aided Reasoning",
               description="", credits=4, priority=False),
        Course(course_id=63, subject="CS", code=4830, name="System Specification Verification and Synthesis",
               description="", credits=4, priority=False),
        Course(course_id=64, subject="CS", code=4850, name="Building Game Engines",
               description="", credits=4, priority=False),
        Course(course_id=65, subject="CS", code=4910, name="Computer Science Topics",
               description="", credits=4, priority=False),
        Course(course_id=66, subject="CS", code=4950, name="Computer Science Research Seminar",
               description="", credits=4, priority=False),
        Course(course_id=67, subject="CS", code=4955, name="Computer Science Teaching Seminar",
               description="", credits=4, priority=False),
        Course(course_id=68, subject="CS", code=4973, name="Topics in Computer Science",
               description="", credits=4, priority=False),
        Course(course_id=69, subject="CS", code=5001, name="Intensive Foundations of Computer Science",
               description="", credits=4, priority=False),
        Course(course_id=70, subject="CS", code=5002, name="Discrete Structures",
               description="", credits=4, priority=False),
        Course(course_id=71, subject="CS", code=5003, name="Recitation for CS 5001",
               description="", credits=4, priority=False),
        Course(course_id=72, subject="CS", code=5004, name="Object-Oriented Design",
               description="", credits=4, priority=False),
        Course(course_id=73, subject="CS", code=5005, name="Recitation for CS 5004",
               description="", credits=4, priority=False),
        Course(course_id=74, subject="CS", code=5006, name="Algorithms",
               description="", credits=4, priority=False),
        Course(course_id=75, subject="CS", code=5007, name="Computer Systems",
               description="", credits=4, priority=False),
        Course(course_id=76, subject="CS", code=5008, name="Data Structures Algorithms and Their Applications within Computer Systems",
               description="", credits=4, priority=False),
        Course(course_id=77, subject="CS", code=5009, name="Recitation for CS 5008",
               description="", credits=4, priority=False),
        Course(course_id=78, subject="CS", code=5010, name="Programming Design Paradigm",
               description="", credits=4, priority=False),
        Course(course_id=79, subject="CS", code=5011, name="Recitation for CS 5010",
               description="", credits=4, priority=False),
        Course(course_id=80, subject="CS", code=5047, name="Exploring AI Trends and Tools",
               description="", credits=4, priority=False),
        Course(course_id=81, subject="CS", code=5097, name="Mixed Reality",
               description="", credits=4, priority=False),
        Course(course_id=82, subject="CS", code=5100, name="Foundations of Artificial Intelligence",
               description="", credits=4, priority=False),
        Course(course_id=83, subject="CS", code=5130, name="Applied Programming and Data Processing for AI",
               description="", credits=4, priority=False),
        Course(course_id=84, subject="CS", code=5131, name="Recitation for CS 5130",
               description="", credits=4, priority=False),
        Course(course_id=85, subject="CS", code=5150, name="Game Artificial Intelligence",
               description="", credits=4, priority=False),
        Course(course_id=86, subject="CS", code=5170, name="Artificial Intelligence for Human-Computer Interaction",
               description="", credits=4, priority=False),
        Course(course_id=87, subject="CS", code=5180, name="Reinforcement Learning and Sequential Decision Making",
               description="", credits=4, priority=False),
        Course(course_id=88, subject="CS", code=5200, name="Database Management Systems",
               description="", credits=4, priority=False),
        Course(course_id=89, subject="CS", code=5310, name="Computer Graphics",
               description="", credits=4, priority=False),
        Course(course_id=90, subject="CS", code=5330, name="Pattern Recognition and Computer Vision",
               description="", credits=4, priority=False),
        Course(course_id=91, subject="CS", code=5335, name="Robotic Science and Systems",
               description="", credits=4, priority=False),
        Course(course_id=92, subject="CS", code=5340, name="Computer/Human Interaction",
               description="", credits=4, priority=False),
        Course(course_id=93, subject="CS", code=5350, name="Computational Geometry",
               description="", credits=4, priority=False),
        Course(course_id=94, subject="CS", code=5360, name="Special Topics in Graphics (varies by semester)",
               description="", credits=4, priority=False),
        Course(course_id=95, subject="CS", code=5400, name="Principles of Programming Language",
               description="", credits=4, priority=False),
        Course(course_id=96, subject="CS", code=5500, name="Foundations of Software Engineering",
               description="", credits=4, priority=False),
        Course(course_id=97, subject="CS", code=5520, name="Mobile Application Development",
               description="", credits=4, priority=False),
        Course(course_id=98, subject="CS", code=5540, name="Game Programming",
               description="", credits=4, priority=False),
        Course(course_id=99, subject="CS", code=5600, name="Computer Systems",
               description="", credits=4, priority=False),
        Course(course_id=100, subject="CS", code=5610,
               name="Web Development", description="", credits=4, priority=False),
        Course(course_id=101, subject="CS", code=5700,
               name="Fundamentals of Computer Networking", description="", credits=4, priority=False),
        Course(course_id=102, subject="CS", code=5800, name="Algorithms",
               description="", credits=4, priority=False),
        Course(course_id=103, subject="CS", code=5850,
               name="Building Game Engines", description="", credits=4, priority=False),
        Course(course_id=104, subject="CS", code=5963, name="Topics",
               description="", credits=4, priority=False),
        Course(course_id=105, subject="CS", code=5964,
               name="Projects for Professionals", description="", credits=4, priority=False),
        Course(course_id=106, subject="CS", code=5965,
               name="Engaging with Industry Partners for Rising Professionals", description="", credits=4, priority=False),
        Course(course_id=107, subject="CS", code=6120,
               name="Natural Language Processing", description="", credits=4, priority=False),
        Course(course_id=108, subject="CS", code=6130,
               name="Affective Computing", description="", credits=4, priority=False),
        Course(course_id=109, subject="CS", code=6140,
               name="Machine Learning", description="", credits=4, priority=False),
        Course(course_id=110, subject="CS", code=6170,
               name="AI Capstone", description="", credits=4, priority=False),
        Course(course_id=111, subject="CS", code=6180,
               name="Foundations for Generative AI", description="", credits=4, priority=False),
        Course(course_id=112, subject="CS", code=6200,
               name="Information Retrieval", description="", credits=4, priority=False),
        Course(course_id=113, subject="CS", code=6220,
               name="Data Mining Techniques", description="", credits=4, priority=False),
        Course(course_id=114, subject="CS", code=6240,
               name="Large-Scale Parallel Data Processing", description="", credits=4, priority=False),
        Course(course_id=115, subject="CS", code=6350,
               name="Empirical Research Methods", description="", credits=4, priority=False),
        Course(course_id=116, subject="CS", code=6410, name="Compilers",
               description="", credits=4, priority=False),
        Course(course_id=117, subject="CS", code=6510,
               name="Advanced Software Development", description="", credits=4, priority=False),
        Course(course_id=118, subject="CS", code=6620,
               name="Fundamentals of Cloud Computing", description="", credits=4, priority=False),
        Course(course_id=119, subject="CS", code=6640,
               name="Operating Systems Implementation", description="", credits=4, priority=False),
        Course(course_id=120, subject="CS", code=6650,
               name="Building Scalable Distributed Systems", description="", credits=4, priority=False),
        Course(course_id=121, subject="CS", code=6710,
               name="Special Topics in Networking (varies by semester)", description="", credits=4, priority=False),
        Course(course_id=122, subject="CS", code=6760,
               name="Privacy Security and Usability", description="", credits=4, priority=False),
        Course(course_id=123, subject="CS", code=6949,
               name="Research/Co-op (varies)", description="", credits=4, priority=False),
        Course(course_id=124, subject="CS", code=6983,
               name="Topics in Computer Science", description="", credits=4, priority=False),
        Course(course_id=125, subject="CS", code=7140,
               name="Advanced Machine Learning", description="", credits=4, priority=False),
        Course(course_id=126, subject="CS", code=7150,
               name="Deep Learning", description="", credits=4, priority=False),
        Course(course_id=127, subject="CS", code=7170,
               name="Seminar in Artificial Intelligence", description="", credits=4, priority=False),
        Course(course_id=128, subject="CS", code=7180,
               name="Special Topics in Artificial Intelligence", description="", credits=4, priority=False),
        Course(course_id=129, subject="CS", code=7200,
               name="Statistical Methods for Computer Science", description="", credits=4, priority=False),
        Course(course_id=130, subject="CS", code=7240,
               name="Principles of Scalable Data Management", description="", credits=4, priority=False),
        Course(course_id=131, subject="CS", code=7250,
               name="Information Visualization: Theory and Applications", description="", credits=4, priority=False),
        Course(course_id=132, subject="CS", code=7260,
               name="Visualization for Network Science", description="", credits=4, priority=False),
        Course(course_id=133, subject="CS", code=7268,
               name="Verifiable Machine Learning", description="", credits=4, priority=False),
        Course(course_id=134, subject="CS", code=7270,
               name="Seminar in Database Systems", description="", credits=4, priority=False),
        Course(course_id=135, subject="CS", code=7280,
               name="Special Topics in Database Management", description="", credits=4, priority=False),
        Course(course_id=136, subject="CS", code=7290,
               name="Special Topics in Data Science", description="", credits=4, priority=False),
        Course(course_id=137, subject="CS", code=7295,
               name="Special Topics in Data Visualization", description="", credits=4, priority=False),
        Course(course_id=138, subject="CS", code=7300,
               name="Empirical Research Methods for Human Computer Interaction", description="", credits=4, priority=False),
        Course(course_id=139, subject="CS", code=7332,
               name="Machine Learning with Graphs", description="", credits=4, priority=False),
        Course(course_id=140, subject="CS", code=7340,
               name="Theory and Methods in Human Computer Interaction", description="", credits=4, priority=False),
        Course(course_id=141, subject="CS", code=7375,
               name="Seminar in Human-Computer Interaction", description="", credits=4, priority=False),
        Course(course_id=142, subject="CS", code=7380,
               name="Special Topics in Graphics/Image Processing", description="", credits=4, priority=False),
        Course(course_id=143, subject="CS", code=7390,
               name="Special Topics in Human-Centered Computing", description="", credits=4, priority=False),
        Course(course_id=144, subject="CS", code=7400,
               name="Intensive Principles of Programming Languages", description="", credits=4, priority=False),
        Course(course_id=145, subject="CS", code=7430,
               name="Formal Specification Verification and Synthesis", description="", credits=4, priority=False),
        Course(course_id=146, subject="CS", code=7470,
               name="Seminar in Programming Languages", description="", credits=4, priority=False),
        Course(course_id=147, subject="CS", code=7480,
               name="Special Topics in Programming Language", description="", credits=4, priority=False),
        Course(course_id=148, subject="CS", code=7485,
               name="Special Topics in Formal Methods", description="", credits=4, priority=False),
        Course(course_id=149, subject="CS", code=7575,
               name="Seminar in Software Engineering", description="", credits=4, priority=False),
        Course(course_id=150, subject="CS", code=7580,
               name="Special Topics in Software Engineering", description="", credits=4, priority=False),
        Course(course_id=151, subject="CS", code=7600,
               name="Intensive Computer Systems", description="", credits=4, priority=False),
        Course(course_id=152, subject="CS", code=7610,
               name="Foundations of Distributed Systems", description="", credits=4, priority=False),
        Course(course_id=153, subject="CS", code=7670,
               name="Seminar in Computer Systems", description="", credits=4, priority=False),
        Course(course_id=154, subject="CS", code=7680,
               name="Special Topics in Computer Systems", description="", credits=4, priority=False),
        Course(course_id=155, subject="CS", code=7770,
               name="Seminar in Computer Networks", description="", credits=4, priority=False),
        Course(course_id=156, subject="CS", code=7775,
               name="Seminar in Computer Security", description="", credits=4, priority=False),
        Course(course_id=157, subject="CS", code=7800,
               name="Advanced Algorithms", description="", credits=4, priority=False),
        Course(course_id=158, subject="CS", code=7805,
               name="Complexity Theory", description="", credits=4, priority=False),
        Course(course_id=159, subject="CS", code=7810,
               name="Foundations of Cryptography", description="", credits=4, priority=False),
        Course(course_id=160, subject="CS", code=7840,
               name="Foundations and Applications of Information Theory", description="", credits=4, priority=False),
        Course(course_id=161, subject="CS", code=7870,
               name="Seminar in Theoretical Computer Science", description="", credits=4, priority=False),
        Course(course_id=162, subject="CS", code=7880,
               name="Special Topics in Theoretical Computer Science", description="", credits=4, priority=False),
        Course(course_id=163, subject="CS", code=7930,
               name="Effective Scientific Writing in Computer Science", description="", credits=4, priority=False),
        Course(course_id=164, subject="CS", code=7980,
               name="Research Capstone", description="", credits=4, priority=False),
        Course(course_id=165, subject="CY", code=2550,
               name="Foundations of Cybersecurity", description="", credits=4, priority=False),
        Course(course_id=166, subject="CY", code=3740,
               name="Systems Security", description="", credits=4, priority=False),
        Course(course_id=167, subject="CY", code=4100,
               name="AI Security and Privacy", description="", credits=4, priority=False),
        Course(course_id=168, subject="CY", code=4170,
               name="The Law Ethics and Policy of Data and Digital Technologies", description="", credits=4, priority=False),
        Course(course_id=169, subject="CY", code=4740,
               name="Network Security", description="", credits=4, priority=False),
        Course(course_id=170, subject="CY", code=4760,
               name="Security of Wireless and Mobile Systems", description="", credits=4, priority=False),
        Course(course_id=171, subject="CY", code=4770,
               name="Foundations of Cryptography", description="", credits=4, priority=False),
        Course(course_id=172, subject="CY", code=4930,
               name="Cybersecurity Capstone", description="", credits=4, priority=False),
        Course(course_id=173, subject="CY", code=4973,
               name="Topics in Cybersecurity", description="", credits=4, priority=False),
        Course(course_id=174, subject="CY", code=5001,
               name="Cybersecurity: Technologies Threats and Defenses", description="", credits=4, priority=False),
        Course(course_id=175, subject="CY", code=5003,
               name="Foundations of Software Security", description="", credits=4, priority=False),
        Course(course_id=176, subject="CY", code=5010,
               name="Cybersecurity Principles and Practices", description="", credits=4, priority=False),
        Course(course_id=177, subject="CY", code=5061,
               name="Cloud Security", description="", credits=4, priority=False),
        Course(course_id=178, subject="CY", code=5062,
               name="Introduction to IoT Security", description="", credits=4, priority=False),
        Course(course_id=179, subject="CY", code=5065,
               name="Cloud Security Practices", description="", credits=4, priority=False),
        Course(course_id=180, subject="CY", code=5120,
               name="Applied Cryptography", description="", credits=4, priority=False),
        Course(course_id=181, subject="CY", code=5130,
               name="Computer System Security", description="", credits=4, priority=False),
        Course(course_id=182, subject="CY", code=5150,
               name="Network Security Practices", description="", credits=4, priority=False),
        Course(course_id=183, subject="CY", code=5200,
               name="Security Risk Management and Assessment", description="", credits=4, priority=False),
        Course(course_id=184, subject="CY", code=5210,
               name="Information System Forensics", description="", credits=4, priority=False),
        Course(course_id=185, subject="CY", code=5240,
               name="Cyberlaw: Privacy Ethics and Digital Rights", description="", credits=4, priority=False),
        Course(course_id=186, subject="CY", code=5250,
               name="Decision Making for Critical Infrastructure", description="", credits=4, priority=False),
        Course(course_id=187, subject="CY", code=5770,
               name="Software Vulnerabilities and Security", description="", credits=4, priority=False),
        Course(course_id=188, subject="CY", code=6120,
               name="Software Security Practices", description="", credits=4, priority=False),
        Course(course_id=189, subject="CY", code=6200,
               name="Special Topics in IT Security Governance Risk and Compliance", description="", credits=4, priority=False),
        Course(course_id=190, subject="CY", code=6240,
               name="Special Topics in Privacy Law", description="", credits=4, priority=False),
        Course(course_id=191, subject="CY", code=6720,
               name="Machine Learning in Cybersecurity and Privacy", description="", credits=4, priority=False),
        Course(course_id=192, subject="CY", code=6740,
               name="Network Security", description="", credits=4, priority=False),
        Course(course_id=193, subject="CY", code=6750,
               name="Cryptography and Communications Security", description="", credits=4, priority=False),
        Course(course_id=194, subject="CY", code=6760,
               name="Wireless and Mobile Systems Security", description="", credits=4, priority=False),
        Course(course_id=195, subject="CY", code=7790,
               name="Special Topics in Security and Privacy", description="", credits=4, priority=False),
        Course(course_id=196, subject="CY", code=7900,
               name="Capstone Project", description="", credits=4, priority=False),
        Course(course_id=197, subject="DA", code=5020,
               name="Collecting Storing and Retrieving Data", description="", credits=4, priority=False),
        Course(course_id=198, subject="DA", code=5030,
               name="Introduction to Data Mining/Machine Learning", description="", credits=4, priority=False),
        Course(course_id=199, subject="DS", code=1300,
               name="Knowledge in a Digital World", description="", credits=4, priority=False),
        Course(course_id=200, subject="DS", code=2000,
               name="Programming with Data", description="", credits=4, priority=False),
        Course(course_id=201, subject="DS", code=2001,
               name="Lab for DS 2000", description="", credits=4, priority=False),
        Course(course_id=202, subject="DS", code=2500,
               name="Intermediate Programming with Data", description="", credits=4, priority=False),
        Course(course_id=203, subject="DS", code=2501,
               name="Lab for DS 2500", description="", credits=4, priority=False),
        Course(course_id=204, subject="DS", code=3000,
               name="Foundations of Data Science", description="", credits=4, priority=False),
        Course(course_id=205, subject="DS", code=3500,
               name="Advanced Programming with Data", description="", credits=4, priority=False),
        Course(course_id=206, subject="DS", code=4200,
               name="Information Presentation and Visualization", description="", credits=4, priority=False),
        Course(course_id=207, subject="DS", code=4300,
               name="Large-Scale Information Storage and Retrieval", description="", credits=4, priority=False),
        Course(course_id=208, subject="DS", code=4400,
               name="Machine Learning and Data Mining 1", description="", credits=4, priority=False),
        Course(course_id=209, subject="DS", code=4420,
               name="Machine Learning and Data Mining 2", description="", credits=4, priority=False),
        Course(course_id=210, subject="DS", code=4440,
               name="Practical Neural Networks", description="", credits=4, priority=False),
        Course(course_id=211, subject="DS", code=4900,
               name="Data Science Senior Project (varies)", description="", credits=4, priority=False),
        Course(course_id=212, subject="DS", code=4973,
               name="Topics in Data Science", description="", credits=4, priority=False),
        Course(course_id=213, subject="DS", code=5010,
               name="Introduction to Programming for Data Science", description="", credits=4, priority=False),
        Course(course_id=214, subject="DS", code=5020,
               name="Introduction to Linear Algebra and Probability for Data Science", description="", credits=4, priority=False),
        Course(course_id=215, subject="DS", code=5110,
               name="Introduction to Data Management and Processing", description="", credits=4, priority=False),
        Course(course_id=216, subject="DS", code=5220,
               name="Supervised Machine Learning and Learning Theory", description="", credits=4, priority=False),
        Course(course_id=217, subject="DS", code=5230,
               name="Unsupervised Machine Learning and Data Mining", description="", credits=4, priority=False),
        Course(course_id=218, subject="DS", code=5500,
               name="Data Science Capstone", description="", credits=4, priority=False),
        Course(course_id=219, subject="DS", code=5983,
               name="Topics in Data Science", description="", credits=4, priority=False),
        Course(course_id=220, subject="HINF", code=200,
               name="Health and Medicine for Nonclinicians", description="", credits=4, priority=False),
        Course(course_id=221, subject="HINF", code=5101,
               name="Introduction to Health Informatics and Health Information Systems", description="", credits=4, priority=False),
        Course(course_id=222, subject="HINF", code=5102,
               name="Data Management in Healthcare", description="", credits=4, priority=False),
        Course(course_id=223, subject="HINF", code=5105,
               name="The American Healthcare System", description="", credits=4, priority=False),
        Course(course_id=224, subject="HINF", code=5106,
               name="Health Informatics Special Topics (varies)", description="", credits=4, priority=False),
        Course(course_id=225, subject="HINF", code=5110,
               name="Global Health Information Management", description="", credits=4, priority=False),
        Course(course_id=226, subject="HINF", code=5200,
               name="Theoretical Foundations in Personal Health Informatics", description="", credits=4, priority=False),
        Course(course_id=227, subject="HINF", code=5300,
               name="Personal Health Interface Design and Development", description="", credits=4, priority=False),
        Course(course_id=228, subject="HINF", code=5301,
               name="Evaluating Health Technologies", description="", credits=4, priority=False),
        Course(course_id=229, subject="HINF", code=5407,
               name="Business Application of Decision Support in Healthcare", description="", credits=4, priority=False),
        Course(course_id=230, subject="HINF", code=6201,
               name="Organizational Behavior Work Flow Design and Change Management", description="", credits=4, priority=False),
        Course(course_id=231, subject="HINF", code=6202,
               name="Business of Healthcare Informatics", description="", credits=4, priority=False),
        Course(course_id=232, subject="HINF", code=6205,
               name="Creation and Application of Medical Knowledge", description="", credits=4, priority=False),
        Course(course_id=233, subject="HINF", code=6215,
               name="Project Management", description="", credits=4, priority=False),
        Course(course_id=234, subject="HINF", code=6220,
               name="Database Design Access Modeling and Security", description="", credits=4, priority=False),
        Course(course_id=235, subject="HINF", code=6240,
               name="Improving the Patient Experience Through Informatics", description="", credits=4, priority=False),
        Course(course_id=236, subject="HINF", code=6335,
               name="Management Issues in Healthcare Information Technology", description="", credits=4, priority=False),
        Course(course_id=237, subject="HINF", code=6345,
               name="Design for Usability in Healthcare", description="", credits=4, priority=False),
        Course(course_id=238, subject="HINF", code=6350,
               name="Public Health Surveillance and Informatics", description="", credits=4, priority=False),
        Course(course_id=239, subject="HINF", code=6355,
               name="Interoperability Key Standards in Health Informatics", description="", credits=4, priority=False),
        Course(course_id=240, subject="HINF", code=6400,
               name="Introduction to Health Data Analytics", description="", credits=4, priority=False),
        Course(course_id=241, subject="HINF", code=6404,
               name="Patient Engagement Informatics and Analytics", description="", credits=4, priority=False),
        Course(course_id=242, subject="HINF", code=6405,
               name="Quantifying the Value of Informatics", description="", credits=4, priority=False),
        Course(course_id=243, subject="IS", code=1300,
               name="Knowledge in a Digital World", description="", credits=4, priority=False),
        Course(course_id=244, subject="IS", code=1500,
               name="Introduction to Web Development", description="", credits=4, priority=False),
        Course(course_id=245, subject="IS", code=2000,
               name="Principles of Information Science", description="", credits=4, priority=False),
        Course(course_id=246, subject="IS", code=3050,
               name="Information and Uncertainty", description="", credits=4, priority=False),
        Course(course_id=247, subject="IS", code=3500,
               name="Information System Design and Development", description="", credits=4, priority=False),
        Course(course_id=248, subject="IS", code=4200,
               name="Information Retrieval", description="", credits=4, priority=False),
        Course(course_id=249, subject="IS", code=4300,
               name="Human-Computer Interaction", description="", credits=4, priority=False),
        Course(course_id=250, subject="IS", code=4600,
               name="Software Project Management", description="", credits=4, priority=False),
        Course(course_id=251, subject="IS", code=4800,
               name="Empirical Research Methods", description="", credits=4, priority=False),
    ]

    db.add_all(courses)
    db.flush()  # populate PKs

    # ------------------------------------------------------------------
    # Faculty
    # ------------------------------------------------------------------
    # (nuid, first_name, last_name, email)
    _faculty_data = [
        (12, "Amal", "Ahmed", "ahmed.a@northeastern.edu"),
        (696, "Dawn", "Shirak", "shirak.d@northeastern.edu"),
        (384, "Mary", "Kennedy", "kennedy.m@northeastern.edu"),
        (131, "David", "Choffnes", "choffnes.d@northeastern.edu"),
        (385, "Aileen", "Kent Yates", "kentyates.a@northeastern.edu"),
        (697, "Jennifer", "Shire", "shire.j@northeastern.edu"),
        (427, "Ben", "Lerner", "lerner.b@northeastern.edu"),
        (177, "Nate", "Derbinsky", "derbinsky.n@northeastern.edu"),
        (500, "Vidoje", "Mihajlovikj", "mihajlovikj.v@northeastern.edu"),
        (784, "Nathaniel", "Tuck", "tuck.n@northeastern.edu"),
        (603, "Predrag", "Radivojac", "radivojac.p@northeastern.edu"),
        (620, "Leena", "Razzaq", "razzaq.l@northeastern.edu"),
        (834, "Claire", "Wassinger", "wassinger.c@northeastern.edu"),
        (49, "Keith", "Bagley", "bagley.k@northeastern.edu"),
        (719, "David", "Smith", "smith.d@northeastern.edu"),
        (663, "Martin", "Schedlbauer", "schedlbauer.m@northeastern.edu"),
        (227, "Matthias", "Felleisen", "felleisen.m@northeastern.edu"),
        (34, "Jose", "Annunziato", "annunziato.j@northeastern.edu"),
        (628, "Mirek", "Riedewald", "riedewald.m@northeastern.edu"),
        (391, "Engin", "Kirda", "kirda.e@northeastern.edu"),
        (547, "Cristina", "Nita-Rotaru", "nitarotaru.c@northeastern.edu"),
        (362, "Craig", "Johnson", "johnson.c@northeastern.edu"),
        (219, "Don", "Fallis", "fallis.d@northeastern.edu"),
        (633, "William", "Robertson", "robertson.w@northeastern.edu"),
        (688, "Abhi", "Shelat", "shelat.a@northeastern.edu"),
        (141, "Ran", "Cohen", "cohen.r@northeastern.edu"),
        (693, "Amit", "Shesh", "shesh.a@northeastern.edu"),
        (730, "Jessica", "Speece", "speece.j@northeastern.edu"),
        (406, "Prajna", "Kulkarni", "kulkarni.p@northeastern.edu"),
        (319, "Ben", "Hescott", "hescott.b@northeastern.edu"),
        (585, "Virgil", "Pavlu", "pavlu.v@northeastern.edu"),
        (742, "Laney", "Strange", "strange.l@northeastern.edu"),
        (20, "Lucas", "Almeida", "almeida.l@northeastern.edu"),
        (873, "Caglar", "Yildirim", "yildirim.c@northeastern.edu"),
        (225, "Daniel", "Feinberg", "feinberg.d@northeastern.edu"),
        (733, "Jay", "Spitulnik", "spitulnik.j@northeastern.edu"),
        (785, "Catherine", "Turner", "turner.c@northeastern.edu"),
        (533, "Felix", "Muzny", "muzny.f@northeastern.edu"),
        (630, "Dan", "Ries", "ries.d@northeastern.edu"),
        (844, "Christo", "Wilson", "wilson.c@northeastern.edu"),
        (601, "John", "Rachlin", "rachlin.j@northeastern.edu"),
        (254, "Myles", "Garvey", "garvey.m@northeastern.edu"),
        (495, "Amber", "Meyers", "meyers.a@northeastern.edu"),
        (320, "Matt", "Higger", "higger.m@northeastern.edu"),
        (257, "Wolfgang", "Gatterbauer", "gatterbauer.w@northeastern.edu"),
        (510, "Alan", "Mislove", "mislove.a@northeastern.edu"),
        (26, "Chris", "Amato", "amato.c@northeastern.edu"),
        (504, "Renee", "Miller", "miller.r@northeastern.edu"),
        (769, "Frank", "Tip", "tip.f@northeastern.edu"),
        (241, "Clark", "Freifeld", "freifeld.c@northeastern.edu"),
        (58, "Eli", "Barzilay", "barzilay.e@northeastern.edu"),
        (91, "Michelle", "Borkin", "borkin.m@northeastern.edu"),
        (92, "John", "Boyland", "boyland.j@northeastern.edu"),
        (195, "Kathleen", "Durant", "durant.k@northeastern.edu"),
        (807, "Ferdinand", "Vesely", "vesely.f@northeastern.edu"),
        (678, "Mike", "Shah", "shah.m@northeastern.edu"),
        (276, "Jacob", "Goldblum", "goldblum.j@northeastern.edu"),
        (79, "Priyanka", "Bishnoi", "bishnoi.p@northeastern.edu"),
        (850, "Lawson", "Wong", "wong.l@northeastern.edu"),
        (447, "Long", "Lu", "lu.l@northeastern.edu"),
        (359, "Holly", "Jimison", "jimison.h@northeastern.edu"),
        (57, "Jim", "Bartolotta", "bartolotta.j@northeastern.edu"),
        (29, "Ghita", "Amor-Tijani", "amortijani.g@northeastern.edu"),
        (782, "Stavros", "Trypakis", "trypakis.s@northeastern.edu"),
        (318, "Jason", "Hemann", "hemann.j@northeastern.edu"),
        (484, "Brianne", "McDonough", "mcdonough.b@northeastern.edu"),
        (612, "Aanjhan", "Ranganathan", "ranganathan.a@northeastern.edu"),
        (819, "Thomas", "Wahl", "wahl.t@northeastern.edu"),
        (593, "Rob", "Platt", "platt.r@northeastern.edu"),
        (668, "Cody", "Dunne", "dunne.c@northeastern.edu"),
        (607, "Rajmohan", "Rajaraman", "rajaraman.r@northeastern.edu"),
        (340, "Stephen", "Intille", "intille.s@northeastern.edu"),
        (140, "Jorio", "Cocola", "cocola.j@northeastern.edu"),
        (631, "Shari", "Robbins", "robbins.s@northeastern.edu"),
        (507, "Omid", "Mirzaei", "mirzaei.o@northeastern.edu"),
        (552, "Lucia", "Nunez", "nunez.l@northeastern.edu"),
        (595, "Adam", "Powell", "powell.a@northeastern.edu"),
        (465, "Marie", "Maloney", "maloney.m@northeastern.edu"),
        (66, "Kylie", "Bemis", "bemis.k@northeastern.edu"),
        (134, "Sophine", "Clachar", "clachar.s@northeastern.edu"),
        (209, "Ehsan", "Elhamifar", "elhamifar.e@northeastern.edu"),
        (576, "John", "Park", "park.j@northeastern.edu"),
        (739, "David", "Stalfa", "stalfa.d@northeastern.edu"),
        (76, "Timothy", "Bickmore", "bickmore.t@northeastern.edu"),
        (561, "Alina", "Oprea", "oprea.a@northeastern.edu"),
        (811, "Emanuele", "Viola", "viola.e@northeastern.edu"),
        (94, "David", "Brady", "brady.d@northeastern.edu"),
        (871, "Roi", "Yehoshua", "yehoshua.r@northeastern.edu"),
        (518, "Yasmil", "Montes", "montes.y@northeastern.edu"),
        (105, "Beth", "Callahan", "callahan.b@northeastern.edu"),
        (288, "Connor", "Guerin", "guerin.c@northeastern.edu"),
        (2, "Anis", "Abdulle", "abdulle.a@northeastern.edu"),
        (587, "Melissa", "Peikin", "peikin.m@northeastern.edu"),
        (147, "Gene", "Cooperman", "cooperman.g@northeastern.edu"),
        (544, "Huy", "Nguyen", "nguyen.h@northeastern.edu"),
        (178, "Peter", "Desnoyers", "desnoyers.p@northeastern.edu"),
        (751, "Ravi", "Sundaram", "sundaram.r@northeastern.edu"),
        (237, "Jill", "Forgash", "forgash.j@northeastern.edu"),
        (275, "Kevin", "Gold", "gold.k@northeastern.edu"),
        (824, "Mitchell", "Wand", "wand.m@northeastern.edu"),
        (342, "Austin", "Isaacson", "isaacson.a@northeastern.edu"),
        (278, "Matthew", "Goodwin", "goodwin.m@northeastern.edu"),
        (788, "Jonathan", "Ullman", "ullman.j@northeastern.edu"),
        (795, "Drew", "Van Der Poel", "vanderpoel.d@northeastern.edu"),
        (888, "Hongyang", "Zhang", "zhang.h@northeastern.edu"),
        (821, "Byron", "Wallace", "wallace.b@northeastern.edu"),
        (839, "Margaret", "Whitehead", "whitehead.m@northeastern.edu"),
        (146, "Seth", "Cooper", "cooper.s@northeastern.edu"),
        (794, "Jan-Willem", "Van De Meent", "vandemeent.j@northeastern.edu"),
        (666, "Walter", "Schnyder", "schnyder.w@northeastern.edu"),
        (702, "Jose", "Sierra", "sierra.j@northeastern.edu"),
        (646, "Joseph", "Rushanan", "rushanan.j@northeastern.edu"),
        (572, "Themis", "Papageorge", "papageorge.t@northeastern.edu"),
        (494, "Jorge", "Mex Perera", "mexperera.j@northeastern.edu"),
        (30, "Kevin", "Amorin", "amorin.k@northeastern.edu"),
        (90, "Elton", "Booker", "booker.e@northeastern.edu"),
        (215, "Abigail", "Evans", "evans.a@northeastern.edu"),
        (714, "Adrienne", "Slaughter", "slaughter.a@northeastern.edu"),
        (529, "Tony", "Mullen", "mullen.t@northeastern.edu"),
        (88, "Tamara", "Bonaci", "bonaci.t@northeastern.edu"),
        (354, "Drew", "Jelani", "jelani.d@northeastern.edu"),
        (184, "Alex", "Donaldson", "donaldson.a@northeastern.edu"),
        (155, "Brian", "Cross", "cross.b@northeastern.edu"),
        (117, "Raman", "Chandrasekar", "chandrasekar.r@northeastern.edu"),
        (128, "Bruce", "Chhay", "chhay.b@northeastern.edu"),
        (415, "Alexander", "Lash", "lash.a@northeastern.edu"),
        (613, "Vinayak", "Rao", "rao.v@northeastern.edu"),
        (367, "Austin", "Jorgensen", "jorgensen.a@northeastern.edu"),
        (750, "Zhifeng", "Sun", "sun.z@northeastern.edu"),
        (421, "Hyonho", "Lee", "lee.h@northeastern.edu"),
        (71, "Rahul", "Bhagat", "bhagat.r@northeastern.edu"),
        (473, "Craig", "Martell", "martell.c@northeastern.edu"),
        (10, "Everaldo", "Aguiar", "aguiar.e@northeastern.edu"),
        (493, "Francisco", "Mesch", "mesch.f@northeastern.edu"),
        (281, "Ian", "Gorton", "gorton.i@northeastern.edu"),
        (369, "Maria", "Jump", "jump.m@northeastern.edu"),
        (657, "Prasad", "Saripalli", "saripalli.p@northeastern.edu"),
        (36, "Sara", "Arunagiri", "arunagiri.s@northeastern.edu"),
        (503, "Mark", "Miller", "miller.m@northeastern.edu"),
        (768, "Jodi", "Tims", "tims.j@northeastern.edu"),
        (673, "Sarah", "Sellke", "sellke.s@northeastern.edu"),
        (345, "Hamid", "Jahanjou", "jahanjou.h@northeastern.edu"),
        (297, "Philip", "Gust", "gust.p@northeastern.edu"),
        (172, "Julien", "Delange", "delange.j@northeastern.edu"),
        (47, "Ricardo", "Baeza-Yates", "baezayates.r@northeastern.edu"),
        (5, "Mamoun", "Abu-Samaha", "abusamaha.m@northeastern.edu"),
        (74, "Anurag", "Bhardwaj", "bhardwaj.a@northeastern.edu"),
        (527, "Smruthi", "Mukund", "mukund.s@northeastern.edu"),
        (48, "Abraham", "Bagherjeiran", "bagherjeiran.a@northeastern.edu"),
        (21, "Omar", "Alonso", "alonso.o@northeastern.edu"),
        (126, "Zhuoqun", "Cheng", "cheng.z@northeastern.edu"),
        (64, "Jonathan", "Bell", "bell.j@northeastern.edu"),
        (203, "Bethany", "Edmunds", "edmunds.b@northeastern.edu"),
        (138, "Yvonne", "Coady", "coady.y@northeastern.edu"),
        (597, "Mirjana", "Prpa", "prpa.m@northeastern.edu"),
        (328, "Richard", "Hoshino", "hoshino.r@northeastern.edu"),
        (291, "Arjun", "Guha", "guha.a@northeastern.edu"),
        (111, "Smajl", "Cengic", "cengic.s@northeastern.edu"),
        (797, "Kathi", "Vander Laan", "vanderlaan.k@northeastern.edu"),
        (757, "Carmen", "Taglienti", "taglienti.c@northeastern.edu"),
        (695, "Ji-Yong", "Shin", "shin.j@northeastern.edu"),
        (543, "Robert", "Ness", "ness.r@northeastern.edu"),
        (672, "Ethan", "Selinger", "selinger.e@northeastern.edu"),
        (475, "Shivakumar", "Mathapathi", "mathapathi.s@northeastern.edu"),
        (771, "Alexandra", "To", "to.a@northeastern.edu"),
        (479, "Bruce", "Maxwell", "maxwell.b@northeastern.edu"),
        (792, "Scott", "Valcourt", "valcourt.s@northeastern.edu"),
        (14, "Michal", "Aibin", "aibin.m@northeastern.edu"),
        (840, "Daniel", "Wichs", "wichs.d@northeastern.edu"),
        (525, "Ab", "Mosca", "mosca.a@northeastern.edu"),
        (208, "Mohamed", "Elbehiry", "elbehiry.m@northeastern.edu"),
        (450, "Bowen", "Luo", "luo.b@northeastern.edu"),
        (886, "Cancan", "Zhang", "zhang.c@northeastern.edu"),
        (532, "Kereme", "Murrell", "murrell.k@northeastern.edu"),
        (322, "Victoria", "Hill", "hill.v@northeastern.edu"),
        (239, "Jamon", "Foster", "foster.j@northeastern.edu"),
        (735, "Taylor", "Sprague", "sprague.t@northeastern.edu"),
        (717, "Anna", "Sloan", "sloan.a@northeastern.edu"),
        (270, "Megan", "Giordano", "giordano.m@northeastern.edu"),
        (744, "Megan", "Strosnider", "strosnider.m@northeastern.edu"),
        (623, "Ali", "Ressing", "ressing.a@northeastern.edu"),
        (698, "Olin", "Shivers III", "shiversiii.o@northeastern.edu"),
        (813, "Jan", "Vitek", "vitek.j@northeastern.edu"),
        (468, "Pete", "Manolios", "manolios.p@northeastern.edu"),
        (814, "Olga", "Vitek", "vitek.o@northeastern.edu"),
        (732, "Hillary", "Spiritos", "spiritos.h@northeastern.edu"),
        (626, "Tyre", "Richards", "richards.t@northeastern.edu"),
        (249, "Ryan", "Gallagher", "gallagher.r@northeastern.edu"),
        (497, "Sakib", "Miazi", "miazi.s@northeastern.edu"),
        (175, "Utku", "Demir", "demir.u@northeastern.edu"),
        (78, "Jessica", "Biron", "biron.j@northeastern.edu"),
        (639, "Lauren", "Rosenberg", "rosenberg.l@northeastern.edu"),
        (448, "Celsey", "Lumbra", "lumbra.c@northeastern.edu"),
        (433, "Karl", "Lieberherr", "lieberherr.k@northeastern.edu"),
        (210, "Tina", "Eliassi-Rad", "eliassirad.t@northeastern.edu"),
        (560, "Kaan", "Onarlioglu", "onarlioglu.k@northeastern.edu"),
        (553, "Benjamin", "Nye", "nye.b@northeastern.edu"),
        (567, "Arianna", "Pagan", "pagan.a@northeastern.edu"),
        (317, "Charles", "Haycook", "haycook.c@northeastern.edu"),
        (472, "Stacy", "Marsella", "marsella.s@northeastern.edu"),
        (357, "Huaizu", "Jiang", "jiang.h@northeastern.edu"),
        (11, "Uzair", "Ahmad", "ahmad.u@northeastern.edu"),
        (758, "Cheng", "Tan", "tan.c@northeastern.edu"),
        (333, "Katie", "Hughes", "hughes.k@northeastern.edu"),
        (25, "Silvio", "Amir", "amir.s@northeastern.edu"),
        (310, "Paul", "Hand", "hand.p@northeastern.edu"),
        (75, "Adeel", "Bhutta", "bhutta.a@northeastern.edu"),
        (106, "Gary", "Cantrell", "cantrell.g@northeastern.edu"),
        (351, "Lindsay", "Jamieson", "jamieson.l@northeastern.edu"),
        (350, "Alan", "Jamieson", "jamieson.a@northeastern.edu"),
        (534, "Jonathan", "Mwaura", "mwaura.j@northeastern.edu"),
        (87, "Philip", "Bogden", "bogden.p@northeastern.edu"),
        (517, "Alvaro", "Monge", "monge.a@northeastern.edu"),
        (304, "Lama", "Hamandi", "hamandi.l@northeastern.edu"),
        (665, "Logan", "Schmidt", "schmidt.l@northeastern.edu"),
        (708, "Sarita", "Singh", "singh.s@northeastern.edu"),
        (122, "Divya", "Chaudhary", "chaudhary.d@northeastern.edu"),
        (680, "Vidhi", "Shah", "shah.v@northeastern.edu"),
        (148, "Lino", "Coria Mendoza", "coriamendoza.l@northeastern.edu"),
        (645, "Michael", "Running Wolf", "runningwolf.m@northeastern.edu"),
        (661, "Saiph", "Savage", "savage.s@northeastern.edu"),
        (300, "Brent", "Hailpern", "hailpern.b@northeastern.edu"),
        (377, "Prathibha", "Kasaragod", "kasaragod.p@northeastern.edu"),
        (180, "Kevin", "Dill", "dill.k@northeastern.edu"),
        (608, "Vishal", "Rajpal", "rajpal.v@northeastern.edu"),
        (515, "Aanchan", "Mohan", "mohan.a@northeastern.edu"),
        (571, "Kaushal", "Paneri", "paneri.k@northeastern.edu"),
        (326, "Steven", "Holtzen", "holtzen.s@northeastern.edu"),
        (841, "John", "Wilder", "wilder.j@northeastern.edu"),
        (775, "Mohammad", "Toutiaee", "toutiaee.m@northeastern.edu"),
        (204, "Timothy", "Edmunds", "edmunds.t@northeastern.edu"),
        (179, "Samantha", "DiCanio", "dicanio.s@northeastern.edu"),
        (72, "Rasika", "Bhalerao", "bhalerao.r@northeastern.edu"),
        (220, "Maryam", "Farahmand Asil", "farahmandasil.m@northeastern.edu"),
        (40, "Amin", "Assareh", "assareh.a@northeastern.edu"),
        (741, "Amy", "Starzec", "starzec.a@northeastern.edu"),
        (583, "Daniel", "Patterson", "patterson.d@northeastern.edu"),
        (889, "Shuo", "Zhang", "zhang.s@northeastern.edu"),
        (554, "Elizabeth", "O'Reilly", "oreilly.e@northeastern.edu"),
        (264, "Fatemeh", "Ghoreishi", "ghoreishi.f@northeastern.edu"),
        (236, "Mark", "Fontenot", "fontenot.m@northeastern.edu"),
        (422, "Jeongkyu", "Lee", "lee.j@northeastern.edu"),
        (685, "Ali", "Sharifian Attar", "sharifianattar.a@northeastern.edu"),
        (383, "Justin", "Kennedy", "kennedy.j@northeastern.edu"),
        (828, "Justin", "Wang", "wang.j@northeastern.edu"),
        (268, "Nabeel", "Gillani", "gillani.n@northeastern.edu"),
        (789, "Ata Aydin", "Uslu", "uslu.a@northeastern.edu"),
        (366, "Matthew", "Jones", "jones.m@northeastern.edu"),
        (761, "Ben", "Tasker", "tasker.b@northeastern.edu"),
        (667, "Garrett", "Schwab", "schwab.g@northeastern.edu"),
        (55, "Rachel", "Bargoot", "bargoot.r@northeastern.edu"),
        (617, "Olivia", "Raykovich", "raykovich.o@northeastern.edu"),
        (60, "Madison", "Bavasso", "bavasso.m@northeastern.edu"),
        (286, "Alexander", "Grob", "grob.a@northeastern.edu"),
        (68, "Keatyn", "Bergsten", "bergsten.k@northeastern.edu"),
        (85, "L.", "Boco", "boco.l@northeastern.edu"),
        (691, "Chord", "Sheriffe", "sheriffe.c@northeastern.edu"),
        (763, "Taryn", "Tessari", "tessari.t@northeastern.edu"),
        (168, "Bob", "De Schutter", "deschutter.b@northeastern.edu"),
        (822, "Robin", "Walters", "walters.r@northeastern.edu"),
        (153, "Kathleen", "Creel", "creel.k@northeastern.edu"),
        (509, "Varun", "Mishra", "mishra.v@northeastern.edu"),
        (59, "David", "Bau", "bau.d@northeastern.edu"),
        (549, "Guevara", "Noubir", "noubir.g@northeastern.edu"),
        (600, "Hong", "Qu", "qu.h@northeastern.edu"),
        (150, "Armando", "Cortez", "cortez.a@northeastern.edu"),
        (176, "Mahsa", "Derakhshan", "derakhshan.m@northeastern.edu"),
        (658, "Aarti", "Sathyanarayana", "sathyanarayana.a@northeastern.edu"),
        (259, "Eric", "Gerber", "gerber.e@northeastern.edu"),
        (802, "Oscar", "Veliz", "veliz.o@northeastern.edu"),
        (726, "Hosung", "Song", "song.h@northeastern.edu"),
        (89, "Mark", "Bonicillo", "bonicillo.m@northeastern.edu"),
        (855, "Ming-Chuan", "Wu", "wu.m@northeastern.edu"),
        (16, "Mona", "Ali", "ali.mo@northeastern.edu"),
        (766, "Jack", "Thomas", "thomas.j@northeastern.edu"),
        (121, "Neda", "Changizi", "changizi.n@northeastern.edu"),
        (602, "Ryan", "Rad", "rad.r@northeastern.edu"),
        (810, "Weston", "Viles", "viles.w@northeastern.edu"),
        (139, "Richard", "Cobbe", "cobbe.r@northeastern.edu"),
        (832, "Susan", "Wang", "wang.s@northeastern.edu"),
        (731, "Ellen", "Spertus", "spertus.e@northeastern.edu"),
        (437, "Albert", "Lionelle", "lionelle.a@northeastern.edu"),
        (70, "Enrico", "Bertini", "bertini.e@northeastern.edu"),
        (258, "Domingo", "Genao", "genao.d@northeastern.edu"),
        (857, "Allen", "Xiao", "xiao.a@northeastern.edu"),
        (401, "Almudena", "Konrad", "konrad.a@northeastern.edu"),
        (555, "Robert", "Oboko", "oboko.r@northeastern.edu"),
        (398, "Jane", "Kokernak", "kokernak.j@northeastern.edu"),
        (579, "Seth", "Pate", "pate.s@northeastern.edu"),
        (62, "Soheil", "Behnezhad", "behnezhad.s@northeastern.edu"),
        (474, "Chris", "Martens", "martens.c@northeastern.edu"),
        (490, "Erika", "Melder", "melder.e@northeastern.edu"),
        (539, "Arasu", "Narayan", "narayan.a@northeastern.edu"),
        (245, "Miguel", "Fuentes-Cabrera", "fuentescabrera.m@northeastern.edu"),
        (199, "Brianna", "Dym", "dym.b@northeastern.edu"),
        (125, "Rongyi", "Chen", "chen.r@northeastern.edu"),
        (371, "Youna", "Jung", "jung.y@northeastern.edu"),
        (151, "Kyle", "Courtney", "courtney.k@northeastern.edu"),
        (682, "Chantal", "Shaib", "shaib.c@northeastern.edu"),
        (91361, "LaKyah", "Tyner", "tyner.l@northeastern.edu"),
        (223, "Sina", "Fazel-pour", "fazelpour.s@northeastern.edu"),
        (804, "Rajagopal", "Venkatesaramani",
         "venkatesaramani.r@northeastern.edu"),
        (324, "Megan", "Hofmann", "hofmann.m@northeastern.edu"),
        (724, "Katherine", "Socha", "socha.k@northeastern.edu"),
        (51, "Jordan", "Ballantyne", "ballantyne.j@northeastern.edu"),
        (636, "Sami", "Rollins", "rollins.s@northeastern.edu"),
        (853, "Chieh", "Wu", "wu.c@northeastern.edu"),
        (783, "Iraklis", "Tsekourakis", "tsekourakis.i@northeastern.edu"),
        (307, "Ariel", "Hamlin", "hamlin.a@northeastern.edu"),
        (791, "Gregory", "Valcourt", "valcourt.g@northeastern.edu"),
        (875, "Yi", "Yin", "yin.y@northeastern.edu"),
        (445, "Nunzio", "Lore", "lore.n@northeastern.edu"),
        (152, "Radha", "Coutinho", "coutinho.r@northeastern.edu"),
        (867, "Xiaoyi", "Yang", "yang.x@northeastern.edu"),
        (298, "Benjamin", "Gyori", "gyori.b@northeastern.edu"),
        (82, "Vance", "Blankers", "blankers.v@northeastern.edu"),
        (173, "Sara", "Dell", "dell.s@northeastern.edu"),
        (508, "Aditya", "Mishra", "mishra.a@northeastern.edu"),
        (28, "Tehmina", "Amjad", "amjad.t@northeastern.edu"),
        (648, "Nadim", "Saad", "saad.n@northeastern.edu"),
        (87957, "Mohammad", "Saneian", "saneian.m@northeastern.edu"),
        (523, "Steve", "Morin", "morin.s@northeastern.edu"),
        (692, "Marcus", "Sherman", "sherman.m@northeastern.edu"),
        (22, "Greg", "Aloupis", "aloupis.g@northeastern.edu"),
        (512, "Prashant", "Mittal", "mittal.p@northeastern.edu"),
        (15, "Ildar", "Akhmetov", "akhmetov.i@northeastern.edu"),
        (101, "Juancho", "Buchanan", "buchanan.j@northeastern.edu"),
        (588, "Cristian", "Penarrieta", "penarrieta.c@northeastern.edu"),
        (760, "Maryam", "Tanha", "tanha.m@northeastern.edu"),
        (265, "Avijit", "Ghosh", "ghosh.a@northeastern.edu"),
        (84, "Ryan", "Bockmon", "bockmon.r@northeastern.edu"),
        (655, "Piotr", "Sapiezynski", "sapiezynski.p@northeastern.edu"),
        (545, "Karl", "Ni", "ni.k@northeastern.edu"),
        (426, "Ada", "Lerner", "lerner.a@northeastern.edu"),
        (540, "Mario", "Nascimento", "nascimento.m@northeastern.edu"),
        (412, "Wallace", "Lages", "lages.w@northeastern.edu"),
        (61, "Akram", "Bayat", "bayat.a@northeastern.edu"),
        (77, "Elettra", "Bietti", "bietti.e@northeastern.edu"),
        (201, "Laura", "Edelson", "edelson.l@northeastern.edu"),
        (825, "Dakuo", "Wang", "wang.d@northeastern.edu"),
        (511, "Joydeep", "Mitra", "mitra.j@northeastern.edu"),
        (565, "Lace", "Padilla", "padilla.l@northeastern.edu"),
        (550, "Beth", "Noveck", "noveck.b@northeastern.edu"),
        (98424, "David", "Fields", "fields.d@northeastern.edu"),
        (133, "Kenneth", "Church", "church.k@northeastern.edu"),
        (644, "Ning", "Rui", "rui.n@northeastern.edu"),
        (675, "Steve", "Shafer", "shafer.s@northeastern.edu"),
        (18, "Malihe", "Alikhani", "alikhani.m@northeastern.edu"),
        (183, "Molly", "Domino", "domino.m@northeastern.edu"),
        (100311, "Sandy", "Ganzell", "ganzell.s@northeastern.edu"),
        (77848, "Carter", "Ithier", "ithier.c@northeastern.edu"),
        (388, "Tala", "Talaei Khoei", "talaeikhoei.t@northeastern.edu"),
        (79378, "James", "Kim", "kim.j@northeastern.edu"),
        (98323, "Kai Yee", "Wan", "wan.k@northeastern.edu"),
        (100314, "Jesse", "Stern", "stern.j@northeastern.edu"),
        (78897, "Diptendu", "Kar", "kar.d@northeastern.edu"),
        (97099, "Fatema", "Nafa", "nafa.f@northeastern.edu"),
        (99361, "Ernest", "Mauristhene", "mauristhene.e@northeastern.edu"),
        (100309, "Rose", "Sloan", "sloan.r@northeastern.edu"),
        (100306, "Huihui", "Wang", "wang.h@northeastern.edu"),
        (100307, "Mohit", "Singhal", "singhal.m@northeastern.edu"),
        (849, "Barry", "Wolfield", "wolfield.b@northeastern.edu"),
        (100308, "Deahan", "Yu", "yu.d@northeastern.edu"),
        (100310, "Crane", "Chen", "chen.c@northeastern.edu"),
        (99402, "Ilmi", "Yoon", "yoon.i@northeastern.edu"),
        (80249, "V", "Lange", "lange.v@northeastern.edu"),
        (102190, "Matt", "Bornstein", "bornstein.m@northeastern.edu"),
        (99379, "Hazra", "Imran", "imran.h@northeastern.edu"),
        (102128, "Saeed", "Yazdanian", "yazdanian.s@northeastern.edu"),
        (101895, "Parsa", "Rajabi", "rajabi.p@northeastern.edu"),
        (654, "Rush", "Sanghrajka", "sanghrajka.r@northeastern.edu"),
        (98609, "Brian", "Hanley", "hanley.b@northeastern.edu"),
        (216, "Michael", "Everett", "everett.m@northeastern.edu"),
        (799, "Akshar", "Varma", "varma.a@northeastern.edu"),
        (162, "Maitraye", "Das", "das.m@northeastern.edu"),
        (207, "Mai", "ElSherif", "elsherif.m@northeastern.edu"),
        (403, "Maciej", "Kos", "kos.m@northeastern.edu"),
        (271, "Adina", "Gitomer", "gitomer.a@northeastern.edu"),
        (100213, "Abir", "Saha", "saha.a@northeastern.edu"),
        (918, "Mardiros", "Merdinian", "merdinian.m@northeastern.edu"),
        (100313, "Chris", "Geeng", "geeng.c@northeastern.edu"),
        (97101, "Florin", "Bidian", "bidian.f@northeastern.edu"),
        (752, "Shanu", "Sushmita", "sushmita.s@northeastern.edu"),
        (100312, "Yifan", "Hu", "hu.y@northeastern.edu"),
        (713, "Theo", "Skoteiniotis", "skoteiniotis.t@northeastern.edu"),
        (97869, "Ahmed", "Ibrahim", "ibrahim.a@northeastern.edu"),
        (102230, "Anwar", "Mamat", "mamat.a@northeastern.edu"),
        (70869, "Ashish", "Bulchandani", "bulchandani.a@northeastern.edu"),
        (277, "Alex", "Gonzalez", "gonzalez.a@northeastern.edu"),
        (98578, "Mohammad", "Selim", "selim.m@northeastern.edu"),
        (98322, "Mais", "Nijim", "nijim.m@northeastern.edu"),
        (759, "Zhi", "Tan", "tan.z@northeastern.edu"),
        (97944, "Amir", "Tahmasebi Maraghoosh",
         "tahmasebimaraghoosh.a@northeastern.edu"),
        (97982, "Jin", "Yu", "yu.j@northeastern.edu"),
        (334, "Aaron", "Hunter", "hunter.a@northeastern.edu"),
        (39, "Javed", "Aslam", "aslam.j@northeastern.edu"),
        (100304, "Ziming", "Zhao", "zhao.z@northeastern.edu"),
        (98850, "Saeed", "Amal", "amal.s@northeastern.edu"),
        (101168, "Joshua", "Gancher", "gancher.j@northeastern.edu"),
        (431, "Tianshi", "Li", "li.t@northeastern.edu"),
        (694, "Weiyan", "Shi", "shi.w@northeastern.edu"),
        (360, "Zhengzhong", "Jin", "jin.z@northeastern.edu"),
        (98851, "Hessam", "Mahdavifar", "mahdavifar.h@northeastern.edu"),
        (461, "Meica", "Magnani", "magnani.m@northeastern.edu"),
        (170, "Michael Ann", "DeVito", "devito.m@northeastern.edu"),
        (107221, "Jia", "Zhu", "zhu.j@northeastern.edu"),
        (103762, "Lothar", "Narins", "narins.l@northeastern.edu"),
        (103036, "Joseph", "Reilly", "reilly.j@northeastern.edu"),
        (107652, "Eunji", "Lee", "lee.e@northeastern.edu"),
        (103617, "Xiang", "Ren", "ren.x@northeastern.edu"),
        (103635, "Gabriela", "Gongora Svartzman",
         "gongorasvartzman.g@northeastern.edu"),
        (103781, "Geoffrey", "Phipps", "phipps.g@northeastern.edu"),
        (101544, "Jessica", "Staddon", "staddon.j@northeastern.edu"),
        (97752, "Steve", "Schmidt", "schmidt.s@northeastern.edu"),
        (103767, "Heather", "Wilkerson", "wilkerson.h@northeastern.edu"),
        (100305, "Elizabeth", "Hawthorne", "hawthorne.e@northeastern.edu"),
        (94372, "Hye Sun", "Yun", "yun.h@northeastern.edu"),
        (107603, "Clare", "Martin", "martin.c@northeastern.edu"),
        (102969, "David", "Albanese", "albanese.d@northeastern.edu"),
        (102650, "Seth", "Hutchinson", "hutchinson.s@northeastern.edu"),
        (102225, "Wengong", "Jin", "jin.w@northeastern.edu"),
        (487, "Kayla", "McLaughlin", "mclaughlin.k@northeastern.edu"),
        (102057, "Prashant", "Pandey", "pandey.p@northeastern.edu"),
        (106382, "Lunjia", "Hu", "hu.l@northeastern.edu"),
        (684, "Aida", "Sharif Rohani", "sharifrohani.a@northeastern.edu"),
        (104247, "Wendy", "Truran", "truran.w@northeastern.edu"),
        (93202, "Si", "Wu", "wu.s@northeastern.edu"),
        (104468, "Terra", "Blevins", "blevins.t@northeastern.edu"),
        (80, "Meredith", "Bittrich", "bittrich.m@northeastern.edu"),
        (458, "Rebecca", "MacKenzie", "mackenzie.r@northeastern.edu"),
        (261, "Mojgan", "Ghasemi", "ghasemi.m@northeastern.edu"),
        (95, "Taylor", "Braswell", "braswell.t@northeastern.edu"),
        (424, "Shun-Yang", "Lee", "lee.s@northeastern.edu"),
        (541, "Farzaneh", "Nekui", "nekui.f@northeastern.edu"),
        (313, "Woodrow", "Hartzog", "hartzog.w@northeastern.edu"),
        (386, "Amin", "Kharraz", "kharraz.a@northeastern.edu"),
        (835, "Michael", "Weintraub", "weintraub.m@northeastern.edu"),
        (881, "Qi", "Yu", "yu.q@northeastern.edu"),
        (830, "Lu", "Wang", "wang.l@northeastern.edu"),
        (338, "Tales", "Imbiriba", "imbiriba.t@northeastern.edu"),
        (568, "Felipe", "Pait", "pait.f@northeastern.edu"),
        (110, "Dylan", "Cashman", "cashman.d@northeastern.edu"),
        (189, "Brecia", "Douglas", "douglas.b@northeastern.edu"),
        (102, "Joseph", "Buck", "buck.j@northeastern.edu"),
        (31, "Erik", "Anderson", "anderson.e@northeastern.edu"),
        (218, "Ahmed", "Ezzat", "ezzat.a@northeastern.edu"),
        (704, "Matthew", "Simonson", "simonson.m@northeastern.edu"),
        (718, "Kevin", "Small", "small.k@northeastern.edu"),
        (462, "Aanchal", "Malhotra", "malhotra.a@northeastern.edu"),
        (306, "CJ", "Hameed", "hameed.c@northeastern.edu"),
        (642, "Monique", "Roth", "roth.m@northeastern.edu"),
        (325, "Kevin", "Holt", "holt.k@northeastern.edu"),
        (381, "Thomas", "Kelley", "kelley.t@northeastern.edu"),
        (632, "Ronald", "Robertson", "robertson.r@northeastern.edu"),
        (842, "Ryan", "Williams", "williams.r@northeastern.edu"),
        (833, "Yanzhi", "Wang", "wang.y@northeastern.edu"),
        (746, "Philip", "Su", "su.p@northeastern.edu"),
        (864, "Natasha", "Yamane", "yamane.n@northeastern.edu"),
        (221, "Andrew", "Fasano", "fasano.a@northeastern.edu"),
        (392, "David", "Klee", "klee.d@northeastern.edu"),
        (1, "Mania", "Abdi", "abdi.m@northeastern.edu"),
        (476, "Ted", "Matherly", "matherly.t@northeastern.edu"),
        (838, "Samuel", "Westby", "westby.s@northeastern.edu"),
        (812, "Amanda", "Vispo", "vispo.a@northeastern.edu"),
        (228, "Sam", "Ferguson", "ferguson.s@northeastern.edu"),
        (634, "Clifton", "Robinson", "robinson.c@northeastern.edu"),
        (229, "Zlatan", "Feric", "feric.z@northeastern.edu"),
        (723, "Wayne", "Snyder", "snyder.w@northeastern.edu"),
        (754, "Uzma Haque", "Syeda", "syeda.u@northeastern.edu"),
        (590, "James", "Perretta", "perretta.j@northeastern.edu"),
        (729, "Laura", "South", "south.l@northeastern.edu"),
        (736, "Steven", "Sprecher", "sprecher.s@northeastern.edu"),
        (69, "Kai", "Bernardini", "bernardini.k@northeastern.edu"),
        (35, "Adam", "Anthony", "anthony.a@northeastern.edu"),
        (187, "Karen", "Donoghue", "donoghue.k@northeastern.edu"),
        (908, "Samuel", "Caldwell", "caldwell.s@northeastern.edu"),
        (127, "Chenyan", "Jia", "jia.c@northeastern.edu"),
        (97112, "Damian", "Isla", "isla.d@northeastern.edu"),
        (440, "David", "Liu", "liu.d@northeastern.edu"),
        (86996, "Anita", "Rathi", "rathi.a@northeastern.edu"),
        (98078, "Jiaji", "Huang", "huang.j@northeastern.edu"),
        (302, "John", "Halamka", "halamka.j@northeastern.edu"),
        (651, "Herman", "Saksono", "saksono.h@northeastern.edu"),
        (97367, "Or", "Katz", "katz.o@northeastern.edu"),
        (336, "Rania", "Hussein", "hussein.r@northeastern.edu"),
        (98425, "Yeh-cheng", "Chen", "chen.y@northeastern.edu"),
        (98675, "Marc", "Meyer", "meyer.m@northeastern.edu"),
        (98505, "Rushil", "Khurana", "khurana.r@northeastern.edu"),
        (589, "Jose", "Perea Benitez", "pereabenitez.j@northeastern.edu"),
        (393, "Rebecca", "Kleinberger", "kleinberger.r@northeastern.edu"),
        (87833, "Ryon", "Sajnovsky", "sajnovsky.r@northeastern.edu"),
        (103977, "Maral", "Azizi", "azizi.m@northeastern.edu"),
        (102691, "Bruno", "Nardone", "nardone.b@northeastern.edu"),
        (102708, "Amy", "Pei", "pei.a@northeastern.edu"),
        (102709, "Allison", "Wan", "wan.a@northeastern.edu"),
        (69647, "Michael", "Ballantyne", "ballantyne.m@northeastern.edu"),
        (103564, "Tomer", "Lancewicki", "lancewicki.t@northeastern.edu"),
        (243, "Kevin", "Fu", "fu.k@northeastern.edu"),
        (69402, "Katherine", "Atwell", "atwell.k@northeastern.edu"),
        (109204, "Jerome", "Braun", "braun.j@northeastern.edu"),
        (108913, "Mina", "Park", "park.m@northeastern.edu"),
        (884, "Rached", "Zantout", "zantout.r@northeastern.edu"),
        (104443, "Rob", "Simmons", "simmons.r@northeastern.edu"),
        (108302, "Paul", "Tymann", "tymann.p@northeastern.edu"),
        (82955, "Philip", "Mathieu", "mathieu.p@northeastern.edu"),
        (419, "Christopher", "Le Dantec", "ledantec.c@northeastern.edu"),
        (88482, "Zohair", "Shafi", "shafi.z@northeastern.edu"),
        (90008, "Samuel", "Stites", "stites.s@northeastern.edu"),
        (102312, "Leah", "Rosenbloom", "rosenbloom.l@northeastern.edu"),
        (109140, "Daniel", "VanBelleghem", "vanbelleghem.d@northeastern.edu"),
        (107548, "Lorenzo", "Torresani", "torresani.l@northeastern.edu"),
        (109244, "Vikrant", "Nanda", "nanda.v@northeastern.edu"),
        (109205, "Chantelle", "Recsky", "recsky.c@northeastern.edu"),
        (109234, "Ariana", "Brody", "brody.a@northeastern.edu"),
        (410, "Timothy", "LaRock", "larock.t@northeastern.edu"),
        (118, "Pandurangan", "Chandrasekaran",
         "chandrasekaran.p@northeastern.edu"),
        (390, "Lucianna", "Kiffer", "kiffer.l@northeastern.edu"),
        (96, "Nicole", "Brewer", "brewer.n@northeastern.edu"),
        (748, "Ruimin", "Sun", "sun.r@northeastern.edu"),
        (323, "Ally", "Hoffman", "hoffman.a@northeastern.edu"),
        (823, "Michael", "Wan", "wan.m@northeastern.edu"),
        (787, "Nikolaos", "Tziavelis", "tziavelis.n@northeastern.edu"),
        (98629, "Pierre", "Donat-Bouillud", "donatbouillud.p@northeastern.edu"),
        (92723, "Benjamin", "Weintraub", "weintraub.b@northeastern.edu"),
        (292, "Kumaraguru", "Guhan", "guhan.k@northeastern.edu"),
        (129, "Patrick", "Chidsey", "chidsey.p@northeastern.edu"),
        (569, "Hari Prasath", "Palani", "palani.h@northeastern.edu"),
        (877, "Gary", "Young", "young.g@northeastern.edu"),
        (17, "Muhammad", "Ali", "ali.mu@northeastern.edu"),
        (13, "Bilal", "Ahmed", "ahmed.b@northeastern.edu"),
        (365, "Chiew", "Jones", "jones.c@northeastern.edu"),
        (70108, "Maxwell", "Bernstein", "bernstein.m@northeastern.edu"),
        (75064, "Racquel", "Fygenson", "fygenson.r@northeastern.edu"),
        (75173, "Kutub", "Gandhi", "gandhi.k@northeastern.edu"),
        (89211, "Fiona", "Shyne", "shyne.f@northeastern.edu"),
        (41, "Kathleen", "Aubrey", "aubrey.k@northeastern.edu"),
        (764, "Andrew", "Therriault", "therriault.a@northeastern.edu"),
        (348, "Shantanu", "Jain", "jain.s@northeastern.edu"),
        (364, "Reid", "Johnson", "johnson.r@northeastern.edu"),
        (442, "Neal", "Livesay", "livesay.n@northeastern.edu"),
        (671, "Jennifer", "Seitzer", "seitzer.j@northeastern.edu"),
        (619, "Ronak", "Razavisousan", "razavisousan.r@northeastern.edu"),
        (738, "Athicha", "Srivirote", "srivirote.a@northeastern.edu"),
        (979, "Sommer", "Harris", "harris.s@northeastern.edu"),
        (98859, "Marko", "Puljic", "puljic.m@northeastern.edu"),
        (88858, "Jim", "Sheldon", "sheldon.j@northeastern.edu"),
        (99020, "Viney", "Ugave", "ugave.v@northeastern.edu"),
        (72067, "Zixuan", "Chen", "chen.z@northeastern.edu"),
    ]
    faculty_list = [
        Faculty(
            nuid=d[0],
            first_name=d[1],
            last_name=d[2],
            email=d[3],
            campus=boston.campus_id,
            active=True,
        )
        for d in _faculty_data
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
        TimeBlock(time_block_id=1, meeting_days="T", start_time=time(
            11, 45), end_time=time(13, 25), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=2, meeting_days="R", start_time=time(
            14, 50), end_time=time(16, 30), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=3, meeting_days="M", start_time=time(
            8, 00), end_time=time(10, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=4, meeting_days="M", start_time=time(
            8, 30), end_time=time(10, 30), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=5, meeting_days="M", start_time=time(
            9, 00), end_time=time(12, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=6, meeting_days="M", start_time=time(
            9, 15), end_time=time(10, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=7, meeting_days="M", start_time=time(
            10, 00), end_time=time(12, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=8, meeting_days="M", start_time=time(
            10, 30), end_time=time(11, 35), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=9, meeting_days="M", start_time=time(
            10, 45), end_time=time(12, 45), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=10, meeting_days="M", start_time=time(
            11, 45), end_time=time(13, 25), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=11, meeting_days="M", start_time=time(
            13, 00), end_time=time(15, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=12, meeting_days="M", start_time=time(
            13, 35), end_time=time(14, 40), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=13, meeting_days="M", start_time=time(
            13, 00), end_time=time(16, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=14, meeting_days="M", start_time=time(
            14, 00), end_time=time(16, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=15, meeting_days="M", start_time=time(
            14, 50), end_time=time(16, 30), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=16, meeting_days="M", start_time=time(
            14, 00), end_time=time(17, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=17, meeting_days="M", start_time=time(
            15, 15), end_time=time(17, 15), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=18, meeting_days="M", start_time=time(
            16, 35), end_time=time(17, 40), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=19, meeting_days="M", start_time=time(
            17, 00), end_time=time(19, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=20, meeting_days="M", start_time=time(
            17, 30), end_time=time(19, 30), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=21, meeting_days="M", start_time=time(
            18, 00), end_time=time(19, 40), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=22, meeting_days="M", start_time=time(
            18, 00), end_time=time(21, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=23, meeting_days="M", start_time=time(
            18, 00), end_time=time(21, 15), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=24, meeting_days="M", start_time=time(
            18, 00), end_time=time(21, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=25, meeting_days="M", start_time=time(
            19, 00), end_time=time(21, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=26, meeting_days="M", start_time=time(
            19, 45), end_time=time(21, 45), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=27, meeting_days="T", start_time=time(
            8, 00), end_time=time(9, 40), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=28, meeting_days="T", start_time=time(
            9, 00), end_time=time(12, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=29, meeting_days="T", start_time=time(
            9, 50), end_time=time(11, 30), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=30, meeting_days="T", start_time=time(
            13, 00), end_time=time(16, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=31, meeting_days="T", start_time=time(
            13, 35), end_time=time(15, 15), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=32, meeting_days="T", start_time=time(
            14, 00), end_time=time(17, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=33, meeting_days="T", start_time=time(
            15, 25), end_time=time(17, 5), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=34, meeting_days="T", start_time=time(
            18, 00), end_time=time(21, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=35, meeting_days="T", start_time=time(
            18, 00), end_time=time(21, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=36, meeting_days="W", start_time=time(
            8, 00), end_time=time(9, 5), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=37, meeting_days="W", start_time=time(
            9, 15), end_time=time(10, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=38, meeting_days="W", start_time=time(
            10, 30), end_time=time(11, 35), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=39, meeting_days="W", start_time=time(
            13, 35), end_time=time(14, 40), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=40, meeting_days="W", start_time=time(
            14, 00), end_time=time(17, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=41, meeting_days="W", start_time=time(
            16, 35), end_time=time(17, 40), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=42, meeting_days="W", start_time=time(
            18, 00), end_time=time(21, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=43, meeting_days="W", start_time=time(
            18, 00), end_time=time(21, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=44, meeting_days="R", start_time=time(
            8, 00), end_time=time(9, 40), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=45, meeting_days="R", start_time=time(
            9, 50), end_time=time(11, 30), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=46, meeting_days="R", start_time=time(
            9, 00), end_time=time(12, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=47, meeting_days="R", start_time=time(
            13, 00), end_time=time(16, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=48, meeting_days="R", start_time=time(
            13, 35), end_time=time(15, 15), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=49, meeting_days="R", start_time=time(
            15, 25), end_time=time(17, 5), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=50, meeting_days="R", start_time=time(
            18, 00), end_time=time(21, 15), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=51, meeting_days="R", start_time=time(
            18, 00), end_time=time(21, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=52, meeting_days="R", start_time=time(
            18, 00), end_time=time(21, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=53, meeting_days="R", start_time=time(
            14, 00), end_time=time(17, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=54, meeting_days="F", start_time=time(
            8, 00), end_time=time(10, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=55, meeting_days="F", start_time=time(
            8, 30), end_time=time(10, 30), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=56, meeting_days="F", start_time=time(
            9, 00), end_time=time(12, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=57, meeting_days="F", start_time=time(
            9, 50), end_time=time(11, 30), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=58, meeting_days="F", start_time=time(
            10, 00), end_time=time(12, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=59, meeting_days="F", start_time=time(
            10, 45), end_time=time(12, 45), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=60, meeting_days="F", start_time=time(
            11, 45), end_time=time(13, 25), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=61, meeting_days="F", start_time=time(
            13, 00), end_time=time(15, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=62, meeting_days="F", start_time=time(
            13, 35), end_time=time(15, 15), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=63, meeting_days="F", start_time=time(
            13, 00), end_time=time(16, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=64, meeting_days="F", start_time=time(
            14, 00), end_time=time(16, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=65, meeting_days="F", start_time=time(
            14, 00), end_time=time(17, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=66, meeting_days="F", start_time=time(
            15, 15), end_time=time(17, 15), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=67, meeting_days="F", start_time=time(
            15, 25), end_time=time(17, 5), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=68, meeting_days="F", start_time=time(
            17, 00), end_time=time(19, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=69, meeting_days="F", start_time=time(
            17, 30), end_time=time(19, 30), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=70, meeting_days="F", start_time=time(
            18, 00), end_time=time(21, 15), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=71, meeting_days="F", start_time=time(
            18, 00), end_time=time(21, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=72, meeting_days="F", start_time=time(
            19, 00), end_time=time(21, 00), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=73, meeting_days="F", start_time=time(
            19, 45), end_time=time(21, 45), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=74, meeting_days="MW", start_time=time(
            14, 50), end_time=time(16, 30), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=75, meeting_days="MR", start_time=time(
            11, 45), end_time=time(13, 25), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=76, meeting_days="MWR", start_time=time(
            8, 00), end_time=time(9, 5), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=77, meeting_days="MWR", start_time=time(
            9, 15), end_time=time(10, 20), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=78, meeting_days="MWR", start_time=time(
            10, 30), end_time=time(11, 35), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=79, meeting_days="MWR", start_time=time(
            13, 35), end_time=time(14, 40), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=80, meeting_days="MWR", start_time=time(
            16, 35), end_time=time(17, 40), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=81, meeting_days="TF", start_time=time(
            8, 00), end_time=time(9, 40), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=82, meeting_days="TF", start_time=time(
            9, 50), end_time=time(11, 30), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=83, meeting_days="TF", start_time=time(
            13, 35), end_time=time(15, 15), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=84, meeting_days="TF", start_time=time(
            15, 25), end_time=time(17, 5), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=85, meeting_days="WF", start_time=time(
            11, 45), end_time=time(13, 25), campus=boston.campus_id, block_group=None),
        TimeBlock(time_block_id=86, meeting_days="WF", start_time=time(
            8, 45), end_time=time(10, 25), campus=boston.campus_id, block_group=None),
    ]

    db.add_all(time_blocks)
    db.flush()

    # ------------------------------------------------------------------
    # Schedule
    # ------------------------------------------------------------------
    past_semesters = [
        Semester(semester_id=1,  season="Fall",
                 year=2020, active=False),
        Semester(semester_id=2,  season="Fall",
                 year=2021, active=False),
        Semester(semester_id=3,  season="Fall",
                 year=2022, active=False),
        Semester(semester_id=4,  season="Fall",
                 year=2023, active=False),
        Semester(semester_id=5,  season="Fall",
                 year=2024, active=False),
        Semester(semester_id=6,  season="Fall",
                 year=2025, active=False),
        Semester(semester_id=7,  season="Spring",
                 year=2020, active=False),
        Semester(semester_id=8,  season="Spring",
                 year=2021, active=False),
        Semester(semester_id=9,  season="Spring",
                 year=2022, active=False),
        Semester(semester_id=10, season="Spring",
                 year=2023, active=False),
        Semester(semester_id=11, season="Spring",
                 year=2024, active=False),
        Semester(semester_id=12, season="Spring",
                 year=2025, active=False),
        Semester(semester_id=13, season="Spring",
                 year=2026, active=False),
        Semester(semester_id=14, season="Summer 1",
                 year=2020, active=False),
        Semester(semester_id=15, season="Summer 1",
                 year=2021, active=False),
        Semester(semester_id=16, season="Summer 1",
                 year=2022, active=False),
        Semester(semester_id=17, season="Summer 1",
                 year=2023, active=False),
        Semester(semester_id=18, season="Summer 1",
                 year=2024, active=False),
        Semester(semester_id=19, season="Summer 1",
                 year=2025, active=False),
        Semester(semester_id=20, season="Summer 1",
                 year=2026, active=False),
        Semester(semester_id=21, season="Summer 2",
                 year=2020, active=False),
        Semester(semester_id=22, season="Summer 2",
                 year=2021, active=False),
        Semester(semester_id=23, season="Summer 2",
                 year=2022, active=False),
        Semester(semester_id=24, season="Summer 2",
                 year=2023, active=False),
        Semester(semester_id=25, season="Summer 2",
                 year=2024, active=False),
        Semester(semester_id=26, season="Summer 2",
                 year=2025, active=False),
        Semester(semester_id=27, season="Summer 2",
                 year=2026, active=False),
        Semester(semester_id=28, season="Summer Full",
                 year=2020, active=False),
        Semester(semester_id=29, season="Summer Full",
                 year=2021, active=False),
        Semester(semester_id=30, season="Summer Full",
                 year=2022, active=False),
        Semester(semester_id=31, season="Summer Full",
                 year=2023, active=False),
        Semester(semester_id=32, season="Summer Full",
                 year=2024, active=False),
        Semester(semester_id=33, season="Summer Full",
                 year=2025, active=False),
        Semester(semester_id=34, season="Summer Full",
                 year=2026, active=False),
    ]

    upcoming_sem = Semester(
        season="FALL",
        year=2026,
    )

    past_schedules = [
        Schedule(schedule_id=1,  name="Fall 2020",
                 semester_id=1,  draft=False, campus=1, active=False),
        Schedule(schedule_id=2,  name="Fall 2021",
                 semester_id=2,  draft=False, campus=1, active=False),
        Schedule(schedule_id=3,  name="Fall 2022",
                 semester_id=3,  draft=False, campus=1, active=False),
        Schedule(schedule_id=4,  name="Fall 2023",
                 semester_id=4,  draft=False, campus=1, active=False),
        Schedule(schedule_id=5,  name="Fall 2024",
                 semester_id=5,  draft=False, campus=1, active=False),
        Schedule(schedule_id=6,  name="Fall 2025",
                 semester_id=6,  draft=False, campus=1, active=False),
        Schedule(schedule_id=7,  name="Spring 2020",
                 semester_id=7,  draft=False, campus=1, active=False),
        Schedule(schedule_id=8,  name="Spring 2021",
                 semester_id=8,  draft=False, campus=1, active=False),
        Schedule(schedule_id=9,  name="Spring 2022",
                 semester_id=9,  draft=False, campus=1, active=False),
        Schedule(schedule_id=10, name="Spring 2023",
                 semester_id=10, draft=False, campus=1, active=False),
        Schedule(schedule_id=11, name="Spring 2024",
                 semester_id=11, draft=False, campus=1, active=False),
        Schedule(schedule_id=12, name="Spring 2025",
                 semester_id=12, draft=False, campus=1, active=False),
        Schedule(schedule_id=13, name="Spring 2026",
                 semester_id=13, draft=False, campus=1, active=False),
        Schedule(schedule_id=14, name="Summer 1 2020",
                 semester_id=14, draft=False, campus=1, active=False),
        Schedule(schedule_id=15, name="Summer 1 2021",
                 semester_id=15, draft=False, campus=1, active=False),
        Schedule(schedule_id=16, name="Summer 1 2022",
                 semester_id=16, draft=False, campus=1, active=False),
        Schedule(schedule_id=17, name="Summer 1 2023",
                 semester_id=17, draft=False, campus=1, active=False),
        Schedule(schedule_id=18, name="Summer 1 2024",
                 semester_id=18, draft=False, campus=1, active=False),
        Schedule(schedule_id=19, name="Summer 1 2025",
                 semester_id=19, draft=False, campus=1, active=False),
        Schedule(schedule_id=20, name="Summer 1 2026",
                 semester_id=20, draft=False, campus=1, active=False),
        Schedule(schedule_id=21, name="Summer 2 2020",
                 semester_id=21, draft=False, campus=1, active=False),
        Schedule(schedule_id=22, name="Summer 2 2021",
                 semester_id=22, draft=False, campus=1, active=False),
        Schedule(schedule_id=23, name="Summer 2 2022",
                 semester_id=23, draft=False, campus=1, active=False),
        Schedule(schedule_id=24, name="Summer 2 2023",
                 semester_id=24, draft=False, campus=1, active=False),
        Schedule(schedule_id=25, name="Summer 2 2024",
                 semester_id=25, draft=False, campus=1, active=False),
        Schedule(schedule_id=26, name="Summer 2 2025",
                 semester_id=26, draft=False, campus=1, active=False),
        Schedule(schedule_id=27, name="Summer 2 2026",
                 semester_id=27, draft=False, campus=1, active=False),
        Schedule(schedule_id=28, name="Summer Full 2020",
                 semester_id=28, draft=False, campus=1, active=False),
        Schedule(schedule_id=29, name="Summer Full 2021",
                 semester_id=29, draft=False, campus=1, active=False),
        Schedule(schedule_id=30, name="Summer Full 2022",
                 semester_id=30, draft=False, campus=1, active=False),
        Schedule(schedule_id=31, name="Summer Full 2023",
                 semester_id=31, draft=False, campus=1, active=False),
        Schedule(schedule_id=32, name="Summer Full 2024",
                 semester_id=32, draft=False, campus=1, active=False),
        Schedule(schedule_id=33, name="Summer Full 2025",
                 semester_id=33, draft=False, campus=1, active=False),
        Schedule(schedule_id=34, name="Summer Full 2026",
                 semester_id=34, draft=False, campus=1, active=False),
    ]

    current_draft = Schedule(
        name="Fall 2026 Draft",
        semester=upcoming_sem,
        schedule_id=1,
        campus=boston.campus_id,
        draft=True,
    )

    db.add_all(past_semesters)
    db.add_all(past_schedules)
    db.add(current_draft)
    db.flush()

    schedule_log = ScheduleLog(
        schedule_id=current_draft.schedule_id,
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
                schedule_id=current_draft.schedule_id,
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
    section_to_course_idx = {s: spec[0] for s, spec in zip(
        sections, section_specs, strict=True)}
    section_to_sec_num = {s: spec[2] for s, spec in zip(
        sections, section_specs, strict=True)}

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
    print(f"  1 schedule ('{current_draft.name}')")
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
