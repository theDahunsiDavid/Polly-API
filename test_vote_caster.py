#!/usr/bin/env python3
"""
Test script for vote casting functionality.

This script demonstrates how to use the vote_caster module
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

from vote_caster import (
    cast_vote,
    cast_vote_simple,
    get_user_vote_on_poll,
    VoteCastError
)

class TestVoteCaster(unittest.TestCase):
    """Unit tests for vote casting functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:8000"
        self.valid_poll_id = 1
        self.valid_option_id = 2
        self.valid_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.test.token"
        self.sample_vote_response = {
            "id": 123,
            "user_id": 456,
            "option_id": 2,
            "created_at": "2024-01-15T10:30:00Z"
        }

    @patch('vote_caster.requests.post')
    def test_successful_vote_cast(self, mock_post):
        """Test successful vote casting"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_vote_response
        mock_post.return_value = mock_response

        # Call the function
        result = cast_vote(
            poll_id=self.valid_poll_id,
            option_id=self.valid_option_id,
            access_token=self.valid_token,
            base_url=self.base_url
        )

        # Assert results
        self.assertTrue(result.success)
        self.assertIsNotNone(result.vote_data)
        if result.vote_data is not None:
            self.assertEqual(result.vote_data["id"], 123)
            self.assertEqual(result.vote_data["user_id"], 456)
            self.assertEqual(result.vote_data["option_id"], 2)
            self.assertEqual(result.vote_data["created_at"], "2024-01-15T10:30:00Z")
        self.assertEqual(result.status_code, 200)
        self.assertIsNone(result.error_message)

        # Verify the request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertIsNotNone(call_args)
        if call_args is not None:
            self.assertEqual(call_args[1]['url'], f"{self.base_url}/polls/{self.valid_poll_id}/vote")
            self.assertEqual(call_args[1]['json'], {"option_id": self.valid_option_id})
            self.assertIn('Authorization', call_args[1]['headers'])
            self.assertEqual(call_args[1]['headers']['Authorization'], f"Bearer {self.valid_token}")
            self.assertEqual(call_args[1]['headers']['Content-Type'], "application/json")

    @patch('vote_caster.requests.post')
    def test_unauthorized_vote_cast(self, mock_post):
        """Test vote casting with invalid/expired token"""
        # Mock 401 Unauthorized response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "detail": "Invalid authentication credentials"
        }
        mock_post.return_value = mock_response

        # Call the function
        result = cast_vote(
            poll_id=self.valid_poll_id,
            option_id=self.valid_option_id,
            access_token="invalid_token",
            base_url=self.base_url
        )

        # Assert results
        self.assertFalse(result.success)
        self.assertIsNone(result.vote_data)
        self.assertEqual(result.status_code, 401)
        self.assertEqual(result.error_message, "Invalid authentication credentials")

    @patch('vote_caster.requests.post')
    def test_poll_not_found(self, mock_post):
        """Test vote casting on non-existent poll"""
        # Mock 404 Not Found response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "detail": "Poll not found"
        }
        mock_post.return_value = mock_response

        # Call the function
        result = cast_vote(
            poll_id=999,
            option_id=self.valid_option_id,
            access_token=self.valid_token,
            base_url=self.base_url
        )

        # Assert results
        self.assertFalse(result.success)
        self.assertIsNone(result.vote_data)
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.error_message, "Poll not found")

    @patch('vote_caster.requests.post')
    def test_option_not_found(self, mock_post):
        """Test vote casting on non-existent option"""
        # Mock 404 Not Found response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "detail": "Option not found or does not belong to this poll"
        }
        mock_post.return_value = mock_response

        # Call the function
        result = cast_vote(
            poll_id=self.valid_poll_id,
            option_id=999,
            access_token=self.valid_token,
            base_url=self.base_url
        )

        # Assert results
        self.assertFalse(result.success)
        self.assertIsNone(result.vote_data)
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.error_message, "Option not found or does not belong to this poll")

    @patch('vote_caster.requests.post')
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
        result = cast_vote(
            poll_id=self.valid_poll_id,
            option_id=self.valid_option_id,
            access_token=self.valid_token,
            base_url=self.base_url
        )

        # Assert results
        self.assertFalse(result.success)
        self.assertIsNone(result.vote_data)
        self.assertEqual(result.status_code, 500)
        self.assertIsNotNone(result.error_message)
        if result.error_message is not None:
            self.assertIn("500", result.error_message)

    @patch('vote_caster.requests.post')
    def test_invalid_json_response(self, mock_post):
        """Test handling of invalid JSON response"""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_post.return_value = mock_response

        # Call the function and expect an exception
        with self.assertRaises(VoteCastError) as context:
            cast_vote(
                poll_id=self.valid_poll_id,
                option_id=self.valid_option_id,
                access_token=self.valid_token,
                base_url=self.base_url
            )

        self.assertIn("Failed to parse JSON response", str(context.exception))

    @patch('vote_caster.requests.post')
    def test_connection_error(self, mock_post):
        """Test handling of connection errors"""
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")

        # Call the function and expect an exception
        with self.assertRaises(VoteCastError) as context:
            cast_vote(
                poll_id=self.valid_poll_id,
                option_id=self.valid_option_id,
                access_token=self.valid_token,
                base_url=self.base_url
            )

        self.assertIn("Failed to connect to the API", str(context.exception))

    @patch('vote_caster.requests.post')
    def test_timeout_error(self, mock_post):
        """Test handling of timeout errors"""
        # Mock timeout error
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")

        # Call the function and expect an exception
        with self.assertRaises(VoteCastError) as context:
            cast_vote(
                poll_id=self.valid_poll_id,
                option_id=self.valid_option_id,
                access_token=self.valid_token,
                base_url=self.base_url
            )

        self.assertIn("Request timed out after 30 seconds", str(context.exception))

    def test_invalid_poll_id_validation(self):
        """Test validation of poll_id parameter"""
        with self.assertRaises(ValueError) as context:
            cast_vote(poll_id=0, option_id=self.valid_option_id, access_token=self.valid_token)
        self.assertIn("Poll ID must be a positive integer", str(context.exception))

        with self.assertRaises(ValueError) as context:
            cast_vote(poll_id=-1, option_id=self.valid_option_id, access_token=self.valid_token)
        self.assertIn("Poll ID must be a positive integer", str(context.exception))

        with self.assertRaises(ValueError) as context:
            cast_vote(poll_id="invalid", option_id=self.valid_option_id, access_token=self.valid_token)  # type: ignore[arg-type]
        self.assertIn("Poll ID must be a positive integer", str(context.exception))

    def test_invalid_option_id_validation(self):
        """Test validation of option_id parameter"""
        with self.assertRaises(ValueError) as context:
            cast_vote(poll_id=self.valid_poll_id, option_id=0, access_token=self.valid_token)
        self.assertIn("Option ID must be a positive integer", str(context.exception))

        with self.assertRaises(ValueError) as context:
            cast_vote(poll_id=self.valid_poll_id, option_id=-1, access_token=self.valid_token)
        self.assertIn("Option ID must be a positive integer", str(context.exception))

        with self.assertRaises(ValueError) as context:
            cast_vote(poll_id=self.valid_poll_id, option_id="invalid", access_token=self.valid_token)  # type: ignore[arg-type]
        self.assertIn("Option ID must be a positive integer", str(context.exception))

    def test_invalid_access_token_validation(self):
        """Test validation of access_token parameter"""
        with self.assertRaises(ValueError) as context:
            cast_vote(poll_id=self.valid_poll_id, option_id=self.valid_option_id, access_token="")
        self.assertIn("Access token must be a non-empty string", str(context.exception))

        with self.assertRaises(ValueError) as context:
            cast_vote(poll_id=self.valid_poll_id, option_id=self.valid_option_id, access_token=None)  # type: ignore[arg-type]
        self.assertIn("Access token must be a non-empty string", str(context.exception))

        with self.assertRaises(ValueError) as context:
            cast_vote(poll_id=self.valid_poll_id, option_id=self.valid_option_id, access_token=123)  # type: ignore[arg-type]
        self.assertIn("Access token must be a non-empty string", str(context.exception))

    @patch('vote_caster.requests.post')
    def test_simple_vote_cast_success(self, mock_post):
        """Test the simple vote cast function with success"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_vote_response
        mock_post.return_value = mock_response

        # Call the simple function
        vote_data = cast_vote_simple(
            poll_id=self.valid_poll_id,
            option_id=self.valid_option_id,
            access_token=self.valid_token,
            base_url=self.base_url
        )

        # Assert results
        self.assertIsNotNone(vote_data)
        self.assertEqual(vote_data["id"], 123)
        self.assertEqual(vote_data["user_id"], 456)
        self.assertEqual(vote_data["option_id"], 2)

    @patch('vote_caster.requests.post')
    def test_simple_vote_cast_failure(self, mock_post):
        """Test the simple vote cast function with failure"""
        # Mock 401 Unauthorized response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "detail": "Unauthorized"
        }
        mock_post.return_value = mock_response

        # Call the simple function and expect an exception
        with self.assertRaises(VoteCastError) as context:
            cast_vote_simple(
                poll_id=self.valid_poll_id,
                option_id=self.valid_option_id,
                access_token="invalid_token",
                base_url=self.base_url
            )

        self.assertIn("Vote casting failed", str(context.exception))

    @patch('vote_caster.requests.post')
    def test_response_validation_missing_fields(self, mock_post):
        """Test response validation with missing fields"""
        # Mock response with missing fields
        incomplete_response = {
            "id": 123,
            # Missing user_id, option_id, created_at
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = incomplete_response
        mock_post.return_value = mock_response

        # Call the function - should succeed but log warnings
        result = cast_vote(
            poll_id=self.valid_poll_id,
            option_id=self.valid_option_id,
            access_token=self.valid_token,
            base_url=self.base_url
        )

        # Assert it still succeeds (just logs warnings)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.vote_data)

    @patch('vote_caster.requests.post')
    def test_response_validation_wrong_option_id(self, mock_post):
        """Test response validation when option_id doesn't match request"""
        # Mock response with wrong option_id
        wrong_response = {
            "id": 123,
            "user_id": 456,
            "option_id": 999,  # Different from requested option_id
            "created_at": "2024-01-15T10:30:00Z"
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = wrong_response
        mock_post.return_value = mock_response

        # Call the function - should succeed but log warning
        result = cast_vote(
            poll_id=self.valid_poll_id,
            option_id=self.valid_option_id,
            access_token=self.valid_token,
            base_url=self.base_url
        )

        # Assert it still succeeds (just logs warning)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.vote_data)

    @patch('vote_caster.requests.post')
    def test_response_validation_invalid_date_format(self, mock_post):
        """Test response validation with invalid date format"""
        # Mock response with invalid date
        invalid_date_response = {
            "id": 123,
            "user_id": 456,
            "option_id": 2,
            "created_at": "invalid-date-format"
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = invalid_date_response
        mock_post.return_value = mock_response

        # Call the function - should succeed but log warning
        vote_result = cast_vote(
            poll_id=self.valid_poll_id,
            option_id=self.valid_option_id,
            access_token=self.valid_token,
            base_url=self.base_url
        )

        # Assert it still succeeds (just logs warning)
        self.assertTrue(vote_result.success)
        self.assertIsNotNone(vote_result.vote_data)

    def test_get_user_vote_on_poll_validation(self):
        """Test validation of get_user_vote_on_poll function"""
        with self.assertRaises(ValueError) as context:
            get_user_vote_on_poll(poll_id=0, access_token=self.valid_token)
        self.assertIn("Poll ID must be a positive integer", str(context.exception))

        with self.assertRaises(ValueError) as context:
            get_user_vote_on_poll(poll_id=self.valid_poll_id, access_token="")
        self.assertIn("Access token must be a non-empty string", str(context.exception))

    def test_get_user_vote_on_poll_placeholder(self):
        """Test the placeholder implementation of get_user_vote_on_poll"""
        # This should return None since it's a placeholder
        result = get_user_vote_on_poll(
            poll_id=self.valid_poll_id,
            access_token=self.valid_token
        )
        self.assertIsNone(result)

    @patch('vote_caster.requests.post')
    def test_token_stripping(self, mock_post):
        """Test that access tokens are stripped of whitespace"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_vote_response
        mock_post.return_value = mock_response

        # Call with token that has whitespace
        token_with_whitespace = "  " + self.valid_token + "  "
        result = cast_vote(
            poll_id=self.valid_poll_id,
            option_id=self.valid_option_id,
            access_token=token_with_whitespace,
            base_url=self.base_url
        )

        # Verify the request was made with stripped token
        call_args = mock_post.call_args
        self.assertIsNotNone(call_args)
        if call_args is not None:
            auth_header = call_args[1]['headers']['Authorization']
            self.assertEqual(auth_header, f"Bearer {self.valid_token}")

    @patch('vote_caster.requests.post')
    def test_error_response_without_detail(self, mock_post):
        """Test handling of error responses without detail field"""
        # Mock error response without detail
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad request"}
        mock_response.text = "Bad request text"
        mock_post.return_value = mock_response

        # Call the function
        vote_result = cast_vote(
            poll_id=self.valid_poll_id,
            option_id=self.valid_option_id,
            access_token=self.valid_token,
            base_url=self.base_url
        )

        # Assert results
        self.assertFalse(vote_result.success)
        self.assertEqual(vote_result.status_code, 400)
        self.assertIsNotNone(vote_result.error_message)


def run_integration_tests():
    """
    Integration tests that actually call the API.
    Only run these if the API server is running and you have a valid token.
    """
    print("\n" + "="*50)
    print("INTEGRATION TESTS")
    print("="*50)
    print("Note: These tests require:")
    print("1. API server running at http://localhost:8000")
    print("2. Valid JWT access token")
    print("3. Existing polls with options")

    base_url = "http://localhost:8000"

    # You would need to replace this with a real access token
    access_token = input("Enter your JWT access token (or 'skip' to skip): ").strip()

    if access_token.lower() == 'skip':
        print("Skipping integration tests.")
        return

    # Test 1: Try to cast a vote
    print("\n1. Testing vote casting...")
    try:
        # First, try to get available polls to find valid poll_id and option_id
        poll_id = int(input("Enter a poll ID to vote on: "))
        option_id = int(input("Enter an option ID to vote for: "))

        result = cast_vote(poll_id=poll_id, option_id=option_id, access_token=access_token, base_url=base_url)

        if result.success and result.vote_data is not None:
            print("✅ SUCCESS: Vote cast successfully!")
            vote_data = result.vote_data
            print(f"   Vote ID: {vote_data['id']}")
            print(f"   User ID: {vote_data['user_id']}")
            print(f"   Option ID: {vote_data['option_id']}")
            print(f"   Cast at: {vote_data['created_at']}")
        else:
            print(f"❌ FAILED: {result.error_message}")
            print(f"   Status Code: {result.status_code}")

    except VoteCastError as e:
        print(f"❌ ERROR: {e}")
    except ValueError as e:
        print(f"❌ INPUT ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

    # Test 2: Try to vote on non-existent poll
    print("\n2. Testing vote on non-existent poll...")
    try:
        result = cast_vote(poll_id=99999, option_id=1, access_token=access_token, base_url=base_url)

        if not result.success and result.status_code == 404:
            print("✅ SUCCESS: Correctly handled non-existent poll")
            print(f"   Error: {result.error_message}")
        else:
            print("❌ UNEXPECTED: Should have failed with 404")

    except VoteCastError as e:
        print(f"❌ ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

    # Test 3: Test simple vote casting function
    print("\n3. Testing simple vote casting...")
    try:
        poll_id = int(input("Enter another poll ID for simple test: "))
        option_id = int(input("Enter an option ID for simple test: "))

        vote_data = cast_vote_simple(poll_id=poll_id, option_id=option_id, access_token=access_token, base_url=base_url)
        print("✅ SUCCESS: Simple vote casting worked")
        print(f"   Vote ID: {vote_data['id']}")

    except VoteCastError as e:
        print(f"❌ FAILED: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")


def main():
    """Main function to run all tests"""
    print("VOTE CASTER TESTING SUITE")
    print("="*50)

    # Run unit tests
    print("\nRunning unit tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)

    # Ask if user wants to run integration tests
    print("\n" + "="*50)
    response = input("Do you want to run integration tests? (Requires API server and valid token) [y/N]: ")

    if response.lower() in ['y', 'yes']:
        run_integration_tests()
    else:
        print("Skipping integration tests.")

    print("\n" + "="*50)
    print("EXAMPLE USAGE")
    print("="*50)

    print("""
# Example 1: Basic usage with detailed response
from vote_caster import cast_vote

result = cast_vote(poll_id=1, option_id=2, access_token="your_jwt_token")
if result.success:
    print(f"Vote cast! Vote ID: {result.vote_data['id']}")
else:
    print(f"Failed: {result.error_message}")

# Example 2: Simple usage (raises exception on failure)
from vote_caster import cast_vote_simple

try:
    vote_data = cast_vote_simple(poll_id=1, option_id=2, access_token="your_jwt_token")
    print(f"Vote ID: {vote_data['id']}")
except VoteCastError as e:
    print(f"Failed: {e}")

# Example 3: Custom base URL
result = cast_vote(poll_id=1, option_id=2, access_token="token", base_url="https://api.example.com")

# Example 4: Error handling
from vote_caster import VoteCastError

try:
    result = cast_vote(poll_id=1, option_id=2, access_token="token")
    if result.success:
        print("Success!")
    elif result.status_code == 401:
        print("Authentication failed")
    elif result.status_code == 404:
        print("Poll or option not found")
    else:
        print(f"Other error: {result.error_message}")
except VoteCastError as e:
    print(f"Network error: {e}")
except ValueError as e:
    print(f"Invalid input: {e}")
    """)


if __name__ == "__main__":
    main()
