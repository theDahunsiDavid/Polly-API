import requests
import logging
from typing import List, Dict, Optional, Any
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PollFetchError(Exception):
    """Custom exception for poll fetching errors"""
    pass

class PollFetchResponse:
    """Response object for poll fetching"""
    def __init__(self, success: bool, polls: Optional[List[Dict[str, Any]]] = None,
                 error_message: Optional[str] = None, status_code: Optional[int] = None,
                 total_fetched: int = 0):
        self.success = success
        self.polls = polls or []
        self.error_message = error_message
        self.status_code = status_code
        self.total_fetched = total_fetched

def fetch_polls(skip: int = 0, limit: int = 10, base_url: str = "http://localhost:8000") -> PollFetchResponse:
    """
    Retrieve a paginated list of polls from the polling platform.

    This function implements the core poll discovery mechanism for the application.
    It enables users to browse available polls in manageable chunks, supporting
    scenarios from simple poll listing to complex pagination interfaces. The
    function provides comprehensive error handling and data validation to ensure
    reliable operation in production environments.

    Business Intent:
        - Enable poll discovery and browsing functionality
        - Support scalable pagination for large poll collections
        - Provide detailed response information for robust error handling
        - Allow flexible deployment across different environments
        - Ensure data integrity through response validation

    Use Cases:
        - Main poll listing page with pagination controls
        - Mobile app infinite scroll implementation
        - Admin interfaces for poll management
        - Analytics systems gathering poll metadata
        - Integration testing with controlled data sets
        - Multi-environment deployments (dev/staging/prod)

    Args:
        skip (int): Starting offset for pagination (0-based). Represents how many
                   polls to skip from the beginning. Use (page_number - 1) * limit
                   for traditional page-based pagination. Defaults to 0 for first page.
        limit (int): Maximum polls to return in this request. Controls response size
                    and affects performance. Larger values reduce API calls but increase
                    response time and memory usage. Defaults to 10 for balanced performance.
        base_url (str): API server endpoint. Critical for multi-environment support.
                       Change for staging/production or when API runs on different
                       host/port. Defaults to local development server.

    Returns:
        PollFetchResponse: Comprehensive response object enabling detailed error handling:
            - success (bool): Whether the fetch operation completed successfully
            - polls (list): Array of poll objects with full metadata
            - status_code (int): HTTP response code for debugging/logging
            - total_fetched (int): Number of polls actually retrieved
            - error_message (str): Human-readable error description on failure

        This rich response supports various UI patterns:
        - Success indicators and loading states
        - Detailed error messages for user feedback
        - Logging and debugging information
        - Conditional rendering based on results

    Raises:
        ValueError: Input validation failed (negative skip, non-positive limit).
                   Indicates programming error that should be caught during development.
        PollFetchError: Network or server issues preventing data retrieval:
                       - Connection timeouts (retry with exponential backoff)
                       - Server errors (check API status)
                       - Invalid responses (verify API compatibility)
    """

    # Validate input parameters
    if not isinstance(skip, int) or skip < 0:
        raise ValueError("Skip must be a non-negative integer")

    if not isinstance(limit, int) or limit <= 0:
        raise ValueError("Limit must be a positive integer")

    if limit > 100:
        logger.warning(f"Large limit value ({limit}) may impact performance")

    # Prepare the request
    url = f"{base_url.rstrip('/')}/polls"
    headers = {
        "Accept": "application/json"
    }

    params = {
        "skip": skip,
        "limit": limit
    }

    logger.info(f"Fetching polls with skip={skip}, limit={limit}")

    try:
        # Make the GET request
        response = requests.get(
            url=url,
            params=params,
            headers=headers,
            timeout=30  # 30 second timeout
        )

        # Log the response for debugging
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")

        # Handle successful fetch (200)
        if response.status_code == 200:
            try:
                polls_data = response.json()

                # Validate response is a list
                if not isinstance(polls_data, list):
                    error_msg = f"Expected list response, got {type(polls_data).__name__}"
                    logger.error(error_msg)
                    raise PollFetchError(error_msg)

                logger.info(f"Successfully fetched {len(polls_data)} polls")

                # Validate response structure matches PollOut schema
                validated_polls = []
                for i, poll in enumerate(polls_data):
                    if not isinstance(poll, dict):
                        logger.warning(f"Poll at index {i} is not a dictionary")
                        continue

                    # Check required fields
                    required_fields = ['id', 'question', 'created_at', 'owner_id', 'options']
                    missing_fields = [field for field in required_fields if field not in poll]

                    if missing_fields:
                        logger.warning(f"Poll {poll.get('id', i)} missing fields: {missing_fields}")

                    # Validate options structure
                    if 'options' in poll and isinstance(poll['options'], list):
                        for j, option in enumerate(poll['options']):
                            if isinstance(option, dict):
                                option_required = ['id', 'text', 'poll_id']
                                option_missing = [field for field in option_required if field not in option]
                                if option_missing:
                                    logger.warning(f"Option {j} in poll {poll.get('id', i)} missing: {option_missing}")

                    # Validate created_at format
                    if 'created_at' in poll:
                        try:
                            datetime.fromisoformat(poll['created_at'].replace('Z', '+00:00'))
                        except (ValueError, AttributeError):
                            logger.warning(f"Invalid created_at format in poll {poll.get('id', i)}")

                    validated_polls.append(poll)

                return PollFetchResponse(
                    success=True,
                    polls=validated_polls,
                    status_code=response.status_code,
                    total_fetched=len(validated_polls)
                )

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON response: {e}"
                logger.error(error_msg)
                raise PollFetchError(error_msg)

        # Handle other HTTP errors
        else:
            error_msg = f"HTTP {response.status_code}: Failed to fetch polls"
            try:
                error_detail = response.json()
                if isinstance(error_detail, dict) and 'detail' in error_detail:
                    error_msg += f" - {error_detail['detail']}"
            except json.JSONDecodeError:
                error_msg += f" - {response.text[:200]}"  # Limit error text length

            logger.error(f"Poll fetch failed: {error_msg}")

            return PollFetchResponse(
                success=False,
                error_message=error_msg,
                status_code=response.status_code
            )

    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 30 seconds"
        logger.error(f"Poll fetch failed: {error_msg}")
        raise PollFetchError(error_msg)

    except requests.exceptions.ConnectionError:
        error_msg = f"Failed to connect to the API at {url}"
        logger.error(f"Poll fetch failed: {error_msg}")
        raise PollFetchError(error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {e}"
        logger.error(f"Poll fetch failed: {error_msg}")
        raise PollFetchError(error_msg)

def fetch_polls_simple(skip: int = 0, limit: int = 10, base_url: str = "http://localhost:8000") -> List[Dict[str, Any]]:
    """
    Fetch polls with streamlined error handling for straightforward use cases.

    This simplified interface to poll fetching eliminates the need for response
    object handling when you only need the poll data. It follows "fail-fast"
    principles - either return the polls or raise an exception. This makes it
    ideal for functional programming patterns, simple scripts, and scenarios
    where detailed error analysis isn't required.

    Business Intent:
        - Provide clean, minimal API for basic poll fetching
        - Reduce boilerplate code in simple integration scenarios
        - Enable rapid prototyping and scripting
        - Support functional programming with exception-based flow control
        - Simplify testing when only success/failure matters

    Use Cases:
        - Simple poll display components that show generic error messages
        - Background data loading where failures should halt processing
        - Command-line tools and administrative scripts
        - Microservices with centralized error handling
        - Functional data processing pipelines
        - Quick prototypes and demos

    Args:
        skip (int): Pagination offset. Same semantics as fetch_polls().
                   Use for implementing pagination controls or infinite scroll.
        limit (int): Maximum polls per request. Balance between API efficiency
                    and response size based on your UI requirements.
        base_url (str): API server URL. Essential for multi-environment
                       deployments and testing against different API versions.

    Returns:
        List[Dict[str, Any]]: Raw poll objects directly from the API:
            Each poll contains: id, question, created_at, owner_id, options[]
            This minimal return focuses on the essential data for most use cases.

    Raises:
        ValueError: Invalid pagination parameters. Fix calling code to provide
                   non-negative skip and positive limit values.
        PollFetchError: Any failure during poll retrieval including:
                       - Network connectivity issues (implement retry logic)
                       - Server errors (check API health)
                       - Data parsing failures (verify API compatibility)

        Exception messages contain specific failure details for logging
        and user notification purposes.
    """

    result = fetch_polls(skip, limit, base_url)

    if result.success:
        return result.polls
    else:
        error_msg = result.error_message or "Unknown error"
        raise PollFetchError(f"Poll fetch failed: {error_msg}")

def fetch_all_polls(base_url: str = "http://localhost:8000", batch_size: int = 50) -> List[Dict[str, Any]]:
    """
    Retrieve the complete poll dataset with automatic pagination management.

    This function abstracts away pagination complexity by automatically fetching
    all available polls across multiple API requests. It's designed for scenarios
    where you need the complete dataset for analysis, export, or comprehensive
    display. The function handles the pagination logic internally while providing
    control over request batching for performance optimization.

    Business Intent:
        - Enable comprehensive poll analysis and reporting
        - Support data export and backup operations
        - Provide complete datasets for admin interfaces
        - Facilitate bulk operations and mass updates
        - Remove pagination complexity from application logic
        - Support offline-first applications that sync all data

    Use Cases:
        - Admin dashboards showing complete poll statistics
        - Data export features for compliance or backup
        - Analytics systems requiring full dataset analysis
        - Search functionality that operates on all polls
        - Offline mobile apps that cache complete poll list
        - Migration tools moving polls between systems
        - Reporting systems generating comprehensive summaries

    Args:
        base_url (str): API server endpoint. Particularly important for this function
                       since it makes multiple API calls. Ensure the server can handle
                       the load and has appropriate rate limiting configured.
        batch_size (int): Number of polls fetched per API request. Larger batches
                         reduce API calls but increase memory usage and individual
                         request time. Choose based on:
                         - Server performance characteristics
                         - Network reliability
                         - Memory constraints
                         - Expected total poll count
                         Default 50 balances efficiency with reliability.

    Returns:
        List[Dict[str, Any]]: Complete list of all polls in the system.
            Contains every poll with full metadata. Be aware this could be
            large - consider memory implications for systems with many polls.
            Each poll includes: id, question, created_at, owner_id, options[]

    Raises:
        ValueError: Invalid batch_size (must be 1-100). Prevents resource exhaustion
                   and ensures reasonable API request sizes.
        PollFetchError: Failed to retrieve complete dataset. Could occur due to:
                       - Network issues during multi-request sequence
                       - Server errors or rate limiting
                       - Authentication timeouts on long operations
                       - Memory exhaustion on very large datasets

        Failures are atomic - either all polls are retrieved or none are returned.
    """

    if batch_size <= 0 or batch_size > 100:
        raise ValueError("Batch size must be between 1 and 100")

    all_polls = []
    skip = 0

    logger.info("Starting to fetch all polls with automatic pagination")

    while True:
        result = fetch_polls(skip=skip, limit=batch_size, base_url=base_url)

        if not result.success:
            error_msg = result.error_message or "Unknown error"
            raise PollFetchError(f"Failed to fetch polls at skip={skip}: {error_msg}")

        if not result.polls:
            # No more polls to fetch
            break

        all_polls.extend(result.polls)

        # If we got fewer polls than requested, we've reached the end
        if len(result.polls) < batch_size:
            break

        skip += batch_size
        logger.info(f"Fetched {len(all_polls)} polls so far...")

    logger.info(f"Completed fetching all polls: {len(all_polls)} total")
    return all_polls

def search_polls_by_question(question_keyword: str, skip: int = 0, limit: int = 10,
                           base_url: str = "http://localhost:8000") -> List[Dict[str, Any]]:
    """
    Find polls containing specific keywords in their questions using client-side filtering.

    This function provides basic search functionality when server-side search isn't
    available or when you need custom filtering logic. It fetches a batch of polls
    and filters them locally based on question text matching. While less efficient
    than server-side search, it offers immediate implementation without backend
    changes and supports complex matching logic.

    Business Intent:
        - Enable poll discovery through question content search
        - Provide search functionality without requiring backend search implementation
        - Support user experience improvements through content filtering
        - Enable rapid prototyping of search features
        - Allow custom matching logic not available server-side
        - Bridge gap until full-text search is implemented server-side

    Use Cases:
        - Search box functionality in poll browsing interfaces
        - Content discovery for users looking for specific topics
        - Admin tools for finding polls by subject matter
        - Quality assurance testing to find polls with specific content
        - Data analysis to categorize polls by content themes
        - Quick demos and prototypes needing search functionality
        - Situations where backend search API is unavailable

    Technical Note:
        This performs client-side filtering, so it only searches within the polls
        returned by the initial fetch (limited by skip/limit). For comprehensive
        search across all polls, consider using fetch_all_polls() first, though
        this has performance implications for large datasets.

    Args:
        question_keyword (str): Search term to find in poll questions. Case-insensitive
                               substring matching is performed. Use specific terms for
                               better precision. Empty strings will raise ValueError.
        skip (int): Pagination offset applied BEFORE filtering. This means if you
                   skip 10 polls, those 10 are never searched. Use carefully in
                   paginated search interfaces.
        limit (int): Maximum polls to fetch for searching. Larger limits increase
                    search comprehensiveness but reduce performance. Balance based on
                    expected result quality vs. response time requirements.
        base_url (str): API endpoint URL for poll fetching.

    Returns:
        List[Dict[str, Any]]: Polls whose questions contain the keyword.
            May return fewer polls than expected if:
            - Few polls match the keyword within the fetched batch
            - The keyword is very specific
            - Most matching polls are outside the skip/limit window

    Raises:
        ValueError: Empty or invalid keyword provided. Ensures meaningful search terms.
        PollFetchError: Underlying poll fetch failed. All fetch_polls_simple() errors
                       apply here, including network issues and server errors.
    """

    if not question_keyword or not isinstance(question_keyword, str):
        raise ValueError("Question keyword must be a non-empty string")

    polls = fetch_polls_simple(skip=skip, limit=limit, base_url=base_url)

    # Filter polls by question keyword (case-insensitive)
    matching_polls = [
        poll for poll in polls
        if 'question' in poll and isinstance(poll['question'], str)
        and question_keyword.lower() in poll['question'].lower()
    ]

    logger.info(f"Found {len(matching_polls)} polls matching keyword '{question_keyword}'")
    return matching_polls

# Example usage and testing functions
def main():
    """
    Demonstrate poll fetching patterns and serve as integration validation.

    This comprehensive demo function showcases different approaches to poll data
    retrieval and serves multiple purposes in the development lifecycle. It acts
    as living documentation through working examples, integration testing to verify
    the poll system works end-to-end, and a reference for developers implementing
    similar functionality.

    Business Intent:
        - Provide clear implementation examples for different poll fetching scenarios
        - Validate that poll fetching APIs are accessible and functioning correctly
        - Document best practices for error handling and user experience
        - Serve as a quick manual test during development and deployment verification
        - Help developers understand when to use each function variant

    The examples demonstrate:
        1. Detailed response handling for robust applications
        2. Simple fetching for straightforward use cases
        3. Search functionality implementation
        4. Pagination patterns for user interfaces
        5. Comprehensive error handling strategies
        6. Performance considerations and trade-offs

    This helps developers make informed decisions about which functions to use
    and how to provide excellent user experience through proper data handling.
    """

    # Example 1: Basic poll fetching
    try:
        result = fetch_polls(skip=0, limit=5)

        if result.success:
            print(f"✅ Successfully fetched {result.total_fetched} polls")
            for poll in result.polls:
                print(f"  Poll ID: {poll.get('id')}")
                print(f"  Question: {poll.get('question')}")
                print(f"  Options: {len(poll.get('options', []))}")
                print(f"  Created: {poll.get('created_at')}")
                print("  ---")
        else:
            print(f"❌ Failed to fetch polls: {result.error_message}")

    except PollFetchError as e:
        print(f"❌ Poll fetch error: {e}")
    except ValueError as e:
        print(f"❌ Invalid input: {e}")

    print("\n" + "="*50 + "\n")

    # Example 2: Simple poll fetching
    try:
        polls = fetch_polls_simple(skip=0, limit=3)
        print(f"✅ Simple fetch returned {len(polls)} polls:")
        for poll in polls:
            print(f"  - {poll.get('question', 'No question')}")

    except PollFetchError as e:
        print(f"❌ Simple fetch failed: {e}")

    print("\n" + "="*50 + "\n")

    # Example 3: Search functionality
    try:
        matching_polls = search_polls_by_question("favorite", skip=0, limit=10)
        print(f"✅ Found {len(matching_polls)} polls with 'favorite' in question")

    except (PollFetchError, ValueError) as e:
        print(f"❌ Search failed: {e}")

    print("\n" + "="*50 + "\n")

    # Example 4: Pagination demonstration
    try:
        print("📄 Pagination example:")
        page_size = 2
        for page in range(3):
            skip = page * page_size
            result = fetch_polls(skip=skip, limit=page_size)

            if result.success and result.polls:
                print(f"  Page {page + 1}: {len(result.polls)} polls")
                for poll in result.polls:
                    print(f"    - {poll.get('question', 'No question')}")
            else:
                print(f"  Page {page + 1}: No more polls")
                break

    except PollFetchError as e:
        print(f"❌ Pagination demo failed: {e}")

if __name__ == "__main__":
    main()
