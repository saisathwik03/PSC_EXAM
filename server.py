import socket
import threading
import psycopg2
from http.server import HTTPServer, BaseHTTPRequestHandler

# Define host and port
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 12345        # Port to listen on (non-privileged ports are > 1023)

# PostgreSQL connection settings
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'student'
DB_USER = 'postgres'
DB_PASSWORD = 'nani'

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

    conn.commit()
    conn.close()

# Function to handle client connections
def handle_client(conn, addr):
    print(f"Connected by {addr}")

    # Receive and process client requests
    while True:
        data = conn.recv(1024).decode()

        if not data:
            break

        # Split received data into parts
        parts = data.split()

        # Perform actions based on the received command
        if parts[0] == 'login':
            username = parts[1]
            password = parts[2]
            if authenticate_user(username, password):
                conn.sendall(b"Login successful")
            else:
                conn.sendall(b"Invalid username or password")
        elif parts[0] == 'register':
            username = parts[1]
            password = parts[2]
            role = parts[3]
            if register_user(username, password, role):
                conn.sendall(b"Registration successful")
            else:
                conn.sendall(b"Failed to register user")
        elif parts[0] == 'create_course':
            # Dummy implementation of creating a course
            course_name = parts[1]
            conn.sendall(b"Course created successfully")
        elif parts[0] == 'enroll_course':
            # Dummy implementation of enrolling in a course
            course_name = parts[1]
            conn.sendall(b"Enrolled in course successfully")
        elif parts[0] == 'drop_course':
            # Dummy implementation of dropping a course
            course_name = parts[1]
            conn.sendall(b"Course dropped successfully")
        else:
            conn.sendall(b"Invalid command")

    # Close connection when done
    conn.close()

# Function to authenticate user using PostgreSQL
def authenticate_user(username, password):
    conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user is not None

# Function to register user and store in the database
def register_user(username, password, role):
    try:
        conn = psycopg2.connect(host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)", (username, password, role))
        conn.commit()
        conn.close()
        return True
    except psycopg2.Error as e:
        print("Error registering user:", e)
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

    error_page = """
    <html>
    <head><title>Error</title></head>
    <body>
        <h1>Error</h1>
        <p>{}</p>
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
        else:
            self.send_error(404, "File not found")

    # Handle POST requests
    def do_POST(self):
        if self.path == '/login':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            username = post_data.split('&')[0].split('=')[1]
            password = post_data.split('&')[1].split('=')[1]
            if authenticate_user(username, password):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Login successful")
            else:
                self.send_response(401)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(self.error_page.format("Invalid username or password").encode())
        elif self.path == '/register':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode()
            username = post_data.split('&')[0].split('=')[1]
            password = post_data.split('&')[1].split('=')[1]
            role = post_data.split('&')[2].split('=')[1]
            if register_user(username, password, role):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b"Registration successful")
            else:
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(self.error_page.format("Failed to register user").encode())
        else:
            self.send_error(404, "File not found")

# Main function to set up the server
def main():
    # Create the database if it does not exist
    create_database()

    # Create tables in the database
    create_tables()

    # Start HTTP server
    http_server = HTTPServer((HOST, PORT), RequestHandler)
    print(f"HTTP server listening on {HOST}:{PORT}")
    http_server.serve_forever()

if __name__ == "__main__":
    main()
