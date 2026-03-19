-- Seed file for Automated Course Scheduler
-- This script runs automatically when the Postgres container is first created.
-- Add your CREATE TABLE and INSERT statements here.

CREATE TYPE role AS ENUM ('Admin', 'Basic');
CREATE TYPE location AS ENUM ('Boston', 'London', 'Oakland');
CREATE TYPE weekday AS ENUM ('M', 'T', 'W', 'R', 'F');
CREATE TYPE semester_season AS ENUM ('Fall', 'Spring');

CREATE TABLE IF NOT EXISTS "User" (
  UserID SERIAL PRIMARY KEY,
  Username VARCHAR(100),
  UserRole role
);

CREATE TABLE IF NOT EXISTS TimeBlock (
    TimeBlockID SERIAL PRIMARY KEY,
    StartTime TIME,
    EndTime TIME,
    MeetingDays weekday[]
);

CREATE TABLE IF NOT EXISTS Campus (
    CampusID SERIAL PRIMARY KEY,
    CampusName location
);

CREATE TABLE IF NOT EXISTS CampusTimeBlock (
    CTBID SERIAL PRIMARY KEY, 
    BlockID INT REFERENCES TimeBlock(TimeBlockID),
    CampusID INT REFERENCES Campus(CampusID),
    Count INT
);

CREATE TABLE IF NOT EXISTS Faculty (
    NUID INT NOT NULL CHECK (NUID > 0) PRIMARY KEY,
    UserID INT REFERENCES "User"(UserID),
    FirstName VARCHAR(50),
    LastName VARCHAR(50),
    Email VARCHAR(255) CHECK (Email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    Title VARCHAR(50),
    Campus INT REFERENCES Campus(CampusID),
    Active BOOLEAN,
    MaxLoad INT
);

CREATE TABLE IF NOT EXISTS Course (
    CourseID SERIAL PRIMARY KEY,
    CourseDescription VARCHAR(255),
    CourseNo INT,
    CourseSubject VARCHAR(10),
    CourseName VARCHAR(100),
    SectionCount INT
);

CREATE TABLE IF NOT EXISTS Schedule (
    ScheduleID SERIAL PRIMARY KEY,
    ScheduleName VARCHAR(50),
    SemesterSeason semester_season,
    SemesterYear SMALLINT,
    Campus INT REFERENCES Campus(CampusID),
    Complete BOOLEAN
);

CREATE TABLE IF NOT EXISTS Section (
    SectionID SERIAL PRIMARY KEY,
    Schedule INT REFERENCES Schedule(ScheduleID),
    TimeBlock INT REFERENCES CampusTimeBlock(CTBID),
    Course INT REFERENCES Course(CourseID),
    Capacity INT,
    Instructor INT REFERENCES Faculty(NUID)
);

CREATE TABLE IF NOT EXISTS FacultyAssignment (
    AssignmentID SERIAL PRIMARY KEY,
    Instructor INT REFERENCES Faculty(NUID),
    SectionID INT REFERENCES Section(SectionID)
);

CREATE TABLE IF NOT EXISTS CoursePreference (
    PreferenceID SERIAL PRIMARY KEY,
    FacultyID INT REFERENCES Faculty(NUID),
    CourseID INT REFERENCES Course(CourseID),
    Rank INT CHECK (Rank >= 1 AND Rank <= 3)
);

CREATE TABLE IF NOT EXISTS TimePreference (
    PreferenceID SERIAL PRIMARY KEY,
    FacultyID INT REFERENCES Faculty(NUID),
    BlockID INT REFERENCES TimeBlock(TimeBlockID),
    Rank INT CHECK (Rank >= 1 AND Rank <= 3)
);
