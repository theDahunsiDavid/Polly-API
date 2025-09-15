#!/usr/bin/env python3
"""
Test script for user registration functionality.

This script demonstrates how to use the user_registration module
and includes comprehensive test cases for various scenarios.
"""

import unittest
from unittest.mock import patch, Mock
import requests
import json
import sys
import os

# Add the current directory to Python path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from user_registration import (
    register_user,
    register_user_simple,
    UserRegistrationError
)

class TestUserRegistration(unittest.TestCase):
    """Unit tests for user registration functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:8000"
        self.valid_username = "testuser123"
        self.valid_password = "securepassword123"

    @patch('user_registration.requests.post')
    def test_successful_registration(self, mock_post):
        """Test successful user registration"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "username": "testuser123"
        }
        mock_post.return_value = mock_response

        # Call the function
        result = register_user(self.valid_username, self.valid_password, self.base_url)

        # Assert results
        self.assertTrue(result.success)
        self.assertIsNotNone(result.user_data)
        # Safe access with proper None check
        if result.user_data is not None:
            self.assertEqual(result.user_data["id"], 1)
            self.assertEqual(result.user_data["username"], "testuser123")
        self.assertEqual(result.status_code, 200)
        self.assertIsNone(result.error_message)

        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIsNotNone(call_args)
        if call_args is not None:
            self.assertEqual(call_args[1]['url'], f"{self.base_url}/register")
            self.assertEqual(call_args[1]['json'], {
                "username": self.valid_username,
                "password": self.valid_password
            })

    @patch('user_registration.requests.post')
    def test_username_already_exists(self, mock_post):
        """Test registration with existing username"""
        # Mock 400 Bad Request response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "detail": "Username already registered"
        }
        mock_post.return_value = mock_response

        # Call the function
        result = register_user(self.valid_username, self.valid_password, self.base_url)

        # Assert results
        self.assertFalse(result.success)
        self.assertIsNone(result.user_data)
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.error_message, "Username already registered")

    @patch('user_registration.requests.post')
    def test_server_error(self, mock_post):
        """Test handling of server errors"""
        # Mock 500 Internal Server Error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "detail": "Internal server error"
        }
        mock_post.return_value = mock_response

        # Call the function
        result = register_user(self.valid_username, self.valid_password, self.base_url)

        # Assert results
        self.assertFalse(result.success)
        self.assertIsNone(result.user_data)
        self.assertEqual(result.status_code, 500)
        self.assertIsNotNone(result.error_message)
        if result.error_message is not None:
            self.assertIn("500", result.error_message)

    @patch('user_registration.requests.post')
    def test_invalid_json_response(self, mock_post):
        """Test handling of invalid JSON response"""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response

        # Call the function and expect an exception
        with self.assertRaises(UserRegistrationError) as context:
            register_user(self.valid_username, self.valid_password, self.base_url)

        self.assertIn("Failed to parse JSON response", str(context.exception))

    @patch('user_registration.requests.post')
    def test_connection_error(self, mock_post):
        """Test handling of connection errors"""
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        # Call the function and expect an exception
        with self.assertRaises(UserRegistrationError) as context:
            register_user(self.valid_username, self.valid_password, self.base_url)

        self.assertIn("Failed to connect to the API", str(context.exception))

    @patch('user_registration.requests.post')
    def test_timeout_error(self, mock_post):
        """Test handling of timeout errors"""
        # Mock timeout error
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        # Call the function and expect an exception
        with self.assertRaises(UserRegistrationError) as context:
            register_user(self.valid_username, self.valid_password, self.base_url)

        self.assertIn("Request timed out after 30 seconds", str(context.exception))

    def test_invalid_username_input(self):
        """Test validation of username input"""
        with self.assertRaises(ValueError) as context:
            register_user("", self.valid_password, self.base_url)
        self.assertIn("Username must be a non-empty string", str(context.exception))

        with self.assertRaises(ValueError) as context:
            register_user(None, self.valid_password, self.base_url)  # type: ignore[arg-type]
        self.assertIn("Username must be a non-empty string", str(context.exception))

        with self.assertRaises(ValueError) as context:
            register_user(123, self.valid_password, self.base_url)  # type: ignore[arg-type]
        self.assertIn("Username must be a non-empty string", str(context.exception))

    def test_invalid_password_input(self):
        """Test validation of password input"""
        with self.assertRaises(ValueError) as context:
            register_user(self.valid_username, "", self.base_url)
        self.assertIn("Password must be a non-empty string", str(context.exception))

        with self.assertRaises(ValueError) as context:
            register_user(self.valid_username, None, self.base_url)  # type: ignore[arg-type]
        self.assertIn("Password must be a non-empty string", str(context.exception))

    @patch('user_registration.requests.post')
    def test_simple_registration_success(self, mock_post):
        """Test the simple registration function with success"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 2,
            "username": "simpleuser"
        }
        mock_post.return_value = mock_response

        # Call the simple function
        user_data = register_user_simple("simpleuser", "simplepass", self.base_url)

        # Assert results
        self.assertIsNotNone(user_data)
        self.assertEqual(user_data["id"], 2)
        self.assertEqual(user_data["username"], "simpleuser")

    @patch('user_registration.requests.post')
    def test_simple_registration_failure(self, mock_post):
        """Test the simple registration function with failure"""
        # Mock 400 Bad Request response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "detail": "Username already registered"
        }
        mock_post.return_value = mock_response

        # Call the simple function and expect an exception
        with self.assertRaises(UserRegistrationError) as context:
            register_user_simple("existinguser", "password", self.base_url)

        self.assertIn("Registration failed", str(context.exception))


def run_integration_tests():
    """
    Integration tests that actually call the API.
    Only run these if the API server is running.
    """
    print("\n" + "="*50)
    print("INTEGRATION TESTS")
    print("="*50)
    print("Note: These tests require the API server to be running at http://localhost:8000")

    base_url = "http://localhost:8000"

    # Test 1: Register a new user
    print("\n1. Testing user registration with new username...")
    try:
        import time
        unique_username = f"testuser_{int(time.time())}"

        result = register_user(unique_username, "testpassword123", base_url)

        if result.success and result.user_data is not None:
            print(f"✅ SUCCESS: User '{unique_username}' registered successfully")
            print(f"   User ID: {result.user_data['id']}")
            print(f"   Username: {result.user_data['username']}")
        else:
            print(f"❌ FAILED: {result.error_message}")

    except UserRegistrationError as e:
        print(f"❌ ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

    # Test 2: Try to register with existing username
    print("\n2. Testing registration with duplicate username...")
    try:
        result = register_user("admin", "password123", base_url)

        if not result.success and result.status_code == 400:
            print("✅ SUCCESS: Correctly rejected duplicate username")
            print(f"   Error: {result.error_message}")
        else:
            print("❌ UNEXPECTED: Registration succeeded or wrong error code")

    except UserRegistrationError as e:
        print(f"❌ ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

    # Test 3: Test simple function
    print("\n3. Testing simple registration function...")
    try:
        import time
        unique_username = f"simpleuser_{int(time.time())}"

        user_data = register_user_simple(unique_username, "simplepassword123", base_url)
        print("✅ SUCCESS: User registered with simple function")
        print(f"   User ID: {user_data['id']}")
        print(f"   Username: {user_data['username']}")

    except UserRegistrationError as e:
        print(f"❌ ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")


def main():
    """Main function to run all tests"""
    print("USER REGISTRATION TESTING SUITE")
    print("="*50)

    # Run unit tests
    print("\nRunning unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)

    # Ask if user wants to run integration tests
    print("\n" + "="*50)
    response = input("Do you want to run integration tests? (Requires API server running) [y/N]: ")

    if response.lower() in ['y', 'yes']:
        run_integration_tests()
    else:
        print("Skipping integration tests.")

    print("\n" + "="*50)
    print("EXAMPLE USAGE")
    print("="*50)

    print("""
# Example 1: Basic usage with detailed response
from user_registration import register_user

result = register_user("myusername", "mypassword")
if result.success:
    print(f"User registered: {result.user_data}")
else:
    print(f"Registration failed: {result.error_message}")

# Example 2: Simple usage (raises exception on failure)
from user_registration import register_user_simple

try:
    user_data = register_user_simple("myusername", "mypassword")
    print(f"User ID: {user_data['id']}")
except UserRegistrationError as e:
    print(f"Registration failed: {e}")

# Example 3: Custom base URL
result = register_user("username", "password", "https://api.example.com")
    """)


if __name__ == "__main__":
    main()
