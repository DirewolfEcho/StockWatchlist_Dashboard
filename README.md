# Stock Analyzer App

A full-stack application to track HK/US stocks, fetch daily news, and generate AI-powered review reports.

## Prerequisites

1.  **Python 3.8+**
2.  **Node.js 18+**
3.  **API Keys** (Optional but recommended for full features):
    *   `OPENAI_API_KEY`: For AI Report Generation.
    *   `TAVILY_API_KEY`: For fetching latest news.

## Setup

1.  **Backend**
    ```bash
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Set Keys (example)
    export OPENAI_API_KEY="sk-..."
    export TAVILY_API_KEY="tvly-..."
    
    # Run Server
    uvicorn app.main:app --reload --port 8000
    ```

2.  **Frontend**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
    Access at `http://localhost:3000` (or 3001 if 3000 is busy).

## Features

*   **Watchlist**: Add HK (e.g., `00700`) or US (e.g., `AAPL`) stocks.
*   **Scheduler**: Set a daily time (HH:MM) for analysis.
*   **Manual Trigger**: Click "Run Analysis Now" for immediate results.
*   **Reports**: View AI-generated summaries including price trends, news analysis, and recommendations.
# Vercel Deploy Trigger
