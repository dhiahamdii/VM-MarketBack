from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Payment
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/test-db")
async def test_database(db: Session = Depends(get_db)):
    try:
        # Test User table
        user_count = db.query(User).count()
        logger.info(f"Found {user_count} users in the database")
        
        # Test Payment table
        payment_count = db.query(Payment).count()
        logger.info(f"Found {payment_count} payments in the database")
        
        # Test database connection by executing a simple query
        result = db.execute("SELECT 1").scalar()
        logger.info("Database connection test successful")
        
        return {
            "status": "success",
            "message": "Database connection is working",
            "user_count": user_count,
            "payment_count": payment_count,
            "test_query_result": result
        }
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database test failed: {str(e)}") 