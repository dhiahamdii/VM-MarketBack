# FastAPI Backend

This is a FastAPI backend with user authentication and Stripe integration.

## Features

- User authentication with JWT tokens
- Stripe payment integration
- SQLite database with SQLAlchemy
- CORS middleware for frontend integration

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
- Copy `.env.example` to `.env`
- Update the following variables:
  - `SECRET_KEY`: A secure random string for JWT token signing
  - `STRIPE_SECRET_KEY`: Your Stripe secret key

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Authentication
- `POST /auth/register`: Register a new user
- `POST /auth/login`: Login and get JWT token

### Stripe
- `POST /stripe/create-checkout-session`: Create a Stripe checkout session

## Frontend Integration

The backend is configured to work with a frontend running on `http://localhost:3000`. Update the CORS settings in `main.py` if your frontend runs on a different URL. 