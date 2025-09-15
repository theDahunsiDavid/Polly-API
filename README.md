# Polly-API: FastAPI Poll Application

A simple poll application built with FastAPI, SQLite, and JWT authentication. Users can register, log in, create, retrieve, vote on, and delete polls. The project follows best practices with modular code in the `api/` directory.

## Features

- User registration and login (JWT authentication)
- Create, retrieve, and delete polls
- Add options to polls (minimum of two options required)
- Vote on polls (authenticated users only)
- View poll results with vote counts
- SQLite database with SQLAlchemy ORM
- Modular code structure for maintainability

## Project Structure

```
Polly-API/
├── api/
│   ├── __init__.py
│   ├── auth.py
│   ├── database.py
│   ├── models.py
│   ├── routes.py
│   └── schemas.py
├── main.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd Polly-API
```

2. **Set up a Python virtual environment (recommended)**

A virtual environment helps isolate your project dependencies.

- **On Unix/macOS:**

  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- **On Windows (cmd):**

  ```cmd
  python -m venv venv
  venv\Scripts\activate
  ```

- **On Windows (PowerShell):**

  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```

To deactivate the virtual environment, simply run:

```bash
deactivate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Set environment variables (optional)**

Create a `.env` file in the project root to override the default secret key:

```
SECRET_KEY=your_super_secret_key
```

5. **Run the application**

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Usage

### 1. Register a new user

- **Endpoint:** `POST /register`
- **Body:**

```json
{
  "username": "yourusername",
  "password": "yourpassword"
}
```

### 2. Login

- **Endpoint:** `POST /login`
- **Body (form):**
  - `username`: yourusername
  - `password`: yourpassword
- **Response:**

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

### 3. Get all polls

- **Endpoint:** `GET /polls`
- **Query params:** `skip` (default 0), `limit` (default 10)
- **Authentication:** Not required

### 4. Create a poll

- **Endpoint:** `POST /polls`
- **Headers:** `Authorization: Bearer <access_token>`
- **Body:**

```json
{
  "question": "Your poll question",
  "options": ["Option 1", "Option 2"]
}
```

### 5. Get a specific poll

- **Endpoint:** `GET /polls/{poll_id}`
- **Authentication:** Not required

### 6. Vote on a poll

- **Endpoint:** `POST /polls/{poll_id}/vote`
- **Headers:** `Authorization: Bearer <access_token>`
- **Body:**

```json
{
  "option_id": 1
}
```

### 7. Get poll results

- **Endpoint:** `GET /polls/{poll_id}/results`
- **Authentication:** Not required
- **Response:**

```json
{
  "poll_id": 1,
  "question": "Your poll question",
  "results": [
    {
      "option_id": 1,
      "text": "Option 1",
      "vote_count": 3
    },
    {
      "option_id": 2,
      "text": "Option 2",
      "vote_count": 1
    }
  ]
}
```

### 8. Delete a poll

- **Endpoint:** `DELETE /polls/{poll_id}`
- **Headers:** `Authorization: Bearer <access_token>`

## Interactive API Docs

Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive Swagger UI.

## Testing

The API includes comprehensive client-side functions with unit and integration tests for user registration, poll fetching, vote casting, and results retrieval.

### Prerequisites for Testing

1. **Install dependencies** (if not already done):
```bash
pip install requests pytest
```

2. **Start the API server** (required for integration tests):
```bash
uvicorn main:app --reload
```

### Unit Tests (No Server Required)

Unit tests use mocked responses and don't require a running server:

```bash
# Test user registration functions
python test_registration.py

# Test poll fetching functions  
python test_poll_fetcher.py

# Test vote casting functions
python test_vote_caster.py

# Test poll results functions
python test_poll_results.py

# Run all tests with pytest (if installed)
python -m pytest test_*.py -v
```

### Integration Tests (Server Required)

Integration tests require a running API server and real authentication tokens.

#### 1. Get a JWT Access Token

First, register a user and login to get an access token:

```bash
# Register a new user
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass123"}'

# Login to get JWT token
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=testpass123"
```

Save the `access_token` from the login response - you'll need it for voting and poll creation.

#### 2. Create Sample Polls for Testing

Create some test polls to use in integration tests:

```bash
# Create a programming poll (replace YOUR_JWT_TOKEN with actual token)
curl -X POST "http://localhost:8000/polls" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "question": "What is your favorite programming language?",
    "options": ["Python", "JavaScript", "Java", "Go", "Rust"]
  }'

# Create a simple yes/no poll
curl -X POST "http://localhost:8000/polls" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "question": "Do you like testing?", 
    "options": ["Yes", "No"]
  }'
```

Note the `poll_id` values returned - you'll use these in the integration tests.

#### 3. Run Integration Tests

Each test suite will prompt you for the required information:

```bash
# Test user registration (no token needed)
python test_registration.py
# When prompted, choose 'y' for integration tests

# Test poll fetching (no token needed)
python test_poll_fetcher.py  
# When prompted, choose 'y' for integration tests

# Test vote casting (requires JWT token and poll IDs)
python test_vote_caster.py
# When prompted:
# - Choose 'y' for integration tests
# - Enter your JWT token
# - Enter poll IDs and option IDs from your created polls

# Test poll results (requires existing poll IDs)
python test_poll_results.py
# When prompted:
# - Choose 'y' for integration tests  
# - Enter poll IDs from your created polls
```

### Quick Test Examples

Test the functions directly in Python:

```python
# Test user registration
from user_registration import register_user_simple
try:
    user = register_user_simple("newuser", "password123")
    print(f"User created: {user['username']}")
except Exception as e:
    print(f"Error: {e}")

# Test poll fetching  
from poll_fetcher import fetch_polls_simple
try:
    polls = fetch_polls_simple(skip=0, limit=5)
    print(f"Found {len(polls)} polls")
except Exception as e:
    print(f"Error: {e}")

# Test vote casting (requires valid token and poll/option IDs)
from vote_caster import cast_vote_simple
try:
    vote = cast_vote_simple(poll_id=1, option_id=2, access_token="your_token")
    print(f"Vote cast: {vote['id']}")
except Exception as e:
    print(f"Error: {e}")

# Test poll results
from poll_results import get_poll_results_simple
try:
    results = get_poll_results_simple(poll_id=1)
    print(f"Poll: {results['question']}")
    for option in results['results']:
        print(f"  {option['text']}: {option['vote_count']} votes")
except Exception as e:
    print(f"Error: {e}")
```

### Test Coverage

The test suites include:
- **Input validation** - Testing parameter validation and error handling
- **Authentication** - Testing JWT token handling and unauthorized access  
- **HTTP error codes** - Testing 200, 400, 401, 404, 500 responses
- **Network errors** - Testing timeouts and connection failures
- **Response validation** - Testing API response schema compliance
- **Edge cases** - Testing empty results, ties, malformed data

## License

MIT License
