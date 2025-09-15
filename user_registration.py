import requests
import logging
from typing import Dict, Optional, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserRegistrationError(Exception):
    """Custom exception for user registration errors"""
    pass

class UserRegistrationResponse:
    """Response object for user registration"""
    def __init__(self, success: bool, user_data: Optional[Dict] = None,
                 error_message: Optional[str] = None, status_code: Optional[int] = None):
        self.success = success
        self.user_data = user_data
        self.error_message = error_message
        self.status_code = status_code

def register_user(username: str, password: str, base_url: str = "http://localhost:8000") -> UserRegistrationResponse:
    """
    Register a new user account in the polling system.

    This function handles the complete user onboarding process for the Polly application.
    It creates new user accounts that can participate in polls by voting and creating
    their own polls. The registration process validates credentials, communicates with
    the backend API, and provides detailed feedback about success or failure.

    Business Intent:
        - Enable new users to join the polling platform
        - Validate user credentials meet system requirements
        - Provide detailed error information for troubleshooting
        - Support different deployment environments via configurable base_url
        - Ensure robust error handling for production use

    Use Cases:
        - User self-registration through web forms
        - Admin bulk user creation
        - Integration testing with detailed result inspection
        - Multi-environment deployments (dev, staging, prod)

    Args:
        username (str): Unique identifier for the user account. Must be non-empty and
                       not already exist in the system. This will be used for login
                       and identifying the user in polls they create or vote on.
        password (str): User's chosen password for account security. Must be non-empty.
                       Consider enforcing password complexity requirements at the UI level.
        base_url (str): API server endpoint. Defaults to local development server.
                       Change this for staging/production deployments or when the
                       API server runs on a different host/port.

    Returns:
        UserRegistrationResponse: Comprehensive result object containing:
            - success (bool): Whether registration completed successfully
            - user_data (dict): User account details (id, username) on success
            - error_message (str): Human-readable error description on failure
            - status_code (int): HTTP status code for debugging/logging

        This detailed response allows callers to handle different scenarios:
        - Show success messages with new user ID
        - Display specific error messages to users
        - Log failures with HTTP status codes for debugging
        - Retry logic based on error types

    Raises:
        ValueError: When input parameters are invalid (empty strings, wrong types).
                   This indicates a programming error that should be caught during
                   development and testing.
        UserRegistrationError: When network/server issues prevent registration.
                              This includes timeouts, connection failures, and
                              unexpected server responses that require retry logic
                              or user notification.
    """

    # Validate input parameters
    if not username or not isinstance(username, str):
        raise ValueError("Username must be a non-empty string")

    if not password or not isinstance(password, str):
        raise ValueError("Password must be a non-empty string")

    # Prepare the request
    url = f"{base_url.rstrip('/')}/register"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    request_body = {
        "username": username,
        "password": password
    }

    logger.info(f"Attempting to register user: {username}")

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

        # Handle successful registration (200)
        if response.status_code == 200:
            try:
                user_data = response.json()
                logger.info(f"User '{username}' registered successfully with ID: {user_data.get('id')}")

                # Validate response structure matches UserOut schema
                if 'id' not in user_data or 'username' not in user_data:
                    logger.warning("Response missing expected fields (id, username)")

                return UserRegistrationResponse(
                    success=True,
                    user_data=user_data,
                    status_code=response.status_code
                )

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON response: {e}"
                logger.error(error_msg)
                raise UserRegistrationError(error_msg)

        # Handle username already registered (400)
        elif response.status_code == 400:
            error_msg = "Username already registered"
            logger.warning(f"Registration failed for '{username}': {error_msg}")

            # Try to get more detailed error message from response
            try:
                error_detail = response.json()
                if isinstance(error_detail, dict) and 'detail' in error_detail:
                    error_msg = error_detail['detail']
            except (json.JSONDecodeError, KeyError):
                # Use default error message if response parsing fails
                pass

            return UserRegistrationResponse(
                success=False,
                error_message=error_msg,
                status_code=response.status_code
            )

        # Handle other HTTP errors
        else:
            error_msg = f"Unexpected HTTP status code: {response.status_code}"
            try:
                error_detail = response.json()
                if isinstance(error_detail, dict) and 'detail' in error_detail:
                    error_msg += f" - {error_detail['detail']}"
            except json.JSONDecodeError:
                error_msg += f" - {response.text}"

            logger.error(f"Registration failed for '{username}': {error_msg}")

            return UserRegistrationResponse(
                success=False,
                error_message=error_msg,
                status_code=response.status_code
            )

    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 30 seconds"
        logger.error(f"Registration failed for '{username}': {error_msg}")
        raise UserRegistrationError(error_msg)

    except requests.exceptions.ConnectionError:
        error_msg = f"Failed to connect to the API at {url}"
        logger.error(f"Registration failed for '{username}': {error_msg}")
        raise UserRegistrationError(error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {e}"
        logger.error(f"Registration failed for '{username}': {error_msg}")
        raise UserRegistrationError(error_msg)

def register_user_simple(username: str, password: str, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Register a user with simplified error handling for "fail-fast" scenarios.

    This is a convenience wrapper around register_user() designed for use cases where
    you want straightforward success/failure behavior without detailed error analysis.
    It follows the principle of "fail fast" - either return the user data or raise
    an exception, making it ideal for scripts, quick integrations, and scenarios
    where detailed error handling isn't needed.

    Business Intent:
        - Provide a simple API for basic user registration needs
        - Reduce boilerplate code when detailed error handling isn't required
        - Enable quick prototyping and scripting
        - Support functional programming patterns with exception-based control flow
        - Simplify integration in contexts where try/catch is preferred over status checking

    Use Cases:
        - Command-line tools and scripts
        - Batch user creation where failures should halt processing
        - Simple web form handlers where generic error pages are acceptable
        - Testing scenarios where you only care about success/failure
        - Microservice integrations with centralized error handling
        - Functional programming chains where exceptions propagate naturally

    Args:
        username (str): Unique identifier for the new user account. Same validation
                       rules as register_user() - must be non-empty and unique.
        password (str): User's password. Same requirements as register_user().
        base_url (str): API endpoint URL. Useful for testing against different
                       environments or when API server location varies.

    Returns:
        Dict[str, Any]: User account data directly from successful registration:
            - 'id' (int): Unique user ID assigned by the system
            - 'username' (str): Confirmed username (should match input)

        This minimal return focuses on the essential data needed after registration:
        the user ID for future API calls and username confirmation.

    Raises:
        ValueError: Input validation failed (empty/invalid parameters). Fix the
                   calling code to provide valid inputs.
        UserRegistrationError: Registration failed for any reason including:
                               - Username already exists (user should try another)
                               - Network connectivity issues (retry may help)
                               - Server errors (check server status/logs)
                               - Invalid API responses (check API compatibility)

        The exception message contains details about the specific failure for
        logging or user notification purposes.
    """

    result = register_user(username, password, base_url)

    if result.success and result.user_data is not None:
        # Type assertion since we've confirmed user_data is not None
        user_data: Dict[str, Any] = result.user_data
        return user_data
    else:
        error_msg = result.error_message or "Unknown error"
        raise UserRegistrationError(f"Registration failed: {error_msg}")

# Example usage and testing functions
def main():
    """
    Demonstrate user registration patterns and serve as integration test.

    This function showcases different approaches to user registration and serves
    multiple purposes in the development lifecycle. It acts as both documentation
    through working examples and as a basic integration test to verify the
    registration system works end-to-end.

    Business Intent:
        - Provide clear usage examples for developers integrating the registration system
        - Serve as a quick manual test during development and deployment
        - Document best practices for error handling and user feedback
        - Validate that the registration API is accessible and functioning

    The examples demonstrate:
        1. Detailed error handling approach using UserRegistrationResponse
        2. Simple approach using register_user_simple with exception handling
        3. Input validation behavior and error messages
        4. Different error scenarios and appropriate responses

    This helps developers understand when to use each function variant and
    how to provide good user experience through proper error handling.
    """

    # Example 1: Using the detailed response function
    try:
        result = register_user("testuser123", "securepassword123")

        if result.success and result.user_data is not None:
            print("Registration successful!")
            # Use temporary variable to satisfy type checker
            user_data = result.user_data
            print(f"User ID: {user_data['id']}")
            print(f"Username: {user_data['username']}")
        else:
            error_msg = result.error_message or "Unknown error"
            print(f"Registration failed: {error_msg}")

    except UserRegistrationError as e:
        print(f"Registration error: {e}")
    except ValueError as e:
        print(f"Invalid input: {e}")

    # Example 2: Using the simple function
    try:
        user_data = register_user_simple("anotheruser456", "anotherpassword456")
        print(f"User registered with ID: {user_data['id']}")

    except UserRegistrationError as e:
        print(f"Registration failed: {e}")

if __name__ == "__main__":
    main()
