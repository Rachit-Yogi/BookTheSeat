-- Supabase/PostgreSQL migration schema for BookTheSeat.com
create table if not exists users (
  user_id serial primary key,
  email varchar(255), phone_number varchar(30), firebase_uid varchar(255) unique not null,
  created_at timestamp default now(), updated_at timestamp default now()
);
create index if not exists idx_users_email on users(email);
create index if not exists idx_users_phone on users(phone_number);

create table if not exists movies (
  movie_id serial primary key, title varchar(255) not null, genre varchar(255) not null,
  rating numeric(3,1) not null default 7.0, description text not null, cast text default '',
  duration integer not null, language varchar(80) not null, poster_url text, release_date date not null,
  created_at timestamp default now()
);

create table if not exists theatres (
  theatre_id serial primary key, name varchar(255) not null, location text not null,
  latitude numeric(10,7) not null, longitude numeric(10,7) not null, city varchar(100) default 'Jaipur',
  created_at timestamp default now()
);
create index if not exists idx_theatres_city on theatres(city);

create table if not exists showtimes (
  showtime_id serial primary key, movie_id integer not null references movies(movie_id),
  theatre_id integer not null references theatres(theatre_id), date date not null, time varchar(10) not null,
  format varchar(20) not null, language varchar(80) not null, created_at timestamp default now()
);
create index if not exists idx_showtimes_movie_theatre_date on showtimes(movie_id,theatre_id,date);

create table if not exists seats (
  seat_id serial primary key, showtime_id integer not null references showtimes(showtime_id),
  seat_number varchar(10) not null, row_letter varchar(3) not null, seat_type varchar(30) not null,
  price numeric(8,2) not null, is_booked boolean default false, booked_by integer references users(user_id),
  created_at timestamp default now(), unique(showtime_id,seat_number)
);
create index if not exists idx_seats_showtime_booked on seats(showtime_id,is_booked);

create table if not exists bookings (
  booking_id serial primary key, user_id integer not null references users(user_id), showtime_id integer not null references showtimes(showtime_id),
  total_price numeric(8,2) not null, booking_status varchar(20) not null default 'pending',
  booking_time timestamp default now(), payment_expiry timestamp, created_at timestamp default now()
);
create index if not exists idx_bookings_user on bookings(user_id);

create table if not exists booking_seats (
  booking_id integer not null references bookings(booking_id) on delete cascade,
  seat_id integer not null references seats(seat_id), primary key(booking_id,seat_id)
);

create table if not exists seat_reservations (
  reservation_id serial primary key, user_id integer not null references users(user_id), showtime_id integer not null references showtimes(showtime_id),
  seat_id integer not null references seats(seat_id), reservation_expiry timestamp not null, created_at timestamp default now(),
  unique(showtime_id,seat_id)
);
create index if not exists idx_reservations_expiry on seat_reservations(reservation_expiry);
