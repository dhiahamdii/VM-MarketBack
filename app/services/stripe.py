import stripe
from fastapi import HTTPException
import os
import logging
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Payment, PaymentStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_checkout_session(product_id: str, price: int, user_id: int):
    try:
        logger.info(f"Creating checkout session for product {product_id} with price {price} for user {user_id}")
        
        # Create a product in Stripe if it doesn't exist
        try:
            product = stripe.Product.retrieve(product_id)
        except stripe.error.InvalidRequestError:
            logger.info(f"Product {product_id} not found, creating new product")
            product = stripe.Product.create(
                id=product_id,
                name=f"Product {product_id}",
                description=f"Description for Product {product_id}"
            )

        # Create a price if it doesn't exist
        try:
            price_obj = stripe.Price.create(
                product=product.id,
                unit_amount=price,
                currency='usd',
            )
        except stripe.error.StripeError as e:
            logger.error(f"Error creating price: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Error creating price: {str(e)}")

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_obj.id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'{os.getenv("FRONTEND_URL", "http://localhost:3000")}/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{os.getenv("FRONTEND_URL", "http://localhost:3000")}/cancel',
            customer_email=None,  # Will be set by Stripe if user is logged in
            metadata={
                'product_id': product_id,
                'user_id': str(user_id)
            }
        )

        logger.info(f"Checkout session created successfully: {checkout_session.id}")

        # Store payment information in database
        db = SessionLocal()
        try:
            payment = Payment(
                user_id=user_id,
                amount=price/100,  # Convert from cents to dollars
                currency='usd',
                stripe_payment_id=checkout_session.payment_intent,
                status=PaymentStatus.PENDING
            )
            db.add(payment)
            db.commit()
            db.refresh(payment)
            logger.info(f"Payment record created in database: {payment.id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        finally:
            db.close()

        return {
            "url": checkout_session.url,
            "payment_id": payment.id,
            "session_id": checkout_session.id
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def update_payment_status(stripe_payment_id: str, status: PaymentStatus):
    logger.info(f"Updating payment status for {stripe_payment_id} to {status}")
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.stripe_payment_id == stripe_payment_id).first()
        if payment:
            payment.status = status
            db.commit()
            db.refresh(payment)
            logger.info(f"Payment status updated successfully for payment {payment.id}")
        else:
            logger.warning(f"Payment not found for stripe_payment_id: {stripe_payment_id}")
        return payment
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        db.close()