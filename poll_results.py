import requests
import logging
from typing import Dict, Optional, Any
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PollResultsError(Exception):
    """Custom exception for poll results retrieval errors"""
    pass

class PollResultsResponse:
    """Response object for poll results retrieval"""
    def __init__(self, success: bool, results_data: Optional[Dict[str, Any]] = None,
                 error_message: Optional[str] = None, status_code: Optional[int] = None):
        self.success = success
        self.results_data = results_data
        self.error_message = error_message
        self.status_code = status_code

def get_poll_results(poll_id: int, base_url: str = "http://localhost:8000") -> PollResultsResponse:
    """
    Retrieve comprehensive voting results and statistics for a specific poll.

    This function implements the core results viewing mechanism for the polling platform.
    It enables users and administrators to see how voting has progressed, understand
    community preferences, and make data-driven decisions based on poll outcomes.
    The function provides detailed vote counts, validates response integrity, and
    supports robust error handling for production environments.

    Business Intent:
        - Enable transparent democratic processes through result visibility
        - Support data-driven decision making with accurate vote counts
        - Provide foundation for analytics and reporting functionality
        - Enable real-time result monitoring during active polling periods
        - Support audit trails and election integrity verification
        - Allow flexible deployment across different environments

    Use Cases:
        - Results pages showing current vote standings
        - Real-time dashboards during live voting events
        - Administrative interfaces for poll management
        - Analytics systems calculating engagement metrics
        - Public transparency portals for organizational decisions
        - Integration testing with controlled result verification
        - Multi-environment deployments (dev/staging/prod)

    Args:
        poll_id (int): Unique identifier of the poll to retrieve results for.
                      Must correspond to an existing poll. This determines which
                      democratic decision or question results are being requested.
        base_url (str): API server endpoint URL. Critical for multi-environment
                       support and when API servers run on different hosts or ports.
                       Defaults to local development server.

    Returns:
        PollResultsResponse: Comprehensive response object enabling detailed handling:
            - success (bool): Whether results were successfully retrieved
            - results_data (dict): Complete results including vote counts per option
            - status_code (int): HTTP response code for debugging and logging
            - error_message (str): Human-readable error description on failure

        This rich response supports various UI patterns:
        - Success indicators and result visualization
        - Detailed error messages for user feedback
        - Logging and debugging information
        - Conditional rendering based on availability

    Raises:
        ValueError: Invalid poll ID (non-positive integer). Indicates programming
                   error that should be caught during development.
        PollResultsError: Network or server issues preventing result retrieval:
                         - Connection timeouts (implement retry logic)
                         - Poll not found (update UI to reflect poll status)
                         - Server errors (check API health)
                         - Invalid responses (verify API compatibility)
    """

    # Validate input parameters
    if not isinstance(poll_id, int) or poll_id <= 0:
        raise ValueError("Poll ID must be a positive integer")

    # Prepare the request
    url = f"{base_url.rstrip('/')}/polls/{poll_id}/results"
    headers = {
        "Accept": "application/json"
    }

    logger.info(f"Retrieving results for poll {poll_id}")

    try:
        # Make the GET request
        response = requests.get(
            url=url,
            headers=headers,
            timeout=30  # 30 second timeout
        )

        # Log the response for debugging
        logger.debug(f"Response status code: {response.status_code}")
        logger.debug(f"Response headers: {response.headers}")

        # Handle successful results retrieval (200)
        if response.status_code == 200:
            try:
                results_data = response.json()
                logger.info(f"Successfully retrieved results for poll {poll_id}")

                # Validate response structure matches PollResults schema
                expected_fields = ['poll_id', 'question', 'results']
                missing_fields = [field for field in expected_fields if field not in results_data]

                if missing_fields:
                    logger.warning(f"Response missing expected fields: {missing_fields}")

                # Validate poll_id matches request
                if results_data.get('poll_id') != poll_id:
                    logger.warning(f"Response poll_id {results_data.get('poll_id')} doesn't match requested {poll_id}")

                # Validate data types
                if 'poll_id' in results_data and not isinstance(results_data['poll_id'], int):
                    logger.warning("Poll ID should be an integer")

                if 'question' in results_data and not isinstance(results_data['question'], str):
                    logger.warning("Question should be a string")

                # Validate results array structure
                if 'results' in results_data and isinstance(results_data['results'], list):
                    total_votes = 0
                    for i, result_item in enumerate(results_data['results']):
                        if not isinstance(result_item, dict):
                            logger.warning(f"Result item {i} is not a dictionary")
                            continue

                        # Check required fields for each result item
                        result_required = ['option_id', 'text', 'vote_count']
                        result_missing = [field for field in result_required if field not in result_item]
                        if result_missing:
                            logger.warning(f"Result item {i} missing fields: {result_missing}")

                        # Validate data types for result items
                        if 'option_id' in result_item and not isinstance(result_item['option_id'], int):
                            logger.warning(f"Option ID in result {i} should be an integer")

                        if 'text' in result_item and not isinstance(result_item['text'], str):
                            logger.warning(f"Text in result {i} should be a string")

                        if 'vote_count' in result_item:
                            if not isinstance(result_item['vote_count'], int):
                                logger.warning(f"Vote count in result {i} should be an integer")
                            elif result_item['vote_count'] < 0:
                                logger.warning(f"Vote count in result {i} should not be negative")
                            else:
                                total_votes += result_item['vote_count']

                    logger.info(f"Poll {poll_id} has {len(results_data['results'])} options with {total_votes} total votes")

                elif 'results' in results_data:
                    logger.warning("Results field should be an array")

                return PollResultsResponse(
                    success=True,
                    results_data=results_data,
                    status_code=response.status_code
                )

            except json.JSONDecodeError as e:
                error_msg = f"Failed to parse JSON response: {e}"
                logger.error(error_msg)
                raise PollResultsError(error_msg)

        # Handle poll not found (404)
        elif response.status_code == 404:
            error_msg = "Poll not found"
            logger.warning(f"Results retrieval failed for poll {poll_id}: {error_msg}")

            # Try to get more detailed error message from response
            try:
                error_detail = response.json()
                if isinstance(error_detail, dict) and 'detail' in error_detail:
                    error_msg = error_detail['detail']
            except (json.JSONDecodeError, KeyError):
                # Use default error message if response parsing fails
                pass

            return PollResultsResponse(
                success=False,
                error_message=error_msg,
                status_code=response.status_code
            )

        # Handle other HTTP errors
        else:
            error_msg = f"HTTP {response.status_code}: Failed to retrieve poll results"
            try:
                error_detail = response.json()
                if isinstance(error_detail, dict) and 'detail' in error_detail:
                    error_msg += f" - {error_detail['detail']}"
            except json.JSONDecodeError:
                error_msg += f" - {response.text[:200]}"  # Limit error text length

            logger.error(f"Results retrieval failed for poll {poll_id}: {error_msg}")

            return PollResultsResponse(
                success=False,
                error_message=error_msg,
                status_code=response.status_code
            )

    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 30 seconds"
        logger.error(f"Results retrieval failed for poll {poll_id}: {error_msg}")
        raise PollResultsError(error_msg)

    except requests.exceptions.ConnectionError:
        error_msg = f"Failed to connect to the API at {url}"
        logger.error(f"Results retrieval failed for poll {poll_id}: {error_msg}")
        raise PollResultsError(error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Request failed: {e}"
        logger.error(f"Results retrieval failed for poll {poll_id}: {error_msg}")
        raise PollResultsError(error_msg)

def get_poll_results_simple(poll_id: int, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Retrieve poll results with streamlined error handling for straightforward display scenarios.

    This simplified interface eliminates response object handling when you only need
    the results data. It follows "fail-fast" principles - either return the complete
    results or raise an exception. This makes it ideal for simple results displays,
    functional programming patterns, and scenarios where detailed error analysis
    isn't required.

    Business Intent:
        - Provide clean, minimal API for basic results display
        - Reduce boilerplate code in simple results viewing implementations
        - Enable rapid development of results visualization features
        - Support exception-based error handling patterns
        - Simplify testing when only success/failure matters
        - Facilitate integration in microservices with centralized error handling

    Use Cases:
        - Simple results display components showing vote counts
        - Mobile app results screens with generic error handling
        - Quick results implementations in prototypes and demos
        - Background data loading where failures should halt processing
        - Command-line tools showing poll outcomes
        - Functional programming chains where exceptions propagate naturally
        - Microservices where error handling is centralized upstream

    Args:
        poll_id (int): Target poll identifier for results retrieval. Must exist
                      and be accessible.
        base_url (str): API server URL for multi-environment support.

    Returns:
        Dict[str, Any]: Complete poll results data directly from API:
            - 'poll_id' (int): Confirms the requested poll
            - 'question' (str): Poll question for context
            - 'results' (list): Array of options with vote counts
            This minimal return focuses on essential data for most display needs.

    Raises:
        ValueError: Invalid poll ID. Fix calling code to provide valid values.
        PollResultsError: Any retrieval failure including:
                         - Poll not found (refresh poll list)
                         - Server errors (retry or show error message)
                         - Network failures (check connectivity)

        Exception messages contain specific failure details for user notifications.
    """

    result = get_poll_results(poll_id, base_url)

    if result.success and result.results_data is not None:
        return result.results_data
    else:
        error_msg = result.error_message or "Unknown error"
        raise PollResultsError(f"Poll results retrieval failed: {error_msg}")

def get_poll_winner(poll_id: int, base_url: str = "http://localhost:8000") -> Optional[Dict[str, Any]]:
    """
    Determine the winning option in a poll based on highest vote count.

    This function implements democratic outcome determination by identifying the
    option with the most votes. It's essential for decision-making processes,
    result announcements, and completion of democratic procedures. The function
    handles edge cases like ties and polls with no votes, providing clear
    outcomes for business logic.

    Business Intent:
        - Enable clear decision outcomes from democratic processes
        - Support automated decision-making based on poll results
        - Provide foundation for result announcement and communication
        - Enable conditional logic based on winning choices
        - Support analytics on decision patterns and preferences
        - Facilitate closure of voting processes with definitive outcomes

    Use Cases:
        - Result announcement interfaces showing clear winners
        - Automated decision systems taking action based on poll outcomes
        - Analytics dashboards highlighting popular choices
        - Completion workflows that execute based on winning options
        - Leaderboard displays showing top-performing options
        - Business process automation triggered by specific winners
        - A/B testing result determination and analysis

    Args:
        poll_id (int): Poll to determine winner for. Must be an existing poll
                      with at least one option.
        base_url (str): API server endpoint for results retrieval.

    Returns:
        Optional[Dict[str, Any]]: Winning option details if determinable:
            - 'option_id' (int): ID of winning option
            - 'text' (str): Text of winning choice
            - 'vote_count' (int): Number of votes received

            Returns None if:
            - No votes have been cast yet
            - All options are tied with zero votes
            - Results cannot be determined

            In case of ties with votes, returns the first option encountered
            with the highest vote count (deterministic tie-breaking).

    Raises:
        ValueError: Invalid poll ID provided.
        PollResultsError: Failed to retrieve poll results for winner determination.
                         All get_poll_results_simple() errors apply here.
    """

    results_data = get_poll_results_simple(poll_id, base_url)

    if 'results' not in results_data or not results_data['results']:
        logger.info(f"Poll {poll_id} has no results")
        return None

    # Find the option with the highest vote count
    max_votes = 0
    winners = []

    for option in results_data['results']:
        if not isinstance(option, dict) or 'vote_count' not in option:
            continue

        vote_count = option['vote_count']
        if vote_count > max_votes:
            max_votes = vote_count
            winners = [option]
        elif vote_count == max_votes and vote_count > 0:
            winners.append(option)

    if not winners or max_votes == 0:
        logger.info(f"Poll {poll_id} has no votes yet")
        return None

    if len(winners) > 1:
        logger.info(f"Poll {poll_id} has a {len(winners)}-way tie with {max_votes} votes each")
        return winners[0]  # Return first winner in case of tie
    else:
        logger.info(f"Poll {poll_id} winner: '{winners[0]['text']}' with {max_votes} votes")
        return winners[0]

def get_poll_statistics(poll_id: int, base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """
    Generate comprehensive statistical analysis and insights from poll results.

    This function transforms raw vote counts into actionable insights through
    statistical analysis. It calculates percentages, identifies trends, and
    provides formatted data suitable for dashboards, reports, and decision-making
    processes. The function is essential for understanding the significance and
    distribution of poll outcomes.

    Business Intent:
        - Enable data-driven insights from democratic processes
        - Support comprehensive reporting and analytics functionality
        - Provide foundation for business intelligence and decision support
        - Enable comparative analysis across different polls
        - Support stakeholder communication with clear metrics
        - Facilitate performance measurement of engagement initiatives

    Use Cases:
        - Executive dashboards showing poll engagement and outcomes
        - Detailed analytics reports for stakeholders and management
        - Comparative analysis interfaces showing option performance
        - Public transparency reports with comprehensive statistics
        - Research data for academic or market research purposes
        - Quality assurance validation of poll integrity and participation
        - Performance monitoring of polling campaigns and initiatives

    Args:
        poll_id (int): Target poll for statistical analysis. Must be an existing
                      poll with available results data.
        base_url (str): API server endpoint for results data retrieval.

    Returns:
        Dict[str, Any]: Comprehensive statistical analysis including:
            - 'poll_id' (int): Confirms analyzed poll
            - 'question' (str): Poll question for context
            - 'total_votes' (int): Sum of all votes across options
            - 'options_count' (int): Number of available options
            - 'winner' (dict|None): Winning option with percentage
            - 'options_with_percentages' (list): All options ranked by votes
                with vote counts and percentage breakdowns

        Each option in the results includes:
            - 'option_id': Unique identifier
            - 'text': Option description
            - 'vote_count': Raw vote count
            - 'percentage': Calculated percentage (rounded to 1 decimal)

        Options are sorted by vote count (highest first) for easy consumption.

    Raises:
        ValueError: Invalid poll ID provided.
        PollResultsError: Failed to retrieve underlying poll results data.
                         All get_poll_results_simple() errors apply here.
    """

    results_data = get_poll_results_simple(poll_id, base_url)

    if 'results' not in results_data or not results_data['results']:
        return {
            'poll_id': poll_id,
            'question': results_data.get('question', ''),
            'total_votes': 0,
            'options_count': 0,
            'winner': None,
            'options_with_percentages': []
        }

    # Calculate statistics
    total_votes = sum(option.get('vote_count', 0) for option in results_data['results'])
    options_count = len(results_data['results'])

    # Calculate percentages and find winner
    options_with_percentages = []
    max_votes = 0
    winner = None

    for option in results_data['results']:
        if not isinstance(option, dict):
            continue

        vote_count = option.get('vote_count', 0)
        percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0

        option_with_percentage = {
            'option_id': option.get('option_id'),
            'text': option.get('text'),
            'vote_count': vote_count,
            'percentage': round(percentage, 1)
        }

        options_with_percentages.append(option_with_percentage)

        if vote_count > max_votes:
            max_votes = vote_count
            winner = option_with_percentage

    # Sort by vote count descending
    options_with_percentages.sort(key=lambda x: x['vote_count'], reverse=True)

    return {
        'poll_id': poll_id,
        'question': results_data.get('question', ''),
        'total_votes': total_votes,
        'options_count': options_count,
        'winner': winner if max_votes > 0 else None,
        'options_with_percentages': options_with_percentages
    }

# Example usage and testing functions
def main():
    """
    Demonstrate poll results analysis patterns and serve as integration validation.

    This comprehensive demonstration function showcases different approaches to
    poll results analysis and serves multiple purposes in the development lifecycle.
    It acts as living documentation through working examples, integration testing
    to verify the results system works end-to-end, and a reference for developers
    implementing results analysis functionality.

    Business Intent:
        - Provide clear implementation examples for different results analysis scenarios
        - Validate that results APIs are accessible and functioning correctly
        - Document best practices for data presentation and user experience
        - Serve as a quick manual test during development and deployment
        - Help developers understand when to use each function variant
        - Demonstrate proper patterns for results visualization and reporting

    The examples demonstrate:
        1. Detailed response handling for robust results applications
        2. Simple results retrieval for straightforward display needs
        3. Winner determination logic and edge case handling
        4. Statistical analysis and percentage calculation patterns
        5. Comprehensive error handling strategies for different failure modes
        6. Data formatting and presentation considerations

    This helps developers make informed decisions about which functions to use
    and how to provide excellent user experience through proper results handling,
    statistical presentation, and meaningful error messaging in results interfaces.
    """

    print("POLL RESULTS EXAMPLES")
    print("="*50)

    # Example 1: Basic poll results retrieval
    try:
        result = get_poll_results(poll_id=1)

        if result.success and result.results_data is not None:
            print("✅ Successfully retrieved poll results!")
            results_data = result.results_data
            print(f"   Poll ID: {results_data['poll_id']}")
            print(f"   Question: {results_data['question']}")
            print(f"   Options: {len(results_data.get('results', []))}")

            if 'results' in results_data:
                print("   Results:")
                for option in results_data['results']:
                    print(f"     - {option.get('text')}: {option.get('vote_count')} votes")
        else:
            error_msg = result.error_message or "Unknown error"
            print(f"❌ Failed to retrieve results: {error_msg}")
            if result.status_code:
                print(f"   Status Code: {result.status_code}")

    except PollResultsError as e:
        print(f"❌ Poll results error: {e}")
    except ValueError as e:
        print(f"❌ Invalid input: {e}")

    print("\n" + "="*50 + "\n")

    # Example 2: Simple poll results retrieval
    try:
        results_data = get_poll_results_simple(poll_id=1)
        print("✅ Simple results retrieval successful!")
        print(f"   Question: {results_data['question']}")

        total_votes = sum(option.get('vote_count', 0) for option in results_data.get('results', []))
        print(f"   Total votes: {total_votes}")

    except PollResultsError as e:
        print(f"❌ Simple results retrieval failed: {e}")

    print("\n" + "="*50 + "\n")

    # Example 3: Get poll winner
    try:
        winner = get_poll_winner(poll_id=1)
        if winner:
            print("✅ Poll winner found!")
            print(f"   Winning option: {winner['text']}")
            print(f"   Vote count: {winner['vote_count']}")
        else:
            print("ℹ️  No winner yet (no votes or tie)")

    except (PollResultsError, ValueError) as e:
        print(f"❌ Winner retrieval failed: {e}")

    print("\n" + "="*50 + "\n")

    # Example 4: Get poll statistics
    try:
        stats = get_poll_statistics(poll_id=1)
        print("✅ Poll statistics retrieved!")
        print(f"   Question: {stats['question']}")
        print(f"   Total votes: {stats['total_votes']}")
        print(f"   Options: {stats['options_count']}")

        if stats['winner']:
            print(f"   Winner: {stats['winner']['text']} ({stats['winner']['percentage']}%)")

        print("   Detailed results:")
        for option in stats['options_with_percentages']:
            print(f"     - {option['text']}: {option['vote_count']} votes ({option['percentage']}%)")

    except (PollResultsError, ValueError) as e:
        print(f"❌ Statistics retrieval failed: {e}")

    print("\n" + "="*50 + "\n")

    # Example 5: Error handling demonstration
    try:
        # This should fail with non-existent poll
        result = get_poll_results(poll_id=99999)

        if not result.success:
            print(f"✅ Error handling working correctly: {result.error_message}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")

    print("\n" + "="*50 + "\n")

    # Example 6: Input validation
    try:
        # This should raise ValueError
        get_poll_results(poll_id=-1)
    except ValueError as e:
        print(f"✅ Input validation working: {e}")

    try:
        # This should raise ValueError
        get_poll_results(poll_id=0)
    except ValueError as e:
        print(f"✅ Input validation working: {e}")

if __name__ == "__main__":
    main()
