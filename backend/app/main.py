from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import handwriting_routes

app = FastAPI(
    title="Kalam3 API",
    description="A handwriting generation API",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Include all routes
app.include_router(handwriting_routes.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint to check if the API is running"""
    return {"message": "Welcome to Kalam3 API"}
