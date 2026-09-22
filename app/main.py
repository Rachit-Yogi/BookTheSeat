import asyncio
import base64
import io
import math
import os
import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal

import qrcode
from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from .auth import get_current_user, verify_token
from .db import Base, engine, db_session
from .models import Booking, BookingSeat, Movie, Seat, SeatReservation, ShowTime, Theatre, User
from .realtime import manager
from .schemas import BookTicketsRequest, CancelReservationRequest, LoginPayload, ProfileUpdate, ReserveSeatsRequest
from .seed import seed_database

app = FastAPI(title="BookTheSeat.com API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")

RESERVATION_MINUTES = int(os.getenv("RESERVATION_MINUTES", "5"))

@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    seed_database()
    asyncio.create_task(expiry_loop())

@app.get("/")
def home():
    return FileResponse("app/static/index.html")

@app.get("/api/config")
def config():
    return {
        "firebase": {
            "apiKey": os.getenv("FIREBASE_API_KEY", ""),
            "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN", ""),
            "projectId": os.getenv("FIREBASE_PROJECT_ID", ""),
            "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET", ""),
            "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID", ""),
            "appId": os.getenv("FIREBASE_APP_ID", ""),
        },
        "reservationMinutes": RESERVATION_MINUTES,
    }

def movie_to_dict(m: Movie):
    return {"movie_id":m.movie_id,"title":m.title,"genre":m.genre,"rating":float(m.rating),"description":m.description,"cast":m.cast,"duration":m.duration,"language":m.language,"poster_url":m.poster_url,"release_date":m.release_date.isoformat()}

def distance_km(lat1, lon1, lat2, lon2):
    R=6371.0
    p1=math.radians(lat1); p2=math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R*2*math.atan2(math.sqrt(a), math.sqrt(1-a))

def cleanup_expired(session: Session, showtime_id: int | None = None):
    now = datetime.utcnow()
    q = session.query(SeatReservation).filter(SeatReservation.reservation_expiry <= now)
    if showtime_id is not None:
        q = q.filter(SeatReservation.showtime_id == showtime_id)
    expired = q.all()
    affected = {r.showtime_id for r in expired}
    for r in expired:
        session.delete(r)
    session.flush()
    return affected

async def broadcast_snapshot(showtime_ids: set[int]):
    for sid in showtime_ids:
        with db_session() as session:
            payload = seat_snapshot(session, sid)
        await manager.broadcast(sid, {"type":"seat_update", **payload})

def seat_snapshot(session: Session, showtime_id: int):
    cleanup_expired(session, showtime_id)
    seats = session.query(Seat).filter(Seat.showtime_id == showtime_id).all()
    reserved_ids = {r.seat_id for r in session.query(SeatReservation).filter(SeatReservation.showtime_id == showtime_id).all()}
    return {"showtime_id": showtime_id, "seats":[{"seat_id":s.seat_id,"seat_number":s.seat_number,"row_letter":s.row_letter,"seat_type":s.seat_type,"price":float(s.price),"is_booked":s.is_booked,"is_reserved":s.seat_id in reserved_ids} for s in seats]}

@app.post("/api/auth/login")
def auth_login(payload: LoginPayload):
    decoded = verify_token(payload.id_token)
    with db_session() as session:
        user = session.query(User).filter(User.firebase_uid == decoded["uid"]).first()
        if not user:
            user = User(firebase_uid=decoded["uid"], email=decoded.get("email"), phone_number=decoded.get("phone_number"))
            session.add(user)
            session.flush()
        else:
            user.email = decoded.get("email") or user.email
            user.phone_number = decoded.get("phone_number") or user.phone_number
        return {"user_id": user.user_id, "email": user.email, "phone_number": user.phone_number, "firebase_uid": user.firebase_uid}

@app.post("/api/auth/signup")
def auth_signup(payload: LoginPayload):
    return auth_login(payload)

@app.get("/api/me")
def me(user: User = Depends(get_current_user)):
    return {"user_id":user.user_id,"email":user.email,"phone_number":user.phone_number,"firebase_uid":user.firebase_uid}

@app.patch("/api/me")
def update_me(payload: ProfileUpdate, user: User = Depends(get_current_user)):
    with db_session() as session:
        dbuser = session.get(User, user.user_id)
        if payload.email is not None: dbuser.email = payload.email
        if payload.phone_number is not None: dbuser.phone_number = payload.phone_number
        return {"user_id":dbuser.user_id,"email":dbuser.email,"phone_number":dbuser.phone_number,"firebase_uid":dbuser.firebase_uid}

@app.get("/api/me/bookings")
def my_bookings(user: User = Depends(get_current_user)):
    with db_session() as session:
        rows = (session.query(Booking, ShowTime, Movie, Theatre)
                .join(ShowTime, Booking.showtime_id==ShowTime.showtime_id)
                .join(Movie, ShowTime.movie_id==Movie.movie_id)
                .join(Theatre, ShowTime.theatre_id==Theatre.theatre_id)
                .filter(Booking.user_id==user.user_id).order_by(Booking.created_at.desc()).all())
        out=[]
        for b, st, m, t in rows:
            seats = session.query(Seat).join(BookingSeat, BookingSeat.seat_id==Seat.seat_id).filter(BookingSeat.booking_id==b.booking_id).all()
            out.append({"booking_id":b.booking_id,"status":b.booking_status,"booking_time":b.booking_time.isoformat() if b.booking_time else None,"total_price":float(b.total_price),"movie":m.title,"movie_poster":m.poster_url,"theatre":t.name,"date":st.date.isoformat(),"time":st.time,"seats":[s.seat_number for s in seats]})
        return out

@app.get("/api/movies")
def movies(q: str = "", genre: str = "", sort: str = "popularity", limit: int = Query(50, le=100)):
    with db_session() as session:
        query = session.query(Movie)
        if q:
            query = query.filter(or_(Movie.title.ilike(f"%{q}%"), Movie.genre.ilike(f"%{q}%"), Movie.language.ilike(f"%{q}%")))
        if genre:
            query = query.filter(Movie.genre.ilike(f"%{genre}%"))
        if sort == "rating": query = query.order_by(Movie.rating.desc())
        elif sort == "release": query = query.order_by(Movie.release_date.desc())
        else: query = query.order_by(Movie.rating.desc(), Movie.release_date.desc())
        return [movie_to_dict(m) for m in query.limit(limit).all()]

@app.get("/api/movies/{movie_id}")
def movie_detail(movie_id: int):
    with db_session() as session:
        m=session.get(Movie,movie_id)
        if not m: raise HTTPException(404,"Movie not found")
        return movie_to_dict(m)

@app.get("/api/theatres")
def theatres(city: str="Jaipur", latitude: float | None=None, longitude: float | None=None):
    with db_session() as session:
        rows=session.query(Theatre).filter(Theatre.city.ilike(city)).all()
        out=[]
        for t in rows:
            d=distance_km(latitude,longitude,float(t.latitude),float(t.longitude)) if latitude is not None and longitude is not None else None
            out.append({"theatre_id":t.theatre_id,"name":t.name,"location":t.location,"latitude":float(t.latitude),"longitude":float(t.longitude),"city":t.city,"distance_km":round(d,1) if d is not None else None})
        out.sort(key=lambda x: x["distance_km"] if x["distance_km"] is not None else 1e9)
        return out

@app.get("/api/showtimes/{movie_id}/{theatre_id}/{show_date}")
def showtimes(movie_id:int,theatre_id:int,show_date:date,fmt:str="",language:str="",max_price:float|None=None):
    with db_session() as session:
        q=session.query(ShowTime).filter(ShowTime.movie_id==movie_id,ShowTime.theatre_id==theatre_id,ShowTime.date==show_date)
        if fmt: q=q.filter(ShowTime.format==fmt)
        if language: q=q.filter(ShowTime.language.ilike(language))
        result=[]
        for st in q.order_by(ShowTime.time).all():
            cleanup_expired(session,st.showtime_id)
            total=session.query(func.count(Seat.seat_id)).filter(Seat.showtime_id==st.showtime_id).scalar() or 0
            booked=session.query(func.count(Seat.seat_id)).filter(Seat.showtime_id==st.showtime_id,Seat.is_booked.is_(True)).scalar() or 0
            result.append({"showtime_id":st.showtime_id,"time":st.time,"format":st.format,"language":st.language,"available_seats":max(total-booked,0),"total_seats":total,"min_price":220,"max_price":420})
        if max_price is not None:
            result=[r for r in result if r["min_price"]<=max_price]
        return result

@app.get("/api/showtimes/by-id/{showtime_id}")
def showtime_by_id(showtime_id:int):
    with db_session() as session:
        row=(session.query(ShowTime, Movie, Theatre)
             .join(Movie, ShowTime.movie_id==Movie.movie_id)
             .join(Theatre, ShowTime.theatre_id==Theatre.theatre_id)
             .filter(ShowTime.showtime_id==showtime_id).first())
        if not row: raise HTTPException(404,"Showtime not found")
        st,m,t=row
        return {"showtime_id":st.showtime_id,"date":st.date.isoformat(),"time":st.time,"format":st.format,"language":st.language,
                "movie":movie_to_dict(m),"theatre":{"theatre_id":t.theatre_id,"name":t.name,"location":t.location,"latitude":float(t.latitude),"longitude":float(t.longitude)}}

@app.get("/api/seats/{showtime_id}")
def seats(showtime_id:int):
    with db_session() as session:
        if not session.get(ShowTime,showtime_id): raise HTTPException(404,"Showtime not found")
        return seat_snapshot(session, showtime_id)

@app.post("/api/reserve-seats")
async def reserve_seats(payload: ReserveSeatsRequest, user: User = Depends(get_current_user)):
    expires=datetime.utcnow()+timedelta(minutes=RESERVATION_MINUTES)
    with db_session() as session:
        st=session.get(ShowTime,payload.showtime_id)
        if not st: raise HTTPException(404,"Showtime not found")
        cleanup_expired(session,payload.showtime_id)
        seats_q=(session.query(Seat).filter(Seat.showtime_id==payload.showtime_id,Seat.seat_id.in_(payload.seat_ids)).with_for_update())
        seat_rows=seats_q.all()
        if len(seat_rows)!=len(set(payload.seat_ids)): raise HTTPException(400,"One or more seats do not belong to this show")
        existing=session.query(SeatReservation).filter(SeatReservation.showtime_id==payload.showtime_id,SeatReservation.seat_id.in_(payload.seat_ids)).all()
        if existing: raise HTTPException(409,"One or more selected seats are currently being booked by another user")
        if any(s.is_booked for s in seat_rows): raise HTTPException(409,"One or more selected seats are already booked")
        prior=session.query(SeatReservation).filter(SeatReservation.user_id==user.user_id,SeatReservation.showtime_id==payload.showtime_id).all()
        if prior:
            for r in prior: session.delete(r)
        reservations=[SeatReservation(user_id=user.user_id,showtime_id=payload.showtime_id,seat_id=s.seat_id,reservation_expiry=expires) for s in seat_rows]
        session.add_all(reservations)
        session.flush()
        movie=session.get(Movie, st.movie_id)
        theatre=session.get(Theatre, st.theatre_id)
        result={"reservation_ids":[r.reservation_id for r in reservations],"expires_at":expires.isoformat(),"showtime_id":payload.showtime_id,
                "movie":{"movie_id":movie.movie_id,"title":movie.title,"poster_url":movie.poster_url},
                "theatre":{"theatre_id":theatre.theatre_id,"name":theatre.name,"location":theatre.location},
                "date":st.date.isoformat(),"time":st.time,"format":st.format,"language":st.language,
                "seats":[{"seat_id":s.seat_id,"seat_number":s.seat_number,"price":float(s.price),"seat_type":s.seat_type} for s in seat_rows],
                "total":round(sum(float(s.price) for s in seat_rows),2)}
    await broadcast_snapshot({payload.showtime_id})
    return result

@app.post("/api/cancel-reservation")
async def cancel_reservation(payload: CancelReservationRequest, user: User = Depends(get_current_user)):
    with db_session() as session:
        rows=session.query(SeatReservation).filter(SeatReservation.reservation_id.in_(payload.reservation_ids),SeatReservation.user_id==user.user_id).all()
        affected={r.showtime_id for r in rows}
        for r in rows: session.delete(r)
    await broadcast_snapshot(affected)
    return {"released":len(rows)}

@app.post("/api/book-tickets")
async def book_tickets(payload: BookTicketsRequest, user: User = Depends(get_current_user)):
    with db_session() as session:
        now=datetime.utcnow()
        reservations=(session.query(SeatReservation).filter(SeatReservation.reservation_id.in_(payload.reservation_ids),SeatReservation.user_id==user.user_id).with_for_update().all())
        if len(reservations)!=len(payload.reservation_ids): raise HTTPException(400,"Reservation is missing or belongs to another user")
        if any(r.reservation_expiry<=now for r in reservations): raise HTTPException(410,"Reservation expired")
        showtime_ids={r.showtime_id for r in reservations}
        if len(showtime_ids)!=1: raise HTTPException(400,"All seats must belong to the same show")
        seat_ids=[r.seat_id for r in reservations]
        seat_rows=session.query(Seat).filter(Seat.seat_id.in_(seat_ids)).with_for_update().all()
        if any(s.is_booked for s in seat_rows): raise HTTPException(409,"A selected seat was booked concurrently")
        total=round(sum(float(s.price) for s in seat_rows),2)
        booking=Booking(user_id=user.user_id,showtime_id=reservations[0].showtime_id,total_price=Decimal(str(total)),booking_status="confirmed")
        session.add(booking); session.flush()
        session.add_all([BookingSeat(booking_id=booking.booking_id,seat_id=s.seat_id) for s in seat_rows])
        for s in seat_rows:
            s.is_booked=True; s.booked_by=user.user_id
        for r in reservations: session.delete(r)
        session.flush()
        booking_ref=f"BTS-{date.today().strftime('%y%m%d')}-{booking.booking_id:05d}-{secrets.token_hex(2).upper()}"
        sid=booking.showtime_id
        st=session.get(ShowTime,sid); m=session.get(Movie,st.movie_id); t=session.get(Theatre,st.theatre_id)
        qr_payload=f"{booking_ref}|{m.title}|{t.name}|{st.date}|{st.time}|{','.join(s.seat_number for s in seat_rows)}|INR {total}"
        qr=qrcode.QRCode(version=2,box_size=8,border=2); qr.add_data(qr_payload); qr.make(fit=True)
        img=qr.make_image(); buf=io.BytesIO(); img.save(buf,format="PNG")
        qr_data="data:image/png;base64,"+base64.b64encode(buf.getvalue()).decode()
        result={"booking_id":booking.booking_id,"booking_ref":booking_ref,"status":"confirmed","total_price":total,"qr_data":qr_data,
                "movie":m.title,"poster_url":m.poster_url,"theatre":t.name,"theatre_location":t.location,
                "date":st.date.isoformat(),"time":st.time,"format":st.format,"language":st.language,
                "seats":[s.seat_number for s in seat_rows],
                "price_breakdown":[{"seat":s.seat_number,"type":s.seat_type,"price":float(s.price)} for s in seat_rows]}
    await broadcast_snapshot({sid})
    return result

@app.get("/api/booking/{booking_id}")
def booking_detail(booking_id:int, user: User = Depends(get_current_user)):
    with db_session() as session:
        row=(session.query(Booking, ShowTime, Movie, Theatre)
             .join(ShowTime, Booking.showtime_id==ShowTime.showtime_id)
             .join(Movie, ShowTime.movie_id==Movie.movie_id)
             .join(Theatre, ShowTime.theatre_id==Theatre.theatre_id)
             .filter(Booking.booking_id==booking_id,Booking.user_id==user.user_id).first())
        if not row: raise HTTPException(404,"Booking not found")
        b,st,m,t=row
        seats=session.query(Seat).join(BookingSeat,BookingSeat.seat_id==Seat.seat_id).filter(BookingSeat.booking_id==b.booking_id).all()
        return {"booking_id":b.booking_id,"status":b.booking_status,"total_price":float(b.total_price),"movie":m.title,"theatre":t.name,"theatre_location":t.location,
                "date":st.date.isoformat(),"time":st.time,"format":st.format,"language":st.language,"seats":[s.seat_number for s in seats]}

@app.post("/api/cancel-booking")
async def cancel_booking(booking_id:int, user: User = Depends(get_current_user)):
    with db_session() as session:
        booking=session.query(Booking).filter(Booking.booking_id==booking_id,Booking.user_id==user.user_id).with_for_update().first()
        if not booking: raise HTTPException(404,"Booking not found")
        if booking.booking_status=="cancelled": return {"status":"cancelled"}
        seats=(session.query(Seat).join(BookingSeat,BookingSeat.seat_id==Seat.seat_id).filter(BookingSeat.booking_id==booking.booking_id).with_for_update().all())
        for s in seats:
            s.is_booked=False; s.booked_by=None
        booking.booking_status="cancelled"
        sid=booking.showtime_id
    await manager.broadcast(sid,{"type":"seat_update", **get_seat_snapshot_sync(sid)})
    return {"status":"cancelled","booking_id":booking_id}

def get_seat_snapshot_sync(sid):
    with db_session() as session: return seat_snapshot(session,sid)

@app.websocket("/ws/seats/{showtime_id}")
async def websocket_seats(ws:WebSocket, showtime_id:int):
    await manager.connect(showtime_id,ws)
    try:
        with db_session() as session:
            await ws.send_json({"type":"seat_update", **seat_snapshot(session,showtime_id)})
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(showtime_id,ws)
    except Exception:
        await manager.disconnect(showtime_id,ws)

async def expiry_loop():
    while True:
        await asyncio.sleep(10)
        try:
            with db_session() as session:
                affected=cleanup_expired(session)
            if affected:
                await broadcast_snapshot(affected)
        except Exception:
            pass
