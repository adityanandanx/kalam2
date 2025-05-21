from fastapi import FastAPI
from app.api.routes import handwriting_routes

app = FastAPI(
    title="Kalam3 API",
    description="A handwriting generation API",
    version="0.1.0",
)

# Include all routes
app.include_router(handwriting_routes.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint to check if the API is running"""
    return {"message": "Welcome to Kalam3 API"}
