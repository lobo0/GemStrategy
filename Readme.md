# GemStrategy - Investment Recommendation Tool

This project is a web application that implements the **Global Equities Momentum (GEM)** investment strategy, as described by Gary Antonacci. It provides investment recommendations based on the 12-month returns of various ETFs.

## Features

*   Calculates 12-month returns for a predefined set of ETFs.
*   Implements the GEM strategy to recommend whether to invest in equities or bonds.
*   Provides a simple web interface to input a reference date and view the recommendation.
*   Includes a benchmark comparison against the S&P 500.
*   Caches API responses to improve performance.

## Technology Stack

*   **Backend:** Python 3, FastAPI
*   **Frontend:** Jinja2, HTML, Bootstrap
*   **Data Processing:** Pandas
*   **Testing:** Pytest, Pytest-Asyncio
*   **Deployment:** Docker, Gunicorn

## Project Structure

```
.
├── Dockerfile
├── Readme.md
├── config.py
├── main.py
├── pytest.ini
├── requirements.txt
├── templates
│   └── index.html
├── tests
│   └── test_main.py
└── vercel.json
```

## Local Development

### Prerequisites

*   Python 3.9+
*   Git

### Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd GemStrategy
    ```

2.  **Create and activate a virtual environment:**
    *   On Windows:
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```
2b. ** Might be problem with execution policy on Windows:
        In PowerShell as administrator Run:
        set-executionpolicy remotesigned 
        
3.  **Install the dependencies:**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

### Running the Application

To run the application locally, use the following command:

```bash
uvicorn main:app --reload
```

The application will be available at `http://127.0.0.1:8000`.

### Running Tests

To run the test suite, use the following command:

```bash
pytest
```

## Deployment

This project includes a `Dockerfile` for containerizing the application and a `vercel.json` for deployment on Vercel (as a proxy to a service like Google Cloud Run).

To build the Docker image:

```bash
docker build -t gem-strategy .
```

To run the Docker container:

```bash
docker run -p 8080:8080 gem-strategy
```
