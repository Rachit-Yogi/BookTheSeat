from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class User(Base):
    __tablename__ = "users"
    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    firebase_uid: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

class Movie(Base):
    __tablename__ = "movies"
    movie_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    genre: Mapped[str] = mapped_column(String(255), default="Drama")
    rating: Mapped[float] = mapped_column(Numeric(3,1), default=7.0)
    description: Mapped[str] = mapped_column(Text)
    cast: Mapped[str] = mapped_column(Text, default="")
    duration: Mapped[int] = mapped_column(Integer, default=120)
    language: Mapped[str] = mapped_column(String(80), default="Hindi")
    poster_url: Mapped[str] = mapped_column(Text, default="")
    release_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Theatre(Base):
    __tablename__ = "theatres"
    theatre_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(Text)
    latitude: Mapped[float] = mapped_column(Numeric(10,7))
    longitude: Mapped[float] = mapped_column(Numeric(10,7))
    city: Mapped[str] = mapped_column(String(100), default="Jaipur", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class ShowTime(Base):
    __tablename__ = "showtimes"
    showtime_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.movie_id"), index=True)
    theatre_id: Mapped[int] = mapped_column(ForeignKey("theatres.theatre_id"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    time: Mapped[str] = mapped_column(String(10))
    format: Mapped[str] = mapped_column(String(20), default="2D")
    language: Mapped[str] = mapped_column(String(80), default="Hindi")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class Seat(Base):
    __tablename__ = "seats"
    seat_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.showtime_id"), index=True)
    seat_number: Mapped[str] = mapped_column(String(10))
    row_letter: Mapped[str] = mapped_column(String(3), index=True)
    seat_type: Mapped[str] = mapped_column(String(30))
    price: Mapped[float] = mapped_column(Numeric(8,2))
    is_booked: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    booked_by: Mapped[int | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    __table_args__ = (UniqueConstraint("showtime_id", "seat_number", name="uq_showtime_seat"),)

class Booking(Base):
    __tablename__ = "bookings"
    booking_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.showtime_id"), index=True)
    total_price: Mapped[float] = mapped_column(Numeric(8,2))
    booking_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    booking_time: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    payment_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

class BookingSeat(Base):
    __tablename__ = "booking_seats"
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.booking_id", ondelete="CASCADE"), primary_key=True)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.seat_id"), primary_key=True)

class SeatReservation(Base):
    __tablename__ = "seat_reservations"
    reservation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), index=True)
    showtime_id: Mapped[int] = mapped_column(ForeignKey("showtimes.showtime_id"), index=True)
    seat_id: Mapped[int] = mapped_column(ForeignKey("seats.seat_id"), index=True)
    reservation_expiry: Mapped[datetime] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    __table_args__ = (UniqueConstraint("showtime_id", "seat_id", name="uq_active_showtime_seat_reservation"),)
