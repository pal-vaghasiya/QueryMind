"""SQLite Database Engine and Synthetic Workload Generator for experimental benchmark datasets."""

import sqlite3
import time
import random
import os
from typing import List, Dict, Any, Tuple, Optional

class DatabaseEngine:
    """Manages SQLite database creation, indexing, query execution, and profiling."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def setup_demo_schema(self, num_students: int = 5000, num_courses: int = 200, num_enrollments: int = 15000, num_professors: int = 50):
        """Populates database with demo tables: Students, Courses, Enrollments, Professors."""
        cursor = self.conn.cursor()

        cursor.execute("DROP TABLE IF EXISTS enrollments;")
        cursor.execute("DROP TABLE IF EXISTS students;")
        cursor.execute("DROP TABLE IF EXISTS courses;")
        cursor.execute("DROP TABLE IF EXISTS professors;")

        # Create tables
        cursor.execute("""
            CREATE TABLE professors (
                id INTEGER PRIMARY KEY,
                name TEXT,
                department TEXT,
                salary REAL,
                experience_years INTEGER
            );
        """)

        cursor.execute("""
            CREATE TABLE courses (
                id INTEGER PRIMARY KEY,
                title TEXT,
                department TEXT,
                credits INTEGER,
                professor_id INTEGER,
                FOREIGN KEY (professor_id) REFERENCES professors(id)
            );
        """)

        cursor.execute("""
            CREATE TABLE students (
                id INTEGER PRIMARY KEY,
                name TEXT,
                cgpa REAL,
                age INTEGER,
                major TEXT,
                year INTEGER
            );
        """)

        cursor.execute("""
            CREATE TABLE enrollments (
                id INTEGER PRIMARY KEY,
                student_id INTEGER,
                course_id INTEGER,
                grade REAL,
                semester TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id),
                FOREIGN KEY (course_id) REFERENCES courses(id)
            );
        """)

        # Insert dummy data
        departments = ["CS", "ECE", "ME", "EE", "MATH", "PHYS"]
        semesters = ["Fall 2024", "Spring 2025", "Fall 2025", "Spring 2026"]

        # Professors
        profs = [(i, f"Professor_{i}", random.choice(departments), random.uniform(50000, 150000), random.randint(1, 35)) for i in range(1, num_professors + 1)]
        cursor.executemany("INSERT INTO professors VALUES (?,?,?,?,?)", profs)

        # Courses
        courses = [(i, f"Course_{i}", random.choice(departments), random.randint(1, 4), random.randint(1, num_professors)) for i in range(1, num_courses + 1)]
        cursor.executemany("INSERT INTO courses VALUES (?,?,?,?,?)", courses)

        # Students
        students = [(i, f"Student_{i}", round(random.gauss(7.5, 1.2), 2), random.randint(18, 25), random.choice(departments), random.randint(1, 4)) for i in range(1, num_students + 1)]
        cursor.executemany("INSERT INTO students VALUES (?,?,?,?,?,?)", students)

        # Enrollments
        enrollments = [(i, random.randint(1, num_students), random.randint(1, num_courses), round(random.uniform(4.0, 10.0), 2), random.choice(semesters)) for i in range(1, num_enrollments + 1)]
        cursor.executemany("INSERT INTO enrollments VALUES (?,?,?,?,?)", enrollments)

        # Create indexes
        cursor.execute("CREATE INDEX idx_students_cgpa ON students(cgpa);")
        cursor.execute("CREATE INDEX idx_students_major ON students(major);")
        cursor.execute("CREATE INDEX idx_enroll_student ON enrollments(student_id);")
        cursor.execute("CREATE INDEX idx_enroll_course ON enrollments(course_id);")
        cursor.execute("CREATE INDEX idx_courses_prof ON courses(professor_id);")

        self.conn.commit()

    def execute_query(self, sql: str) -> Tuple[int, float]:
        """Executes a SQL query and returns (actual_cardinality, execution_time_ms)."""
        cursor = self.conn.cursor()
        start_time = time.perf_counter()
        cursor.execute(sql)
        rows = cursor.fetchall()
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return len(rows), elapsed_ms

    def close(self):
        self.conn.close()


class WorkloadGenerator:
    """Generates synthetic SQL workloads for training and evaluating QueryMind."""

    def __init__(self, db_engine: DatabaseEngine):
        self.db_engine = db_engine

    def generate_queries(self, count: int = 100) -> List[str]:
        """Generates a list of SQL queries with varying join counts and filters."""
        queries = []
        majors = ["CS", "ECE", "ME", "EE", "MATH", "PHYS"]

        for i in range(count):
            q_type = random.choice(["single", "2-join", "3-join"])
            
            if q_type == "single":
                cgpa_val = round(random.uniform(6.0, 9.5), 1)
                sql = f"SELECT * FROM students s WHERE s.cgpa > {cgpa_val};"
            elif q_type == "2-join":
                cgpa_val = round(random.uniform(7.0, 9.0), 1)
                sql = f"SELECT * FROM students s JOIN enrollments e ON s.id = e.student_id WHERE s.cgpa > {cgpa_val};"
            else:
                dept = random.choice(majors)
                cgpa_val = round(random.uniform(7.0, 9.0), 1)
                sql = (
                    f"SELECT * FROM students s "
                    f"JOIN enrollments e ON s.id = e.student_id "
                    f"JOIN courses c ON e.course_id = c.id "
                    f"WHERE s.cgpa > {cgpa_val} AND s.major = '{dept}';"
                )
            queries.append(sql)

        return queries
