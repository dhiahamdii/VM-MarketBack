from app.database import engine
from sqlalchemy import text

def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✅ Successfully connected to PostgreSQL!")
            print(f"Test query result: {result.scalar()}")
    except Exception as e:
        print("❌ Failed to connect to PostgreSQL!")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_connection() 