import unittest
import requests
from bs4 import BeautifulSoup

class TestServer(unittest.TestCase):
    def test_server_connection(self):
        # Test if the server is running and accessible
        response = requests.get('http://127.0.0.1:12345')
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):
        # Test if the login page is accessible and contains expected content
        response = requests.get('http://127.0.0.1:12345')
        soup = BeautifulSoup(response.text, 'html.parser')
        self.assertIn('<title>Login Page</title>', str(soup))
        self.assertIn('<h1>Login</h1>', str(soup))
        self.assertIn('<form method="post" action="/login">', str(soup))
        # Add more assertions as needed for other elements on the login page

    def test_register_page(self):
        # Test if the register page is accessible and contains expected content
        response = requests.get('http://127.0.0.1:12345')
        soup = BeautifulSoup(response.text, 'html.parser')
        self.assertIn('<title>Login Page</title>', str(soup))
        self.assertIn('<h1>Register</h1>', str(soup))
        self.assertIn('<form method="post" action="/register">', str(soup))
        # Add more assertions as needed for other elements on the register page

    def test_dashboard_page_unauthorized_access(self):
        # Test if accessing the dashboard without login results in an unauthorized response
        response = requests.get('http://127.0.0.1:12345/dashboard')
        self.assertEqual(response.status_code, 401)

    def test_dashboard_page_authorized_access(self):
        # Test if accessing the dashboard after login results in a successful response
        # This assumes a successful login process, which could be simulated by sending a POST request to the login endpoint
        login_data = {'username': 'test_user', 'password': 'test_password'}
        login_response = requests.post('http://127.0.0.1:12345/login', data=login_data)
        self.assertEqual(login_response.status_code, 302)  # Assuming successful login redirects to the dashboard
        dashboard_response = requests.get('http://127.0.0.1:12345/dashboard', cookies=login_response.cookies)
        self.assertEqual(dashboard_response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
