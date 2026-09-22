# BookTheSeat.com

A BookMyShow-inspired movie seat booking demo built with **FastAPI + PostgreSQL/Supabase + Firebase Authentication + WebSockets**.

## Features
- Responsive movie discovery UI with search, genre filters and sorting
- Jaipur sample movie/theatre catalogue
- Browser geolocation to sort theatres by distance
- Firebase Google OAuth + phone OTP authentication hooks
- Atomic seat reservations with PostgreSQL row locks
- Five-minute temporary seat holds and automatic expiry
- Real-time seat status over WebSockets
- Simulated payment flow
- Booking confirmation with generated QR code
- Booking history
- Supabase-ready SQL schema and sample-data seeder

## Quick start
1. Create a virtual environment and install dependencies:
```bash
python -m venv .venv
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and configure Supabase/Firebase.

3. Run:
```bash
uvicorn app.main:app --reload
```

Open http://localhost:8000

## Demo login
The Login modal contains **Use demo account** for local UI testing without Firebase Admin configuration.

## Supabase
Run `schema.sql` in the Supabase SQL Editor and set `DATABASE_URL`.

## Production notes
For production, add HTTPS/WSS, rate limiting, Firebase App Check, audit logs, scheduled reservation cleanup, real payment gateway/webhooks, and stricter CORS configuration.


## Firebase Google Login setup

The frontend is connected to Firebase project `booktheseat-c364a` and uses the Firebase modular Web SDK 12.19.0.

In Firebase Console:
1. Open **Authentication → Sign-in method** and enable **Google**.
2. For phone login, enable **Phone** and keep reCAPTCHA verification enabled.
3. In **Authentication → Settings → Authorized domains**, add the production domain where BookTheSeat is hosted. For local development, add `localhost` when required.
4. Run the app over HTTP locally or HTTPS in production.

The browser signs users in with Google/Phone and sends the Firebase ID token to FastAPI. The backend validates that token through Firebase Admin when `FIREBASE_SERVICE_ACCOUNT_JSON` is provided, otherwise it uses the Firebase Identity Toolkit verification endpoint with the configured web API key. Firebase's official web documentation recommends enabling the provider in the Authentication console and using the SDK's Google provider flow. citeturn770674search0turn770674search1
