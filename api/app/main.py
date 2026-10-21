"""FastAPI application entry point for the E-Commerce API.

Defines `app` and a simple health endpoint used by tests and other components.
"""

from fastapi import FastAPI


app = FastAPI(title="E-Commerce API")


@app.get("/health")
def health() -> dict[str, str]:
    """Health check endpoint.

    Returns a tiny JSON object used by tests and orchestration systems.

    Returns:
        A mapping with a single key "status" and value "ok".
    """
    return {"status": "ok"}
