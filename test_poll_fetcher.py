#!/usr/bin/env python3
"""
Test script for poll fetching functionality.

This script demonstrates how to use the poll_fetcher module
and includes comprehensive test cases for various scenarios.
"""

import unittest
from unittest.mock import patch, Mock
import requests
import json
import sys
import os
from datetime import datetime

# Add the current directory to Python path to import our module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from poll_fetcher import (
    fetch_polls,
    fetch_polls_simple,
    fetch_all_polls,
    search_polls_by_question,
    PollFetchError,
    PollFetchResponse
)

class TestPollFetcher(unittest.TestCase):
    """Unit tests for poll fetching functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:8000"
        self.sample_polls = [
            {
                "id": 1,
                "question": "What's your favorite programming language?",
                "created_at": "2024-01-15T10:30:00Z",
                "owner_id": 1,
                "options": [
                    {"id": 1, "text": "Python", "poll_id": 1},
                    {"id": 2, "text": "JavaScript", "poll_id": 1},
                    {"id": 3, "text": "Java", "poll_id": 1}
                ]
            },
            {
                "id": 2,
                "question": "Best time for coffee?",
                "created_at": "2024-01-16T08:15:00Z",
                "owner_id": 2,
                "options": [
                    {"id": 4, "text": "Morning", "poll_id": 2},
                    {"id": 5, "text": "Afternoon", "poll_id": 2}
                ]
            }
        ]

    @patch('poll_fetcher.requests.get')
    def test_successful_poll_fetch(self, mock_get):
        """Test successful poll fetching"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_polls
        mock_get.return_value = mock_response

        # Call the function
        result = fetch_polls(skip=0, limit=10, base_url=self.base_url)

        # Assert results
        self.assertTrue(result.success)
        self.assertEqual(len(result.polls), 2)
        self.assertEqual(result.total_fetched, 2)
        self.assertEqual(result.status_code, 200)
        self.assertIsNone(result.error_message)

        # Verify poll structure
        first_poll = result.polls[0]
        self.assertEqual(first_poll["id"], 1)
        self.assertEqual(first_poll["question"], "What's your favorite programming language?")
        self.assertEqual(len(first_poll["options"]), 3)

        # Verify the request was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIsNotNone(call_args)
        if call_args is not None:
            self.assertEqual(call_args[1]['url'], f"{self.base_url}/polls")
            self.assertEqual(call_args[1]['params'], {"skip": 0, "limit": 10})

    @patch('poll_fetcher.requests.get')
    def test_empty_poll_response(self, mock_get):
        """Test handling of empty poll list"""
        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_get.return_value = mock_response

        # Call the function
        result = fetch_polls(skip=50, limit=10, base_url=self.base_url)

        # Assert results
        self.assertTrue(result.success)
        self.assertEqual(len(result.polls), 0)
        self.assertEqual(result.total_fetched, 0)
        self.assertEqual(result.status_code, 200)

    @patch('poll_fetcher.requests.get')
    def test_server_error(self, mock_get):
        """Test handling of server errors"""
        # Mock 500 Internal Server Error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "detail": "Internal server error"
        }
        mock_get.return_value = mock_response

        # Call the function
        result = fetch_polls(skip=0, limit=10, base_url=self.base_url)

        # Assert results
        self.assertFalse(result.success)
        self.assertEqual(len(result.polls), 0)
        self.assertEqual(result.status_code, 500)
        self.assertIn("500", result.error_message)

    @patch('poll_fetcher.requests.get')
    def test_invalid_json_response(self, mock_get):
        """Test handling of invalid JSON response"""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        # Call the function and expect an exception
        with self.assertRaises(PollFetchError) as context:
            fetch_polls(skip=0, limit=10, base_url=self.base_url)

        self.assertIn("Failed to parse JSON response", str(context.exception))

    @patch('poll_fetcher.requests.get')
    def test_non_list_response(self, mock_get):
        """Test handling of non-list response"""
        # Mock response with non-list data
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Not a list"}
        mock_get.return_value = mock_response

        # Call the function and expect an exception
        with self.assertRaises(PollFetchError) as context:
            fetch_polls(skip=0, limit=10, base_url=self.base_url)

        self.assertIn("Expected list response", str(context.exception))

    @patch('poll_fetcher.requests.get')
    def test_connection_error(self, mock_get):
        """Test handling of connection errors"""
        # Mock connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        # Call the function and expect an exception
        with self.assertRaises(PollFetchError) as context:
            fetch_polls(skip=0, limit=10, base_url=self.base_url)

        self.assertIn("Failed to connect to the API", str(context.exception))

    @patch('poll_fetcher.requests.get')
    def test_timeout_error(self, mock_get):
        """Test handling of timeout errors"""
        # Mock timeout error
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        # Call the function and expect an exception
        with self.assertRaises(PollFetchError) as context:
            fetch_polls(skip=0, limit=10, base_url=self.base_url)

        self.assertIn("Request timed out after 30 seconds", str(context.exception))

    def test_invalid_skip_parameter(self):
        """Test validation of skip parameter"""
        with self.assertRaises(ValueError) as context:
            fetch_polls(skip=-1, limit=10)
        self.assertIn("Skip must be a non-negative integer", str(context.exception))

        with self.assertRaises(ValueError) as context:
            fetch_polls(skip="invalid", limit=10)  # type: ignore
        self.assertIn("Skip must be a non-negative integer", str(context.exception))

    def test_invalid_limit_parameter(self):
        """Test validation of limit parameter"""
        with self.assertRaises(ValueError) as context:
            fetch_polls(skip=0, limit=0)
        self.assertIn("Limit must be a positive integer", str(context.exception))

        with self.assertRaises(ValueError) as context:
            fetch_polls(skip=0, limit=-5)
        self.assertIn("Limit must be a positive integer", str(context.exception))

        with self.assertRaises(ValueError) as context:
            fetch_polls(skip=0, limit="invalid")  # type: ignore
        self.assertIn("Limit must be a positive integer", str(context.exception))

    @patch('poll_fetcher.requests.get')
    def test_simple_fetch_success(self, mock_get):
        """Test the simple fetch function with success"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_polls
        mock_get.return_value = mock_response

        # Call the simple function
        polls = fetch_polls_simple(skip=0, limit=5, base_url=self.base_url)

        # Assert results
        self.assertEqual(len(polls), 2)
        self.assertEqual(polls[0]["question"], "What's your favorite programming language?")
        self.assertEqual(polls[1]["question"], "Best time for coffee?")

    @patch('poll_fetcher.requests.get')
    def test_simple_fetch_failure(self, mock_get):
        """Test the simple fetch function with failure"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "detail": "Not found"
        }
        mock_get.return_value = mock_response

        # Call the simple function and expect an exception
        with self.assertRaises(PollFetchError) as context:
            fetch_polls_simple(skip=0, limit=10, base_url=self.base_url)

        self.assertIn("Poll fetch failed", str(context.exception))

    @patch('poll_fetcher.requests.get')
    def test_fetch_all_polls(self, mock_get):
        """Test fetching all polls with pagination"""
        # Mock responses for pagination
        first_response = Mock()
        first_response.status_code = 200
        first_response.json.return_value = self.sample_polls

        second_response = Mock()
        second_response.status_code = 200
        second_response.json.return_value = []  # Empty response indicates end

        mock_get.side_effect = [first_response, second_response]

        # Call the fetch all function
        all_polls = fetch_all_polls(base_url=self.base_url, batch_size=2)

        # Assert results
        self.assertEqual(len(all_polls), 2)
        self.assertEqual(mock_get.call_count, 2)

        # Verify the calls were made with correct parameters
        first_call = mock_get.call_args_list[0]
        second_call = mock_get.call_args_list[1]

        self.assertEqual(first_call[1]['params'], {"skip": 0, "limit": 2})
        self.assertEqual(second_call[1]['params'], {"skip": 2, "limit": 2})

    @patch('poll_fetcher.requests.get')
    def test_fetch_all_polls_error(self, mock_get):
        """Test fetch all polls with error"""
        # Mock error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"detail": "Server error"}
        mock_get.return_value = mock_response

        # Call the function and expect an exception
        with self.assertRaises(PollFetchError) as context:
            fetch_all_polls(base_url=self.base_url)

        self.assertIn("Failed to fetch polls at skip=0", str(context.exception))

    def test_fetch_all_polls_invalid_batch_size(self):
        """Test fetch all polls with invalid batch size"""
        with self.assertRaises(ValueError) as context:
            fetch_all_polls(batch_size=0)
        self.assertIn("Batch size must be between 1 and 100", str(context.exception))

        with self.assertRaises(ValueError) as context:
            fetch_all_polls(batch_size=101)
        self.assertIn("Batch size must be between 1 and 100", str(context.exception))

    @patch('poll_fetcher.requests.get')
    def test_search_polls_by_question(self, mock_get):
        """Test searching polls by question keyword"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_polls
        mock_get.return_value = mock_response

        # Search for polls containing "favorite"
        matching_polls = search_polls_by_question("favorite", skip=0, limit=10)

        # Assert results
        self.assertEqual(len(matching_polls), 1)
        self.assertIn("favorite", matching_polls[0]["question"].lower())

    @patch('poll_fetcher.requests.get')
    def test_search_polls_no_matches(self, mock_get):
        """Test searching polls with no matches"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_polls
        mock_get.return_value = mock_response

        # Search for non-existent keyword
        matching_polls = search_polls_by_question("nonexistent", skip=0, limit=10)

        # Assert results
        self.assertEqual(len(matching_polls), 0)

    def test_search_polls_invalid_keyword(self):
        """Test search polls with invalid keyword"""
        with self.assertRaises(ValueError) as context:
            search_polls_by_question("", skip=0, limit=10)
        self.assertIn("Question keyword must be a non-empty string", str(context.exception))

        with self.assertRaises(ValueError) as context:
            search_polls_by_question(None, skip=0, limit=10)  # type: ignore
        self.assertIn("Question keyword must be a non-empty string", str(context.exception))

    @patch('poll_fetcher.requests.get')
    def test_malformed_poll_structure(self, mock_get):
        """Test handling of polls with missing fields"""
        # Mock response with malformed poll data
        malformed_polls = [
            {
                "id": 1,
                "question": "Good poll",
                "created_at": "2024-01-15T10:30:00Z",
                "owner_id": 1,
                "options": [{"id": 1, "text": "Option 1", "poll_id": 1}]
            },
            {
                "id": 2,
                # Missing question field
                "created_at": "invalid-date-format",
                "owner_id": 2,
                "options": [{"id": 2, "text": "Option 2"}]  # Missing poll_id
            }
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = malformed_polls
        mock_get.return_value = mock_response

        # Call the function - should succeed but log warnings
        result = fetch_polls(skip=0, limit=10, base_url=self.base_url)

        # Assert it still succeeds (just logs warnings)
        self.assertTrue(result.success)
        self.assertEqual(len(result.polls), 2)


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

    # Test 1: Basic poll fetching
    print("\n1. Testing basic poll fetching...")
    try:
        result = fetch_polls(skip=0, limit=5, base_url=base_url)

        if result.success:
            print(f"✅ SUCCESS: Fetched {result.total_fetched} polls")
            for i, poll in enumerate(result.polls[:3]):  # Show first 3
                print(f"   Poll {i+1}: {poll.get('question', 'No question')[:50]}...")
        else:
            print(f"❌ FAILED: {result.error_message}")

    except PollFetchError as e:
        print(f"❌ ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

    # Test 2: Pagination test
    print("\n2. Testing pagination...")
    try:
        page1 = fetch_polls(skip=0, limit=2, base_url=base_url)
        page2 = fetch_polls(skip=2, limit=2, base_url=base_url)

        if page1.success and page2.success:
            print(f"✅ SUCCESS: Page 1 has {len(page1.polls)} polls, Page 2 has {len(page2.polls)} polls")
            if len(page1.polls) > 0 and len(page2.polls) > 0:
                # Verify different polls on different pages
                page1_ids = {poll['id'] for poll in page1.polls}
                page2_ids = {poll['id'] for poll in page2.polls}
                if page1_ids.isdisjoint(page2_ids):
                    print("   ✅ Pages contain different polls (good pagination)")
                else:
                    print("   ⚠️  Pages contain overlapping polls")
        else:
            print(f"❌ FAILED: Page 1 success: {page1.success}, Page 2 success: {page2.success}")

    except PollFetchError as e:
        print(f"❌ ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

    # Test 3: Simple fetch test
    print("\n3. Testing simple fetch function...")
    try:
        polls = fetch_polls_simple(skip=0, limit=3, base_url=base_url)
        print(f"✅ SUCCESS: Simple fetch returned {len(polls)} polls")
        for poll in polls:
            print(f"   - {poll.get('question', 'No question')[:40]}...")

    except PollFetchError as e:
        print(f"❌ ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

    # Test 4: Search functionality test
    print("\n4. Testing search functionality...")
    try:
        # Try common keywords that might exist
        keywords = ["favorite", "best", "what", "how"]
        found_any = False

        for keyword in keywords:
            try:
                matching_polls = search_polls_by_question(keyword, skip=0, limit=10, base_url=base_url)
                if matching_polls:
                    print(f"✅ SUCCESS: Found {len(matching_polls)} polls with keyword '{keyword}'")
                    for poll in matching_polls[:2]:  # Show first 2 matches
                        print(f"   - {poll.get('question', 'No question')[:50]}...")
                    found_any = True
                    break
            except Exception:
                continue

        if not found_any:
            print("ℹ️  No polls found with common keywords (this may be normal)")

    except PollFetchError as e:
        print(f"❌ ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

    # Test 5: Large limit test
    print("\n5. Testing with larger limit...")
    try:
        result = fetch_polls(skip=0, limit=50, base_url=base_url)

        if result.success:
            print(f"✅ SUCCESS: Large limit fetch returned {result.total_fetched} polls")
        else:
            print(f"❌ FAILED: {result.error_message}")

    except PollFetchError as e:
        print(f"❌ ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")


def main():
    """Main function to run all tests"""
    print("POLL FETCHER TESTING SUITE")
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
from poll_fetcher import fetch_polls

result = fetch_polls(skip=0, limit=10)
if result.success:
    print(f"Fetched {result.total_fetched} polls")
    for poll in result.polls:
        print(f"- {poll['question']}")
else:
    print(f"Failed: {result.error_message}")

# Example 2: Simple usage (raises exception on failure)
from poll_fetcher import fetch_polls_simple

try:
    polls = fetch_polls_simple(skip=0, limit=5)
    for poll in polls:
        print(f"Poll: {poll['question']}")
except PollFetchError as e:
    print(f"Failed: {e}")

# Example 3: Fetch all polls with automatic pagination
from poll_fetcher import fetch_all_polls

try:
    all_polls = fetch_all_polls()
    print(f"Total polls: {len(all_polls)}")
except PollFetchError as e:
    print(f"Failed: {e}")

# Example 4: Search polls by keyword
from poll_fetcher import search_polls_by_question

try:
    matching_polls = search_polls_by_question("favorite")
    print(f"Found {len(matching_polls)} matching polls")
except (PollFetchError, ValueError) as e:
    print(f"Search failed: {e}")

# Example 5: Custom base URL and pagination
result = fetch_polls(skip=20, limit=10, base_url="https://api.example.com")
    """)


if __name__ == "__main__":
    main()
