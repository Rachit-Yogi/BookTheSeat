from datetime import date
from pydantic import BaseModel, Field

class ReserveSeatsRequest(BaseModel):
    showtime_id: int
    seat_ids: list[int] = Field(min_length=1, max_length=10)

class BookTicketsRequest(BaseModel):
    reservation_ids: list[int] = Field(min_length=1)

class CancelReservationRequest(BaseModel):
    reservation_ids: list[int] = Field(min_length=1)

class LoginPayload(BaseModel):
    id_token: str

class ProfileUpdate(BaseModel):
    email: str | None = None
    phone_number: str | None = None

class MovieOut(BaseModel):
    movie_id: int
    title: str
    genre: str
    rating: float
    description: str
    cast: str
    duration: int
    language: str
    poster_url: str
    release_date: date

    class Config:
        from_attributes = True
