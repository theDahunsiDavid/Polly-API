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
    Register a new user via the /register endpoint.

    Args:
        username (str): The username for the new user
        password (str): The password for the new user
        base_url (str): The base URL of the API (default: http://localhost:8000)

    Returns:
        UserRegistrationResponse: Object containing registration result

    Raises:
        UserRegistrationError: If registration fails due to client/server errors
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
    Simplified wrapper function that returns user data directly on success or raises exception on failure.

    Args:
        username (str): The username for the new user
        password (str): The password for the new user
        base_url (str): The base URL of the API (default: http://localhost:8000)

    Returns:
        Dict: User data containing 'id' and 'username' fields

    Raises:
        ValueError: For invalid input parameters
        UserRegistrationError: If registration fails for any reason
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
    """Example usage of the registration functions"""

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
