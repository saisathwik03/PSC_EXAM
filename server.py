import socket
import threading
import psycopg2
from http.server import HTTPServer, BaseHTTPRequestHandler
import secrets
import string

# Define host and port
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 12345        # Port to listen on (non-privileged ports are > 1023)

# PostgreSQL connection settings
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'student'
DB_USER = 'postgres'
DB_PASSWORD = 'nani'

# Function to generate session token
def generate_session_token():
    # Generate a random session token
    alphabet = string.ascii_letters + string.digits
    session_token = ''.join(secrets.choice(alphabet) for i in range(32))
    return session_token

# Global dictionary to store session tokens
session_tokens = {}

# Function to create database and tables
def create_database():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname='postgres', user=DB_USER, password=DB_PASSWORD)
    conn.autocommit = True
    cursor = conn.cursor()

    # Check if the database already exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    exists = cursor.fetchone()

    # If the database does not exist, create it
    if not exists:
        cursor.execute(f"CREATE DATABASE {DB_NAME} ENCODING 'UTF8'")

    conn.close()

def create_tables():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(50) NOT NULL,
            role VARCHAR(10) NOT NULL
        )
    ''')

    # Create courses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL
        )
    ''')

    # Create enrolled_courses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enrolled_courses (
            id SERIAL PRIMARY KEY,
            student_name VARCHAR(50) NOT NULL,
            course_name VARCHAR(100) NOT NULL,
            FOREIGN KEY (course_name) REFERENCES courses(name)
        )
    ''')

    conn.commit()
    conn.close()

def fetch_available_courses():
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM courses")
    courses = [row[0] for row in cursor.fetchall()]
    conn.close()
    return courses

def enroll_course(student_name, course_name):
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO enrolled_courses (student_name, course_name) VALUES (%s, %s)", (student_name, course_name))
        conn.commit()
        conn.close()
        return True
    except psycopg2.Error as e:
        print("Error enrolling course:", e)
        return False

def drop_course(student_name, course_name):
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM enrolled_courses WHERE student_name = %s AND course_name = %s", (student_name, course_name))
        conn.commit()
        conn.close()
        return True
    except psycopg2.Error as e:
        print("Error dropping course:", e)
        return False

# HTTP request handler class
class RequestHandler(BaseHTTPRequestHandler):
    # Define HTML content
    index_page = """
    <html>
    <head><title>Login Page</title></head>
    <body>
        <h1>Login</h1>
        <form method="post" action="/login">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            <input type="submit" value="Login">
        </form>
        <h1>Register</h1>
        <form method="post" action="/register">
            Username: <input type="text" name="username"><br>
            Password: <input type="password" name="password"><br>
            Role: <select name="role">
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
            </select><br>
            <input type="submit" value="Register">
        </form>
    </body>
    </html>
    """

    dashboard_page = """
    <html>
    <head><title>Dashboard</title></head>
    <body>
        <h1>Welcome to Your Dashboard, %s</h1>
        <h2>Enrolled Courses:</h2>
        <ul>
        %s
        </ul>
        <h2>Available Courses:</h2>
        <ul>
        %s
        </ul>
    </body>
    </html>
    """

    create_course_page = """
    <html>
    <head><title>Create Course</title></head>
    <body>
        <h1>Create Course</h1>
        <form method="post" action="/create_course">
            Course Name: <input type="text" name="course_name"><br>
            <input type="submit" value="Create Course">
        </form>
    </body>
    </html>
    """

    # Handle GET requests
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.index_page.encode())
        elif self.path == '/dashboard':
            # Fetch enrolled courses for the current user
            student_name = session_tokens.get(self.headers.get('Cookie').split('=')[1])
            if student_name:
                enrolled_courses = fetch_enrolled_courses(student_name)
                available_courses = fetch_available_courses()
                enrolled_courses_html = "".join([f"<li>{course}</li>" for course in enrolled_courses])
                available_courses_html = "".join([f"<li>{course}</li>" for course in available_courses])
                dashboard_content = self.dashboard_page % (student_name, enrolled_courses_html, available_courses_html)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(dashboard_content.encode())
            else:
                self.send_error(401, "Unauthorized")
        elif self.path == '/create_course':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.create_course_page.encode())
        else:
            self.send_error(404, "File not found")

    # Handle POST requests
    def do_POST(self):
        if self.path == '/login':
            # Code to authenticate user
            # If authentication successful, generate session token and redirect to dashboard
            session_token = generate_session_token()
            session_tokens[session_token] = self.headers['username']  # Assuming username is sent in the request headers
            self.send_response(302)
            self.send_header('Location', '/dashboard')
            self.send_header('Set-Cookie', f'session_token={session_token}; Path=/')  # Set session token in cookie
            self.end_headers()
        elif self.path == '/enroll_course':
            # Code to enroll in a course
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            student_name = session_tokens.get(self.headers.get('Cookie').split('=')[1])
            if student_name:
                course_name = post_data.split('=')[1]
                if enroll_course(student_name, course_name):
                    self.send_response(302)
                    self.send_header('Location', '/dashboard')
                    self.end_headers()
                else:
                    self.send_error(500, "Failed to enroll in course")
            else:
                self.send_error(401, "Unauthorized")
        elif self.path == '/drop_course':
            # Code to drop a course
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            student_name = session_tokens.get(self.headers.get('Cookie').split('=')[1])
            if student_name:
                course_name = post_data.split('=')[1]
                if drop_course(student_name, course_name):
                    self.send_response(302)
                    self.send_header('Location', '/dashboard')
                    self.end_headers()
                else:
                    self.send_error(500, "Failed to drop course")
            else:
                self.send_error(401, "Unauthorized")
        else:
            self.send_error(404, "File not found")

def main():
    create_database()
    create_tables()

    # Create HTTP server
    server = HTTPServer((HOST, PORT), RequestHandler)
    print(f"Server started on {HOST}:{PORT}")

    # Serve requests indefinitely
    server.serve_forever()

if __name__ == "__main__":
    main()
