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

def create_checkout_session(amount: int, currency: str, metadata: dict, user_id: int):
    try:
        logger.info(f"Creating checkout session for amount {amount} for user {user_id}")
        
        # Create a checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': 'VM Deployment',
                    },
                    'unit_amount': amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{os.getenv('FRONTEND_URL')}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('FRONTEND_URL')}/payment/cancel",
            metadata={
                'user_id': str(user_id),
                **metadata
            }
        )

        logger.info(f"Checkout session created successfully: {session.id}")

        # Store payment information in database
        db = SessionLocal()
        try:
            payment = Payment(
                user_id=user_id,
                amount=amount/100,  # Convert from cents to dollars
                currency=currency,
                stripe_payment_id=session.id,
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
            "session_id": session.id,
            "payment_id": payment.id,
            "url": session.url
        }
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def create_payment_intent(amount: int, currency: str, metadata: dict, user_id: int):
    try:
        logger.info(f"Creating payment intent for amount {amount} for user {user_id}")
        
        # Create a payment intent
        payment_intent = stripe.PaymentIntent.create(
            amount=amount,
            currency=currency,
            payment_method_types=['card'],
            metadata={
                'user_id': str(user_id),
                **metadata
            }
        )

        logger.info(f"Payment intent created successfully: {payment_intent.id}")

        # Store payment information in database
        db = SessionLocal()
        try:
            payment = Payment(
                user_id=user_id,
                amount=amount/100,  # Convert from cents to dollars
                currency=currency,
                stripe_payment_id=payment_intent.id,
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
            "client_secret": payment_intent.client_secret,
            "payment_id": payment.id,
            "id": payment_intent.id
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