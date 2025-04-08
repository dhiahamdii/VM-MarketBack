import os
import sys

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User, Payment

def view_database():
    db = SessionLocal()
    try:
        # View Users
        print("\n=== Users ===")
        users = db.query(User).all()
        if not users:
            print("No users found in the database")
        else:
            for user in users:
                print(f"ID: {user.id}, Email: {user.email}")

        # View Payments
        print("\n=== Payments ===")
        payments = db.query(Payment).all()
        if not payments:
            print("No payments found in the database")
        else:
            for payment in payments:
                print(f"ID: {payment.id}, User ID: {payment.user_id}, Amount: {payment.amount}, Status: {payment.status}")

    except Exception as e:
        print(f"Error accessing database: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    view_database() 