import requests
import logging
from typing import Dict, Optional, Any
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VoteCastError(Exception):
    """Custom exception for vote casting errors"""
    pass

class VoteCastResponse:
    """Response object for vote casting"""
    def __init__(self, success: bool, vote_data: Optional[Dict[str, Any]] = None,
                 error_message: Optional[str] = None, status_code: Optional[int] = None):
        self.success = success
        self.vote_data = vote_data
        self.error_message = error_message
        self.status_code = status_code

def cast_vote(poll_id: int, option_id: int, access_token: str,
              base_url: str = "http://localhost:8000") -> VoteCastResponse:
    """
    Cast or update a user's vote on a specific poll option.

    This function implements the core democratic participation mechanism of the polling
    platform. It allows authenticated users to express their preferences by voting on
    poll options. The function handles the complete voting lifecycle including vote
    creation, updates (if the user changes their mind), authentication verification,
    and comprehensive error handling for production reliability.

    Business Intent:
        - Enable democratic participation through secure vote casting
        - Support vote updates allowing users to change their minds
        - Ensure vote integrity through proper authentication
        - Provide detailed feedback for user experience and debugging
        - Support different deployment environments and configurations
        - Maintain audit trail through comprehensive logging

    Use Cases:
        - Primary voting interface in web and mobile applications
        - Real-time polling during live events or presentations
        - Anonymous feedback collection with authenticated participation
        - Decision-making tools for teams and organizations
        - Survey completion with option selection
        - Integration testing of voting workflows
        - Multi-environment deployments requiring different API endpoints

    Args:
        poll_id (int): Unique identifier of the poll to vote on. Must correspond to
                      an existing, accessible poll. This links the vote to the specific
                      question or decision being made.
        option_id (int): Unique identifier of the chosen option within the poll.
                        Must belong to the specified poll. This represents the user's
                        actual choice or preference.
        access_token (str): JWT authentication token proving user identity and
                           authorization. Required for vote attribution and preventing
                           unauthorized voting. Should be obtained from successful login.
        base_url (str): API server endpoint URL. Critical for multi-environment
                       support (dev/staging/prod) and when API servers run on
                       different hosts or ports.

    Returns:
        VoteCastResponse: Comprehensive response object enabling detailed handling:
            - success (bool): Whether vote was successfully recorded
            - vote_data (dict): Vote details including ID, user_id, option_id, timestamp
            - status_code (int): HTTP response code for debugging and logging
            - error_message (str): Human-readable error description for user feedback

        This rich response supports various UX patterns:
        - Success confirmations with vote details
        - Specific error messages for different failure scenarios
        - Logging and analytics data collection
        - Retry logic based on error types

    Raises:
        ValueError: Input validation failed (invalid IDs, empty token). Indicates
                   programming errors that should be caught during development.
        VoteCastError: Network or server issues preventing vote submission:
                      - Connection timeouts (implement retry with exponential backoff)
                      - Authentication failures (redirect to login)
                      - Server errors (show generic error, log details)
                      - Invalid responses (check API compatibility)
    """

    # Validate input parameters
    if not isinstance(poll_id, int) or poll_id <= 0:
        raise ValueError("Poll ID must be a positive integer")

    if not isinstance(option_id, int) or option_id <= 0:
        raise ValueError("Option ID must be a positive integer")

    if not access_token or not isinstance(access_token, str):
        raise ValueError("Access token must be a non-empty string")

    # Prepare the request
    url = f"{base_url.rstrip('/')}/polls/{poll_id}/vote"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token.strip()}"
    }

    request_body = {
        "option_id": option_id
    }

    logger.info(f"Attempting to cast vote for poll {poll_id}, option {option_id}")

    try:
        # Make the POST request
        response = requests.post(
            url=url,
            json=request_body,
            headers=headers,
            timeout=30  # 30 second timeout
        )

        # Log the response for debugging
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")

        # Handle successful vote casting (200)
        if response.status_code == 200:
            try:
                vote_data = response.json()
                logger.info(f"Vote cast successfully: vote ID {vote_data.get('id')}")

                # Validate response structure matches VoteOut schema
                expected_fields = ['id', 'user_id', 'option_id', 'created_at']
                missing_fields = [field for field in expected_fields if field not in vote_data]

                if missing_fields:
                    logger.warning(f"Response missing expected fields: {missing_fields}")

                # Validate data types
                if 'id' in vote_data and not isinstance(vote_data['id'], int):
                    logger.warning("Vote ID should be an integer")

                if 'user_id' in vote_data and not isinstance(vote_data['user_id'], int):
                    logger.warning("User ID should be an integer")

                if 'option_id' in vote_data and not isinstance(vote_data['option_id'], int):
                    logger.warning("Option ID should be an integer")

                # Validate created_at format
                if 'created_at' in vote_data:
                    try:
                        datetime.fromisoformat(vote_data['created_at'].replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        logger.warning("Invalid created_at format in vote response")

                # Verify the option_id matches what we requested
                if vote_data.get('option_id') != option_id:
                    logger.warning(f"Response option_id {vote_data.get('option_id')} doesn't match requested {option_id}")

                return VoteCastResponse(
                    success=True,
                    vote_data=vote_data,
                    status_code=response.status_code
                )

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON response: {e}"
                logger.error(error_msg)
                raise VoteCastError(error_msg)

        # Handle unauthorized access (401)
        elif response.status_code == 401:
            error_msg = "Unauthorized: Invalid or expired access token"
            logger.warning(f"Vote casting failed for poll {poll_id}: {error_msg}")

            # Try to get more detailed error message from response
            try:
                error_detail = response.json()
                if isinstance(error_detail, dict) and 'detail' in error_detail:
                    error_msg = error_detail['detail']
            except (json.JSONDecodeError, KeyError):
                # Use default error message if response parsing fails
                pass

            return VoteCastResponse(
                success=False,
                error_message=error_msg,
                status_code=response.status_code
            )

        # Handle poll or option not found (404)
        elif response.status_code == 404:
            error_msg = "Poll or option not found"
            logger.warning(f"Vote casting failed for poll {poll_id}: {error_msg}")

            # Try to get more detailed error message from response
            try:
                error_detail = response.json()
                if isinstance(error_detail, dict) and 'detail' in error_detail:
                    error_msg = error_detail['detail']
            except (json.JSONDecodeError, KeyError):
                # Use default error message if response parsing fails
                pass

            return VoteCastResponse(
                success=False,
                error_message=error_msg,
                status_code=response.status_code
            )

        # Handle other HTTP errors
        else:
            error_msg = f"HTTP {response.status_code}: Failed to cast vote"
            try:
                error_detail = response.json()
                if isinstance(error_detail, dict) and 'detail' in error_detail:
                    error_msg += f" - {error_detail['detail']}"
            except json.JSONDecodeError:
                error_msg += f" - {response.text[:200]}"  # Limit error text length

            logger.error(f"Vote casting failed for poll {poll_id}: {error_msg}")

            return VoteCastResponse(
                success=False,
                error_message=error_msg,
                status_code=response.status_code
            )

    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 30 seconds"
        logger.error(f"Vote casting failed for poll {poll_id}: {error_msg}")
        raise VoteCastError(error_msg)

    except requests.exceptions.ConnectionError:
        error_msg = f"Failed to connect to the API at {url}"
        logger.error(f"Vote casting failed for poll {poll_id}: {error_msg}")
        raise VoteCastError(error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {e}"
        logger.error(f"Vote casting failed for poll {poll_id}: {error_msg}")
        raise VoteCastError(error_msg)

def cast_vote_simple(poll_id: int, option_id: int, access_token: str,
                     base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Cast a vote with streamlined error handling for straightforward voting scenarios.

    This simplified interface eliminates response object handling when you only need
    the vote confirmation data. It follows "fail-fast" principles - either return
    the vote details or raise an exception. This makes it ideal for simple voting
    interfaces, functional programming patterns, and scenarios where detailed error
    analysis isn't required.

    Business Intent:
        - Provide clean, minimal API for basic voting functionality
        - Reduce boilerplate code in simple voting implementations
        - Enable rapid development of voting features
        - Support exception-based error handling patterns
        - Simplify testing when only success/failure matters
        - Facilitate integration in microservices with centralized error handling

    Use Cases:
        - Simple voting buttons that show generic success/error messages
        - Mobile app voting where failures should halt the voting flow
        - Quick voting implementations in prototypes and demos
        - Batch voting operations where any failure should stop processing
        - Command-line voting tools and administrative scripts
        - Functional programming chains where exceptions propagate naturally
        - Microservices where error handling is centralized upstream

    Args:
        poll_id (int): Target poll identifier. Must exist and be accessible to user.
        option_id (int): Chosen option within the poll. Must belong to specified poll.
        access_token (str): User authentication token from login process.
        base_url (str): API server URL for multi-environment support.

    Returns:
        Dict[str, Any]: Essential vote confirmation data:
            - 'id' (int): Unique vote record ID for auditing and tracking
            - 'user_id' (int): ID of the voting user for verification
            - 'option_id' (int): Confirms the selected option
            - 'created_at' (str): Timestamp of vote submission for audit trails

        This minimal return focuses on vote verification and audit trail essentials.

    Raises:
        ValueError: Invalid input parameters. Fix calling code to provide valid values.
        VoteCastError: Any voting failure including:
                      - Authentication issues (redirect to login)
                      - Poll/option not found (refresh poll data)
                      - Server errors (retry or show error message)
                      - Network failures (check connectivity)

        Exception messages contain specific failure details for user notifications.
    """

    result = cast_vote(poll_id, option_id, access_token, base_url)

    if result.success and result.vote_data is not None:
        return result.vote_data
    else:
        error_msg = result.error_message or "Unknown error"
        raise VoteCastError(f"Vote casting failed: {error_msg}")

def get_user_vote_on_poll(poll_id: int, access_token: str,
                          base_url: str = "http://localhost:8000") -> Optional[Dict[str, Any]]:
    """
    Check if the authenticated user has already participated in a specific poll.

    This utility function enables applications to show appropriate voting interfaces
    based on user participation status. It helps create better user experiences by
    distinguishing between first-time voting and vote updates. While currently a
    placeholder implementation, it represents an important pattern for voting UX.

    Business Intent:
        - Enable contextual voting interfaces (vote vs. update vote)
        - Support user experience personalization based on participation history
        - Provide foundation for voting analytics and engagement tracking
        - Enable audit trail functionality for compliance and transparency
        - Support different UI states based on user voting status
        - Facilitate A/B testing of voting interfaces

    Use Cases:
        - Show "Vote" vs. "Change Vote" buttons based on participation status
        - Display user's current vote selection in voting interfaces
        - Analytics dashboards showing user engagement patterns
        - Audit interfaces for election integrity verification
        - User profile pages showing voting history
        - Compliance reporting for regulated voting scenarios
        - Testing scenarios validating voting state consistency

    Implementation Note:
        This is currently a placeholder returning None, as the current API spec
        doesn't include a direct endpoint for user voting history. A full
        implementation would likely query user-specific voting data or poll
        results with user filtering.

    Args:
        poll_id (int): Poll to check for user participation. Must be a valid,
                      accessible poll ID.
        access_token (str): User authentication token to identify which user's
                           voting status to check. Must be valid and not expired.
        base_url (str): API server endpoint for the voting status query.

    Returns:
        Optional[Dict[str, Any]]: User's vote data if they have voted:
            - 'id': Vote record ID
            - 'option_id': Which option the user selected
            - 'created_at': When they voted
            Returns None if user hasn't voted on this poll yet.

    Raises:
        ValueError: Invalid poll ID or empty access token.
        VoteCastError: Network/server issues preventing status check:
                      - Authentication failures
                      - Server errors
                      - Network connectivity issues
    """

    if not isinstance(poll_id, int) or poll_id <= 0:
        raise ValueError("Poll ID must be a positive integer")

    if not access_token or not isinstance(access_token, str):
        raise ValueError("Access token must be a non-empty string")

    # This is a placeholder implementation since the API spec doesn't include
    # a direct endpoint to get current user's votes. In a real implementation,
    # you might need to fetch poll results and cross-reference with user info.

    logger.info(f"Checking if user has voted on poll {poll_id}")

    # Note: Implementation would depend on available endpoints
    # For now, this returns None indicating we can't determine voting status
    return None

# Example usage and testing functions
def main():
    """
    Demonstrate vote casting patterns and serve as integration validation.

    This comprehensive demonstration function showcases different approaches to
    vote casting and serves multiple purposes in the development lifecycle. It
    acts as living documentation through working examples, integration testing
    to verify the voting system works end-to-end, and a reference for developers
    implementing voting functionality.

    Business Intent:
        - Provide clear implementation examples for different voting scenarios
        - Validate that voting APIs are accessible and functioning correctly
        - Document best practices for authentication and error handling
        - Serve as a quick manual test during development and deployment
        - Help developers understand when to use each function variant
        - Demonstrate proper user experience patterns for voting interfaces

    The examples demonstrate:
        1. Detailed response handling for robust voting applications
        2. Simple voting for straightforward use cases
        3. Authentication token usage and security considerations
        4. Comprehensive error handling strategies for different failure modes
        5. Input validation patterns and user feedback approaches
        6. Integration patterns for voting in larger applications

    This helps developers make informed decisions about which functions to use
    and how to provide excellent user experience through proper vote handling,
    error messaging, and state management in voting interfaces.
    """

    # Note: You'll need a valid access token for these examples to work
    sample_token = "your_jwt_token_here"  # Replace with actual token

    print("VOTE CASTING EXAMPLES")
    print("="*50)
    print("Note: These examples require a valid JWT access token")
    print("="*50)

    # Example 1: Using the detailed response function
    try:
        result = cast_vote(poll_id=1, option_id=2, access_token=sample_token)

        if result.success and result.vote_data is not None:
            print("✅ Vote cast successfully!")
            vote_data = result.vote_data
            print(f"   Vote ID: {vote_data['id']}")
            print(f"   User ID: {vote_data['user_id']}")
            print(f"   Option ID: {vote_data['option_id']}")
            print(f"   Cast at: {vote_data['created_at']}")
        else:
            error_msg = result.error_message or "Unknown error"
            print(f"❌ Vote casting failed: {error_msg}")
            if result.status_code:
                print(f"   Status Code: {result.status_code}")

    except VoteCastError as e:
        print(f"❌ Vote casting error: {e}")
    except ValueError as e:
        print(f"❌ Invalid input: {e}")

    print("\n" + "="*50 + "\n")

    # Example 2: Using the simple function
    try:
        vote_data = cast_vote_simple(poll_id=1, option_id=3, access_token=sample_token)
        print("✅ Simple vote casting successful!")
        print(f"   Vote ID: {vote_data['id']}")
        print(f"   Option chosen: {vote_data['option_id']}")

    except VoteCastError as e:
        print(f"❌ Simple vote casting failed: {e}")

    print("\n" + "="*50 + "\n")

    # Example 3: Error handling demonstration
    try:
        # This should fail with invalid token
        result = cast_vote(poll_id=1, option_id=1, access_token="invalid_token")

        if not result.success:
            print(f"✅ Error handling working correctly: {result.error_message}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("\n" + "="*50 + "\n")

    # Example 4: Input validation
    try:
        # This should raise ValueError
        cast_vote(poll_id=-1, option_id=1, access_token="token")
    except ValueError as e:
        print(f"✅ Input validation working: {e}")

    try:
        # This should raise ValueError
        cast_vote(poll_id=1, option_id=0, access_token="token")
    except ValueError as e:
        print(f"✅ Input validation working: {e}")

    try:
        # This should raise ValueError
        cast_vote(poll_id=1, option_id=1, access_token="")
    except ValueError as e:
        print(f"✅ Input validation working: {e}")

if __name__ == "__main__":
    main()
