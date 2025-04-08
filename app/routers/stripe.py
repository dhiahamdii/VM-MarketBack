from fastapi import APIRouter, Depends, Request, HTTPException
from ..services.auth import get_current_user
from ..services.stripe import create_checkout_session, update_payment_status
from ..models import User, PaymentStatus, Payment
from ..database import SessionLocal
import stripe
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter()

@router.post("/create-test-product")
async def create_test_product(current_user: User = Depends(get_current_user)):
    """
    Create a test product in Stripe
    """
    try:
        # Create a test product
        product = stripe.Product.create(
            name="Test VM Instance",
            description="A test virtual machine instance",
        )

        # Create a price for the product
        price = stripe.Price.create(
            product=product.id,
            unit_amount=1000,  # $10.00
            currency="usd",
        )

        return {
            "product_id": product.id,
            "price_id": price.id,
            "amount": 1000,
            "currency": "usd"
        }
    except Exception as e:
        logger.error(f"Error creating test product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-checkout-session")
async def create_stripe_checkout_session(
    product_id: str,
    price: int,
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Stripe checkout session for a product.
    """
    return create_checkout_session(product_id, price, current_user.id)

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

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        payment_intent = session.payment_intent
        update_payment_status(payment_intent, PaymentStatus.COMPLETED)
        logger.info(f"Payment completed for session {session.id}")
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        update_payment_status(payment_intent['id'], PaymentStatus.FAILED)
        logger.warning(f"Payment failed for payment intent {payment_intent['id']}")
    elif event['type'] == 'charge.refunded':
        payment_intent = event['data']['object']['payment_intent']
        update_payment_status(payment_intent, PaymentStatus.REFUNDED)
        logger.info(f"Payment refunded for payment intent {payment_intent}")

    return {"status": "success"} 