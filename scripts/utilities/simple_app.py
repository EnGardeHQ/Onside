"""Simple FastAPI app to test Swagger documentation."""
from fastapi import FastAPI

app = FastAPI(
    title="OnSide API Test",
    description="Simple test app for Swagger documentation",
    version="1.0.0",
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str = None):
    """Read an item."""
    return {"item_id": item_id, "q": q}
