#!/usr/bin/env python3
"""
Test script for poll results functionality.

This script demonstrates how to use the poll_results module
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

from poll_results import (
    get_poll_results,
    get_poll_results_simple,
    get_poll_winner,
    get_poll_statistics,
    PollResultsError
)

class TestPollResults(unittest.TestCase):
    """Unit tests for poll results functions"""

    def setUp(self):
        """Set up test fixtures"""
        self.base_url = "http://localhost:8000"
        self.valid_poll_id = 1
        self.sample_results_response = {
            "poll_id": 1,
            "question": "What's your favorite programming language?",
            "results": [
                {"option_id": 1, "text": "Python", "vote_count": 15},
                {"option_id": 2, "text": "JavaScript", "vote_count": 10},
                {"option_id": 3, "text": "Java", "vote_count": 5},
                {"option_id": 4, "text": "Go", "vote_count": 3}
            ]
        }

    @patch('poll_results.requests.get')
    def test_successful_results_retrieval(self, mock_get):
        """Test successful poll results retrieval"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_results_response
        mock_get.return_value = mock_response

        # Call the function
        result = get_poll_results(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert results
        self.assertTrue(result.success)
        self.assertIsNotNone(result.results_data)
        if result.results_data is not None:
            self.assertEqual(result.results_data["poll_id"], 1)
            self.assertEqual(result.results_data["question"], "What's your favorite programming language?")
            self.assertEqual(len(result.results_data["results"]), 4)
            self.assertEqual(result.results_data["results"][0]["text"], "Python")
            self.assertEqual(result.results_data["results"][0]["vote_count"], 15)
        self.assertEqual(result.status_code, 200)
        self.assertIsNone(result.error_message)

        # Verify the request was made correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertIsNotNone(call_args)
        if call_args is not None:
            self.assertEqual(call_args[1]['url'], f"{self.base_url}/polls/{self.valid_poll_id}/results")
            self.assertIn('Accept', call_args[1]['headers'])
            self.assertEqual(call_args[1]['headers']['Accept'], "application/json")

    @patch('poll_results.requests.get')
    def test_poll_not_found(self, mock_get):
        """Test results retrieval for non-existent poll"""
        # Mock 404 Not Found response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "detail": "Poll not found"
        }
        mock_get.return_value = mock_response

        # Call the function
        result = get_poll_results(poll_id=999, base_url=self.base_url)

        # Assert results
        self.assertFalse(result.success)
        self.assertIsNone(result.results_data)
        self.assertEqual(result.status_code, 404)
        self.assertEqual(result.error_message, "Poll not found")

    @patch('poll_results.requests.get')
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
        result = get_poll_results(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert results
        self.assertFalse(result.success)
        self.assertIsNone(result.results_data)
        self.assertEqual(result.status_code, 500)
        self.assertIsNotNone(result.error_message)
        if result.error_message is not None:
            self.assertIn("500", result.error_message)

    @patch('poll_results.requests.get')
    def test_invalid_json_response(self, mock_get):
        """Test handling of invalid JSON response"""
        # Mock response with invalid JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_get.return_value = mock_response

        # Call the function and expect an exception
        with self.assertRaises(PollResultsError) as context:
            get_poll_results(poll_id=self.valid_poll_id, base_url=self.base_url)

        self.assertIn("Failed to parse JSON response", str(context.exception))

    @patch('poll_results.requests.get')
    def test_connection_error(self, mock_get):
        """Test handling of connection errors"""
        # Mock connection error
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        # Call the function and expect an exception
        with self.assertRaises(PollResultsError) as context:
            get_poll_results(poll_id=self.valid_poll_id, base_url=self.base_url)

        self.assertIn("Failed to connect to the API", str(context.exception))

    @patch('poll_results.requests.get')
    def test_timeout_error(self, mock_get):
        """Test handling of timeout errors"""
        # Mock timeout error
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        # Call the function and expect an exception
        with self.assertRaises(PollResultsError) as context:
            get_poll_results(poll_id=self.valid_poll_id, base_url=self.base_url)

        self.assertIn("Request timed out after 30 seconds", str(context.exception))

    def test_invalid_poll_id_validation(self):
        """Test validation of poll_id parameter"""
        with self.assertRaises(ValueError) as context:
            get_poll_results(poll_id=0)
        self.assertIn("Poll ID must be a positive integer", str(context.exception))

        with self.assertRaises(ValueError) as context:
            get_poll_results(poll_id=-1)
        self.assertIn("Poll ID must be a positive integer", str(context.exception))

        with self.assertRaises(ValueError) as context:
            get_poll_results(poll_id="invalid")  # type: ignore[arg-type]
        self.assertIn("Poll ID must be a positive integer", str(context.exception))

    @patch('poll_results.requests.get')
    def test_simple_results_success(self, mock_get):
        """Test the simple results function with success"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_results_response
        mock_get.return_value = mock_response

        # Call the simple function
        results_data = get_poll_results_simple(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert results
        self.assertIsNotNone(results_data)
        self.assertEqual(results_data["poll_id"], 1)
        self.assertEqual(results_data["question"], "What's your favorite programming language?")
        self.assertEqual(len(results_data["results"]), 4)

    @patch('poll_results.requests.get')
    def test_simple_results_failure(self, mock_get):
        """Test the simple results function with failure"""
        # Mock 404 Not Found response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {
            "detail": "Poll not found"
        }
        mock_get.return_value = mock_response

        # Call the simple function and expect an exception
        with self.assertRaises(PollResultsError) as context:
            get_poll_results_simple(poll_id=999, base_url=self.base_url)

        self.assertIn("Poll results retrieval failed", str(context.exception))

    @patch('poll_results.requests.get')
    def test_get_poll_winner(self, mock_get):
        """Test getting the poll winner"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_results_response
        mock_get.return_value = mock_response

        # Call the winner function
        winner = get_poll_winner(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert results
        self.assertIsNotNone(winner)
        if winner is not None:
            self.assertEqual(winner["text"], "Python")
            self.assertEqual(winner["vote_count"], 15)
            self.assertEqual(winner["option_id"], 1)

    @patch('poll_results.requests.get')
    def test_get_poll_winner_no_votes(self, mock_get):
        """Test getting winner when no votes exist"""
        # Mock response with no votes
        no_votes_response = {
            "poll_id": 1,
            "question": "Test poll",
            "results": [
                {"option_id": 1, "text": "Option 1", "vote_count": 0},
                {"option_id": 2, "text": "Option 2", "vote_count": 0}
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = no_votes_response
        mock_get.return_value = mock_response

        # Call the winner function
        winner = get_poll_winner(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert no winner
        self.assertIsNone(winner)

    @patch('poll_results.requests.get')
    def test_get_poll_winner_tie(self, mock_get):
        """Test getting winner when there's a tie"""
        # Mock response with tie
        tie_response = {
            "poll_id": 1,
            "question": "Test poll",
            "results": [
                {"option_id": 1, "text": "Option 1", "vote_count": 5},
                {"option_id": 2, "text": "Option 2", "vote_count": 5}
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = tie_response
        mock_get.return_value = mock_response

        # Call the winner function
        winner = get_poll_winner(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert it returns first winner in case of tie
        self.assertIsNotNone(winner)
        if winner is not None:
            self.assertEqual(winner["text"], "Option 1")
            self.assertEqual(winner["vote_count"], 5)

    @patch('poll_results.requests.get')
    def test_get_poll_statistics(self, mock_get):
        """Test getting poll statistics"""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_results_response
        mock_get.return_value = mock_response

        # Call the statistics function
        stats = get_poll_statistics(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert results
        self.assertEqual(stats["poll_id"], 1)
        self.assertEqual(stats["question"], "What's your favorite programming language?")
        self.assertEqual(stats["total_votes"], 33)  # 15 + 10 + 5 + 3
        self.assertEqual(stats["options_count"], 4)

        # Check winner
        self.assertIsNotNone(stats["winner"])
        if stats["winner"] is not None:
            self.assertEqual(stats["winner"]["text"], "Python")
            self.assertEqual(stats["winner"]["vote_count"], 15)
            self.assertEqual(stats["winner"]["percentage"], 45.5)  # 15/33 * 100 rounded

        # Check options are sorted by vote count
        options = stats["options_with_percentages"]
        self.assertEqual(len(options), 4)
        self.assertEqual(options[0]["text"], "Python")
        self.assertEqual(options[0]["vote_count"], 15)
        self.assertEqual(options[1]["text"], "JavaScript")
        self.assertEqual(options[1]["vote_count"], 10)

    @patch('poll_results.requests.get')
    def test_get_poll_statistics_no_votes(self, mock_get):
        """Test getting statistics when no votes exist"""
        # Mock response with no votes
        no_votes_response = {
            "poll_id": 1,
            "question": "Test poll",
            "results": []
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = no_votes_response
        mock_get.return_value = mock_response

        # Call the statistics function
        stats = get_poll_statistics(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert results
        self.assertEqual(stats["poll_id"], 1)
        self.assertEqual(stats["total_votes"], 0)
        self.assertEqual(stats["options_count"], 0)
        self.assertIsNone(stats["winner"])
        self.assertEqual(len(stats["options_with_percentages"]), 0)

    @patch('poll_results.requests.get')
    def test_response_validation_missing_fields(self, mock_get):
        """Test response validation with missing fields"""
        # Mock response with missing fields
        incomplete_response = {
            "poll_id": 1,
            # Missing question and results
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = incomplete_response
        mock_get.return_value = mock_response

        # Call the function - should succeed but log warnings
        result = get_poll_results(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert it still succeeds (just logs warnings)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.results_data)

    @patch('poll_results.requests.get')
    def test_response_validation_wrong_poll_id(self, mock_get):
        """Test response validation when poll_id doesn't match request"""
        # Mock response with wrong poll_id
        wrong_response = {
            "poll_id": 999,  # Different from requested poll_id
            "question": "Wrong poll",
            "results": []
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = wrong_response
        mock_get.return_value = mock_response

        # Call the function - should succeed but log warning
        result = get_poll_results(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert it still succeeds (just logs warning)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.results_data)

    @patch('poll_results.requests.get')
    def test_response_validation_malformed_results(self, mock_get):
        """Test response validation with malformed results array"""
        # Mock response with malformed results
        malformed_response = {
            "poll_id": 1,
            "question": "Test poll",
            "results": [
                {"option_id": 1, "text": "Good option", "vote_count": 5},
                {"option_id": "invalid", "text": 123, "vote_count": "not_a_number"},  # Invalid types
                {"text": "Missing option_id"},  # Missing required field
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = malformed_response
        mock_get.return_value = mock_response

        # Call the function - should succeed but log warnings
        result = get_poll_results(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert it still succeeds (just logs warnings)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.results_data)

    @patch('poll_results.requests.get')
    def test_response_validation_negative_vote_count(self, mock_get):
        """Test response validation with negative vote counts"""
        # Mock response with negative vote count
        negative_response = {
            "poll_id": 1,
            "question": "Test poll",
            "results": [
                {"option_id": 1, "text": "Option 1", "vote_count": -5}  # Negative votes
            ]
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = negative_response
        mock_get.return_value = mock_response

        # Call the function - should succeed but log warning
        result = get_poll_results(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert it still succeeds (just logs warning)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.results_data)

    @patch('poll_results.requests.get')
    def test_error_response_without_detail(self, mock_get):
        """Test handling of error responses without detail field"""
        # Mock error response without detail
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": "Bad request"}
        mock_response.text = "Bad request text"
        mock_get.return_value = mock_response

        # Call the function
        result = get_poll_results(poll_id=self.valid_poll_id, base_url=self.base_url)

        # Assert results
        self.assertFalse(result.success)
        self.assertEqual(result.status_code, 400)
        self.assertIsNotNone(result.error_message)


def run_integration_tests():
    """
    Integration tests that actually call the API.
    Only run these if the API server is running.
    """
    print("\n" + "="*50)
    print("INTEGRATION TESTS")
    print("="*50)
    print("Note: These tests require:")
    print("1. API server running at http://localhost:8000")
    print("2. Existing polls with some votes")

    base_url = "http://localhost:8000"

    # Test 1: Get results for existing poll
    print("\n1. Testing poll results retrieval...")
    try:
        poll_id = int(input("Enter a poll ID to get results for: "))

        result = get_poll_results(poll_id=poll_id, base_url=base_url)

        if result.success and result.results_data is not None:
            print(f"✅ SUCCESS: Retrieved results for poll {poll_id}")
            results_data = result.results_data
            print(f"   Question: {results_data['question']}")
            print(f"   Options: {len(results_data.get('results', []))}")

            total_votes = 0
            if 'results' in results_data:
                print("   Results:")
                for option in results_data['results']:
                    votes = option.get('vote_count', 0)
                    print(f"     - {option.get('text')}: {votes} votes")
                    total_votes += votes

            print(f"   Total votes: {total_votes}")
        else:
            print(f"❌ FAILED: {result.error_message}")
            print(f"   Status Code: {result.status_code}")

    except PollResultsError as e:
        print(f"❌ ERROR: {e}")
    except ValueError as e:
        print(f"❌ INPUT ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

    # Test 2: Try to get results for non-existent poll
    print("\n2. Testing results for non-existent poll...")
    try:
        result = get_poll_results(poll_id=99999, base_url=base_url)

        if not result.success and result.status_code == 404:
            print("✅ SUCCESS: Correctly handled non-existent poll")
            print(f"   Error: {result.error_message}")
        else:
            print("❌ UNEXPECTED: Should have failed with 404")

    except PollResultsError as e:
        print(f"❌ ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

    # Test 3: Test simple results function
    print("\n3. Testing simple results function...")
    try:
        poll_id = int(input("Enter another poll ID for simple test: "))

        results_data = get_poll_results_simple(poll_id=poll_id, base_url=base_url)
        print("✅ SUCCESS: Simple results retrieval worked")
        print(f"   Question: {results_data['question']}")
        print(f"   Options: {len(results_data.get('results', []))}")

    except PollResultsError as e:
        print(f"❌ FAILED: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

    # Test 4: Test winner function
    print("\n4. Testing winner detection...")
    try:
        poll_id = int(input("Enter a poll ID to find the winner: "))

        winner = get_poll_winner(poll_id=poll_id, base_url=base_url)

        if winner:
            print("✅ SUCCESS: Winner found!")
            print(f"   Winning option: {winner['text']}")
            print(f"   Vote count: {winner['vote_count']}")
        else:
            print("ℹ️  No winner found (no votes or tie)")

    except (PollResultsError, ValueError) as e:
        print(f"❌ FAILED: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")

    # Test 5: Test statistics function
    print("\n5. Testing statistics calculation...")
    try:
        poll_id = int(input("Enter a poll ID for statistics: "))

        stats = get_poll_statistics(poll_id=poll_id, base_url=base_url)

        print("✅ SUCCESS: Statistics calculated!")
        print(f"   Question: {stats['question']}")
        print(f"   Total votes: {stats['total_votes']}")
        print(f"   Options count: {stats['options_count']}")

        if stats['winner']:
            winner = stats['winner']
            print(f"   Winner: {winner['text']} with {winner['vote_count']} votes ({winner['percentage']}%)")

        print("   Detailed breakdown:")
        for option in stats['options_with_percentages']:
            print(f"     - {option['text']}: {option['vote_count']} votes ({option['percentage']}%)")

    except (PollResultsError, ValueError) as e:
        print(f"❌ FAILED: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")


def main():
    """Main function to run all tests"""
    print("POLL RESULTS TESTING SUITE")
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
from poll_results import get_poll_results

result = get_poll_results(poll_id=1)
if result.success:
    print(f"Question: {result.results_data['question']}")
    for option in result.results_data['results']:
        print(f"- {option['text']}: {option['vote_count']} votes")
else:
    print(f"Failed: {result.error_message}")

# Example 2: Simple usage (raises exception on failure)
from poll_results import get_poll_results_simple

try:
    results = get_poll_results_simple(poll_id=1)
    total_votes = sum(opt['vote_count'] for opt in results['results'])
    print(f"Total votes: {total_votes}")
except PollResultsError as e:
    print(f"Failed: {e}")

# Example 3: Get poll winner
from poll_results import get_poll_winner

try:
    winner = get_poll_winner(poll_id=1)
    if winner:
        print(f"Winner: {winner['text']} with {winner['vote_count']} votes")
    else:
        print("No winner yet")
except PollResultsError as e:
    print(f"Failed: {e}")

# Example 4: Get detailed statistics
from poll_results import get_poll_statistics

try:
    stats = get_poll_statistics(poll_id=1)
    print(f"Total votes: {stats['total_votes']}")
    print(f"Winner: {stats['winner']['text']} ({stats['winner']['percentage']}%)")

    for option in stats['options_with_percentages']:
        print(f"- {option['text']}: {option['percentage']}%")
except PollResultsError as e:
    print(f"Failed: {e}")

# Example 5: Custom base URL
result = get_poll_results(poll_id=1, base_url="https://api.example.com")
    """)


if __name__ == "__main__":
    main()
