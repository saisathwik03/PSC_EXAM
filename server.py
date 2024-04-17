import socket
import threading

# Define host and port
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 12345        # Port to listen on (non-privileged ports are > 1023)

# Dummy database for storing user credentials and course information
# In a real-world application, you would use a proper database
users = {
    'student': {'username': 'student', 'password': 'password', 'role': 'student'},
    'teacher': {'username': 'teacher', 'password': 'password', 'role': 'teacher'}
}

courses = {}

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
            if username in users and users[username]['password'] == password:
                conn.sendall(b"Login successful")
            else:
                conn.sendall(b"Invalid username or password")
        elif parts[0] == 'create_course':
            # Dummy implementation of creating a course
            course_name = parts[1]
            courses[course_name] = {'name': course_name}
            conn.sendall(b"Course created successfully")
        elif parts[0] == 'enroll_course':
            # Dummy implementation of enrolling in a course
            course_name = parts[1]
            if course_name in courses:
                conn.sendall(b"Enrolled in course successfully")
            else:
                conn.sendall(b"Course not found")
        elif parts[0] == 'drop_course':
            # Dummy implementation of dropping a course
            course_name = parts[1]
            if course_name in courses:
                del courses[course_name]
                conn.sendall(b"Course dropped successfully")
            else:
                conn.sendall(b"Course not found")
        else:
            conn.sendall(b"Invalid command")

    # Close connection when done
    conn.close()

# Main function to set up the server
def main():
    # Create a socket object
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        # Bind the socket to the address and port
        server_socket.bind((HOST, PORT))

        # Listen for incoming connections
        server_socket.listen()

        print(f"Server listening on {HOST}:{PORT}")

        # Accept incoming connections and spawn threads to handle them
        while True:
            conn, addr = server_socket.accept()
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

if __name__ == "__main__":
    main()
