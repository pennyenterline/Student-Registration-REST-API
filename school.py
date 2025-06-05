#!/usr/bin/env python3

import os
import sys
import json
import psycopg2
import cgitb
from db_config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

cgitb.enable()

def connect():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def respond(status, message=None, redirect_url=None):
    print(f"Status: {status}")
    print("Content-Type: application/json")
    if redirect_url:
        print(f"Location: {redirect_url}")
    print()
    if message:
        print(json.dumps({"error": message}))
    sys.exit()

def get_students():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM students")
            students = []
            for row in cur.fetchall():
                student_id, name = row
                cur.execute("SELECT course_id FROM registrations WHERE student_id = %s", (student_id,))
                courses = [r[0] for r in cur.fetchall()]
                students.append({"id": student_id, "name": name, "courses": courses, "link": f"students/{student_id}"})
    print("Content-Type: application/json\n")
    print(json.dumps(students))

def post_student():
    try:
        input_data = json.load(sys.stdin)
        student_id = input_data["id"]
        name = input_data["name"]
        if not isinstance(student_id, int):
            respond(400, "Student ID must be an integer")
        if not isinstance(name, str) or not name:
            respond(400, "Name must be a non-empty string")
    except:
        respond(400, "Invalid input")

    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM students WHERE id = %s", (student_id,))
            if cur.fetchone():
                respond(400, "Student ID already exists")
            cur.execute("INSERT INTO students (id, name) VALUES (%s, %s)", (student_id, name))
            conn.commit()
    respond(303, redirect_url=f"students/{student_id}")

def get_student(student_id):
    try:
        student_id = int(student_id)
    except ValueError:
        respond(400, "Student ID must be an integer")
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM students WHERE id = %s", (student_id,))
            result = cur.fetchone()
            if not result:
                respond(404, "Student not found")
            name = result[0]
            cur.execute("SELECT course_id FROM registrations WHERE student_id = %s", (student_id,))
            courses = [r[0] for r in cur.fetchall()]
            student = {"id": student_id, "name": name, "courses": courses, "link": f"students/{student_id}"}
    print("Content-Type: application/json\n")
    print(json.dumps(student))

def delete_student(student_id):
    try:
        student_id = int(student_id)
    except ValueError:
        respond(400, "Student ID must be an integer")
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM students WHERE id = %s", (student_id,))
            conn.commit()
    respond(303, redirect_url="students")

def post_student_course(student_id):
    try:
        student_id = int(student_id)
    except ValueError:
        respond(400, "Student ID must be an integer")
    try:
        course_data = json.load(sys.stdin)
        course_id = course_data
    except:
        respond(400, "Invalid input")
    
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM students WHERE id = %s", (student_id,))
            if not cur.fetchone():
                respond(404, "Student not found")
            cur.execute("SELECT 1 FROM courses WHERE id = %s", (course_id,))
            if not cur.fetchone():
                respond(400, "Course ID not found")
            cur.execute("SELECT 1 FROM registrations WHERE student_id = %s AND course_id = %s", (student_id, course_id))
            if cur.fetchone():
                respond(400, "Already enrolled")
            cur.execute("INSERT INTO registrations (student_id, course_id) VALUES (%s, %s)", (student_id, course_id))
            conn.commit()
    respond(303, redirect_url=f"students/{student_id}/courses")

def get_courses():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM courses")
            courses = [{"id": row[0], "link": f"courses/{row[0]}"} for row in cur.fetchall()]
    print("Content-Type: application/json\n")
    print(json.dumps(courses))

def get_course(course_id):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM courses WHERE id = %s", (course_id,))
            if not cur.fetchone():
                respond(404, "Course not found")
            course = {"id": course_id, "link": f"courses/{course_id}"}
    print("Content-Type: application/json\n")
    print(json.dumps(course))

def post_course():
    try:
        input_data = json.load(sys.stdin)
        course_id = input_data["id"]
        if not isinstance(course_id, str) or not course_id:
            respond(400, "Course ID must be a non-empty string")
    except:
        respond(400, "Invalid input")
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM courses WHERE id = %s", (course_id,))
            if cur.fetchone():
                respond(400, "Course ID already exists")
            cur.execute("INSERT INTO courses (id) VALUES (%s)", (course_id,))
            conn.commit()
    respond(303, redirect_url=f"courses/{course_id}")

def delete_course(course_id):
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM registrations WHERE course_id = %s", (course_id,))
            if cur.fetchone():
                respond(400, "Cannot delete course; students are enrolled")
            cur.execute("DELETE FROM courses WHERE id = %s", (course_id,))
            conn.commit()
    respond(303, redirect_url="courses")

def get_debug():
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM students")
            students = cur.fetchall()
            cur.execute("SELECT * FROM courses")
            courses = cur.fetchall()
            cur.execute("SELECT * FROM registrations")
            registrations = cur.fetchall()
    print("Content-Type: application/json\n")
    print(json.dumps({
        "students": students,
        "courses": courses,
        "registrations": registrations
    }, default=str))

def main():
    path = os.environ.get("PATH_INFO", "").strip("/").split("/")
    method = os.environ.get("REQUEST_METHOD", "GET")

    if not path[0]:
        respond(400, "Invalid URL")

    if path[0] == "students":
        if len(path) == 1:
            if method == "GET":
                get_students()
            elif method == "POST":
                post_student()
        elif len(path) == 2:
            if method == "GET":
                get_student(path[1])
            elif method == "DELETE":
                delete_student(path[1])
        elif len(path) == 3 and path[2] == "courses" and method == "POST":
            post_student_course(path[1])

    elif path[0] == "courses":
        if len(path) == 1:
            if method == "GET":
                get_courses()
            elif method == "POST":
                post_course()
        elif len(path) == 2:
            if method == "GET":
                get_course(path[1])
            elif method == "DELETE":
                delete_course(path[1])

    elif path[0] == "debug" and method == "GET":
        get_debug()

    respond(404, "Invalid URL")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        respond(500, str(e))
