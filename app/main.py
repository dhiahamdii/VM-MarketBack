from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import stripe

from .routers import auth, stripe as stripe_router, test
from .database import engine, Base
from .models import User
import os

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VM Marketplace API",
              description="API for the VM Marketplace",
              version="0.1.0")


stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(stripe_router.router, prefix="/stripe", tags=["stripe"])
app.include_router(test.router, prefix="/test", tags=["test"])

@app.get("/")
async def root():
    return {"message": "Welcome to the API"} 




