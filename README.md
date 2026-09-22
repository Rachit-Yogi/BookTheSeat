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
