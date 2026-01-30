# Orbidi Senior Backend Technical Challenge

This project implements a high-performance API for commercial agents to identify high-probability leads using a sigmoidal conversion metric and proximity data.

## 🚀 Architectural Decisions
To meet the non-functional requirements, the following strategies were implemented:

1. **Asynchronous Stack**: Built with **FastAPI** and `asyncio` to handle high concurrency without blocking threads.
2. **Cache-Aside Pattern**: **Redis** is used to cache results (valid for 5 mins).
3. **Database Optimization**: Uses **SQLAlchemy 2.0 (Async)** with connection pooling.
4. **Multi-worker Deployment**: Configured with multiple Uvicorn workers to utilize all CPU cores within the Docker container.

## 🧮 Conversion Metric Logic
The probability of conversion is calculated using a **Sigmoid function**:
$$f(x) = \frac{1}{1 + e^{-x}}$$

Where $x$ is defined as:
$$x = 0.2 \cdot (\text{rentability}/100) + 0.4 \cdot (\text{typology}/1000) + 0.4 \cdot (\frac{1}{1 + \text{distance}})$$

## 🛠️ Project Structure
```text
app/
├── core/         # Config, Security (JWT), Redis Client
├── db/           # Session management & Migrations
├── models/       # SQLAlchemy models
├── schemas/      # Pydantic validation schemas
├── services/     # Business logic & Metric Calculator
└── main.py       # Application Entry Point and Endpoints logic
```

## 🐳 Running with Docker

### Start the Services
To build and start the entire stack (API, Database, and Redis) in the background, run:

```bash
docker-compose up --build -d
```

### Stop the Services
To stop the containers while preserving data:

```bash
docker-compose stop
```

To shut down the services and **wipe the database volumes** (resetting the DB):

```bash
docker-compose down -v
```

---

## 🔐 Authentication (JWT)

Endpoints are protected by **JSON Web Token (JWT)** authentication. You must include a valid token in the `Authorization` header of your requests.

**Header Format:**
`Authorization: Bearer <your_access_token>`

1. **Obtain Token:** Send a POST request to your auth endpoint (e.g., `/api/v1/auth/token`) with your credentials.
2. **Usage:** Use the `access_token` provided in the response to authorize search queries.

---

## 🛣️ API Usage Example

Once the stack is running, you can search for the seeded businesses in Madrid (e.g., coordinates near `40.41, -3.70`):

```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/businesses/search?lat=40.41&lon=-3.70&radius=5000' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN_HERE'
```

---

## 🧠 Architecture & Logic

* **Distance Calculation:** Uses the **Haversine formula** implemented natively to calculate the great-circle distance between coordinates without external library overhead.
* **Conversion Metric:** A custom calculation service weights profitability, IAE typology values, and urban proximity to score business locations.
* **Race Condition Protection:** The lifespan manager is configured to handle multiple Uvicorn workers, ensuring that even with concurrent processes, the database schema initialization is handled safely.

---