# User Registration Module

A Python module for registering users via the Polly-API `/register` endpoint with comprehensive error handling and logging.

## Features

- ✅ Full compliance with OpenAPI 3.1 specification
- ✅ Proper request body formatting (username, password)
- ✅ Comprehensive HTTP response code handling (200, 400, 500, etc.)
- ✅ Robust error handling and meaningful logging
- ✅ Response validation against API schema
- ✅ Connection timeout and retry logic
- ✅ Input validation and sanitization
- ✅ Both detailed and simplified function interfaces

## Requirements

```bash
pip install requests
```

## Quick Start

### Basic Usage (Detailed Response)

```python
from user_registration import register_user

# Register a new user
result = register_user("myusername", "securepassword123")

if result.success:
    print(f"✅ User registered successfully!")
    print(f"User ID: {result.user_data['id']}")
    print(f"Username: {result.user_data['username']}")
else:
    print(f"❌ Registration failed: {result.error_message}")
    print(f"Status Code: {result.status_code}")
```

### Simple Usage (Exception-Based)

```python
from user_registration import register_user_simple, UserRegistrationError

try:
    user_data = register_user_simple("myusername", "securepassword123")
    print(f"User registered with ID: {user_data['id']}")
except UserRegistrationError as e:
    print(f"Registration failed: {e}")
```

## API Specification Compliance

This module is designed to work with the Polly-API OpenAPI specification:

### Request Format
- **Endpoint**: `POST /register`
- **Content-Type**: `application/json`
- **Body**: 
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```

### Response Formats

#### Success (200)
```json
{
  "id": 1,
  "username": "myusername"
}
```

#### Username Already Exists (400)
```json
{
  "detail": "Username already registered"
}
```

## Function Reference

### `register_user(username, password, base_url)`

The main registration function with detailed response handling.

**Parameters:**
- `username` (str): The username for the new user
- `password` (str): The password for the new user  
- `base_url` (str, optional): API base URL (default: "http://localhost:8000")

**Returns:**
- `UserRegistrationResponse`: Object containing:
  - `success` (bool): Whether registration succeeded
  - `user_data` (dict): User data on success (id, username)
  - `error_message` (str): Error description on failure
  - `status_code` (int): HTTP status code

**Raises:**
- `ValueError`: For invalid input parameters
- `UserRegistrationError`: For connection/timeout issues

### `register_user_simple(username, password, base_url)`

Simplified wrapper that returns user data directly or raises an exception.

**Parameters:** Same as `register_user()`

**Returns:**
- `dict`: User data containing 'id' and 'username' fields

**Raises:**
- `ValueError`: For invalid input parameters  
- `UserRegistrationError`: For any registration failure

## Error Handling

The module provides comprehensive error handling for various scenarios:

### Input Validation
```python
# These will raise ValueError
register_user("", "password")        # Empty username
register_user(None, "password")      # None username  
register_user("user", "")            # Empty password
register_user("user", None)          # None password
```

### Network Errors
```python
try:
    result = register_user("user", "pass", "http://invalid-url")
except UserRegistrationError as e:
    # Handles: Connection errors, timeouts, DNS failures
    print(f"Network error: {e}")
```

### HTTP Status Codes

| Status Code | Meaning | Handling |
|-------------|---------|----------|
| 200 | Success | Returns user data |
| 400 | Username already exists | Returns error response |
| 500+ | Server errors | Returns error response |
| Others | Unexpected errors | Returns error response |

### Response Validation

The module validates that successful responses contain the expected fields:
- `id` (integer): User ID
- `username` (string): Username

## Logging

The module uses Python's built-in logging with different levels:

```python
import logging
logging.basicConfig(level=logging.INFO)  # Set desired level

# Logs generated:
# INFO: Successful registrations
# WARNING: Username conflicts  
# ERROR: Network/server errors
# DEBUG: Request/response details (when enabled)
```

## Testing

### Unit Tests

Run the comprehensive test suite:

```bash
python test_registration.py
```

The test suite includes:
- ✅ Successful registration scenarios
- ✅ Username conflict handling
- ✅ Server error responses
- ✅ Network error conditions
- ✅ Input validation
- ✅ JSON parsing errors
- ✅ Both function interfaces

### Integration Tests

Test against a running API server:

```bash
# Start your Polly-API server first
python test_registration.py
# Choose 'y' when prompted for integration tests
```

## Configuration

### Custom Base URL

```python
# For production API
result = register_user("user", "pass", "https://api.polly.com")

# For staging environment  
result = register_user("user", "pass", "https://staging-api.polly.com")
```

### Request Timeout

The default timeout is 30 seconds. To customize, modify the timeout in the source:

```python
response = requests.post(
    url=url,
    json=request_body,
    headers=headers,
    timeout=60  # Custom timeout in seconds
)
```

## Example Applications

### CLI Registration Tool

```python
#!/usr/bin/env python3
import sys
from user_registration import register_user_simple, UserRegistrationError

def main():
    if len(sys.argv) != 3:
        print("Usage: python register_cli.py <username> <password>")
        sys.exit(1)
    
    username, password = sys.argv[1], sys.argv[2]
    
    try:
        user_data = register_user_simple(username, password)
        print(f"✅ User '{username}' registered with ID: {user_data['id']}")
    except UserRegistrationError as e:
        print(f"❌ Registration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Batch Registration

```python
from user_registration import register_user
import time

users_to_register = [
    ("alice", "password123"),
    ("bob", "securepass456"), 
    ("charlie", "mypassword789")
]

for username, password in users_to_register:
    result = register_user(username, password)
    
    if result.success:
        print(f"✅ {username}: ID {result.user_data['id']}")
    else:
        print(f"❌ {username}: {result.error_message}")
    
    time.sleep(1)  # Rate limiting
```

## Security Considerations

### Password Handling
- Passwords are sent over HTTPS in production
- Passwords are not logged by this module
- Use strong passwords and consider password policy enforcement

### Error Information
- Error messages don't expose sensitive system information
- Username conflicts are handled gracefully
- Connection errors provide helpful debugging information

### Input Validation
- All inputs are validated before sending requests
- SQL injection protection through JSON serialization
- XSS prevention through proper content-type handling

## Troubleshooting

### Common Issues

**Connection Refused**
```
UserRegistrationError: Failed to connect to the API at http://localhost:8000/register
```
→ Ensure the Polly-API server is running

**Timeout Errors** 
```
UserRegistrationError: Request timed out after 30 seconds
```
→ Check server performance or increase timeout

**Invalid JSON Response**
```
UserRegistrationError: Failed to parse JSON response
```
→ Server may be returning HTML error pages; check server logs

**Username Already Exists**
```
Registration failed: Username already registered (Status: 400)
```
→ Choose a different username

### Debug Mode

Enable debug logging for detailed request/response information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all requests and responses will be logged
result = register_user("debug_user", "debug_pass")
```

## Contributing

1. Follow the existing code style and patterns
2. Add tests for any new functionality
3. Update documentation for API changes
4. Ensure all tests pass before submitting

## License

This module is part of the Polly-API project. See the main project license for details.