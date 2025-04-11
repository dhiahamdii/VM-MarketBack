from fastapi import APIRouter, Depends, Request, HTTPException
from ..services.auth import get_current_user
from ..services.stripe import create_payment_intent, update_payment_status, create_checkout_session
from ..models import User, Payment, PaymentStatus, PaymentCreate, PaymentUpdate
from ..database import SessionLocal
import stripe
import os
import logging
from dotenv import load_dotenv
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter()

@router.post("/create-payment-intent")
async def create_stripe_payment_intent(
    amount: int,
    currency: str,
    metadata: Dict,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Stripe payment intent.
    """
    return create_payment_intent(amount, currency, metadata, current_user.id)

@router.post("/create-checkout-session")
async def create_stripe_checkout_session(
    amount: int,
    currency: str,
    metadata: Dict,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Stripe checkout session.
    """
    return create_checkout_session(amount, currency, metadata, current_user.id)

@router.get("/payment-status/{payment_id}")
async def get_payment_status(
    payment_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Get the status of a payment by its ID.
    """
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(
            Payment.id == payment_id,
            Payment.user_id == current_user.id
        ).first()
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
            
        return {
            "status": payment.status.value,
            "amount": payment.amount,
            "currency": payment.currency,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at
        }
    finally:
        db.close()

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """
    Handle Stripe webhook events.
    """
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    if not endpoint_secret:
        logger.error("STRIPE_WEBHOOK_SECRET is not set")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

    logger.info(f"Received Stripe webhook event: {event['type']}")

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        update_payment_status(payment_intent['id'], PaymentStatus.COMPLETED)
        logger.info(f"Payment completed for payment intent {payment_intent['id']}")
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        update_payment_status(payment_intent['id'], PaymentStatus.FAILED)
        logger.warning(f"Payment failed for payment intent {payment_intent['id']}")
    elif event['type'] == 'charge.refunded':
        payment_intent = event['data']['object']['payment_intent']
        update_payment_status(payment_intent, PaymentStatus.REFUNDED)
        logger.info(f"Payment refunded for payment intent {payment_intent}")

    return {"status": "success"} 