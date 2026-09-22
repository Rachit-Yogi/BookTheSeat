from datetime import date, timedelta
from decimal import Decimal
from .db import db_session
from .models import Movie, Theatre, ShowTime, Seat

CURRENT_MOVIES = [
    {"title":"Hanuman Ansh","genre":"Action, Mythology","rating":8.1,"language":"Hindi","duration":145,"release_date":date(2026,8,7),"poster_url":"https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=700&q=80","description":"A contemporary mythological adventure following a young devotee discovering a legacy that changes his destiny.","cast":"Shobhinaw Satyaa, Chandan Anand"},
    {"title":"Mirzapur: The Movie","genre":"Crime, Thriller","rating":7.9,"language":"Hindi","duration":155,"release_date":date(2026,9,4),"poster_url":"https://akm-img-in.tosshub.com/indiatoday/images/story/202602/whatsapp_image_2026-02-05_at_10.05.27_am.jpeg?size=690:388","description":"The Mirzapur universe expands to the big screen with a large-scale crime drama.","cast":"Pankaj Tripathi, Divyenndu, Jitendra Kumar"},
    {"title":"Daayra","genre":"Drama, Thriller","rating":7.5,"language":"Hindi","duration":143,"release_date":date(2026,9,18),"poster_url":"https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?auto=format&fit=crop&w=700&q=80","description":"A high-stakes thriller where two strangers find their lives colliding around a hidden secret.","cast":"Kareena Kapoor, Prithviraj Sukumaran"},
    {"title":"VIBE","genre":"Comedy, Drama","rating":7.2,"language":"Hindi","duration":132,"release_date":date(2026,9,18),"poster_url":"https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=700&q=80","description":"A warm, funny story about friendship, ambition and one unforgettable performance.","cast":"Preity Zinta, Sparsh Shrivastav"},
    {"title":"Resident Evil","genre":"Horror, Action","rating":7.8,"language":"English","duration":120,"release_date":date(2026,9,1),"poster_url":"https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=700&q=80","description":"A survival horror feature with a new outbreak and a race against time.","cast":"International Ensemble"},
    {"title":"I’m Game","genre":"Fantasy, Action","rating":7.7,"language":"Hindi","duration":150,"release_date":date(2026,9,3),"poster_url":"https://www.keralatv.in/media/2026/08/Im-Game-New-Release-Date-1280x720.jpg","description":"A globe-spanning fantasy action adventure built around a dangerous chase.","cast":"Dulquer Salmaan, Ensemble"},
    {"title":"The Vvaan: Force of the Forest","genre":"Fantasy, Thriller","rating":7.6,"language":"Hindi","duration":148,"release_date":date(2026,9,25),"poster_url":"https://i.cdn.newsbytesapp.com/images/l61820260709162719.jpeg","description":"A mythic force awakens in the forest, pulling a reluctant hero into a supernatural conflict.","cast":"Sidharth Malhotra, Tamannaah Bhatia"},
    {"title":"Haiwaan","genre":"Thriller","rating":7.4,"language":"Hindi","duration":138,"release_date":date(2026,9,11),"poster_url":"https://www.tribuneindia.com/sortd-service/imaginary/v22-01/jpg/large/high?url=dGhldHJpYnVuZS1zb3J0ZC1wcm8tcHJvZC1zb3J0ZC9tZWRpYWIxY2VhMDEwLTcyMWUtMTFmMS1hZmFlLTJkNzNlMTMwYzExYi5qcGc=","description":"A psychological thriller from director Priyadarshan.","cast":"Akshay Kumar, Saif Ali Khan"},
    {"title":"Toxic: A Fairy Tale for Grown-Ups","genre":"Action, Crime","rating":7.0,"language":"Hindi","duration":151,"release_date":date(2026,3,19),"poster_url":"https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?auto=format&fit=crop&w=700&q=80","description":"A stylized action drama set against an international underworld.","cast":"Yash, Nayanthara, Kiara Advani"},
    {"title":"Project Hail Mary","genre":"Sci-Fi, Adventure","rating":8.2,"language":"English","duration":145,"release_date":date(2026,3,20),"poster_url":"https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=700&q=80","description":"A lone astronaut wakes with one impossible mission: save humanity.","cast":"Ryan Gosling, Sandra Hüller"},
    {"title":"Avatar: Fire and Ash","genre":"Sci-Fi, Adventure","rating":8.0,"language":"English","duration":192,"release_date":date(2025,12,19),"poster_url":"https://images.unsplash.com/photo-1518709594023-6eab9bab7b23?auto=format&fit=crop&w=700&q=80","description":"Pandora returns with a new chapter of family, survival and discovery.","cast":"Sam Worthington, Zoe Saldaña"},
    {"title":"Mortal Kombat II","genre":"Action, Fantasy","rating":7.3,"language":"English","duration":115,"release_date":date(2026,5,15),"poster_url":"https://images.unsplash.com/photo-1534791547706-3fc7b3f84c39?auto=format&fit=crop&w=700&q=80","description":"Warriors face a new tournament with the fate of realms at stake.","cast":"Lewis Tan, Jessica McNamee"},
    {"title":"Supergirl","genre":"Action, Adventure","rating":7.5,"language":"English","duration":130,"release_date":date(2026,6,26),"poster_url":"https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=700&q=80","description":"A new hero carves her own path beyond the shadow of legacy.","cast":"Milly Alcock, Jason Momoa"},
    {"title":"Toy Story 5","genre":"Animation, Comedy","rating":8.0,"language":"English","duration":105,"release_date":date(2026,6,19),"poster_url":"https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=700&q=80","description":"Old friends and a new generation discover what belonging really means.","cast":"Tom Hanks, Tim Allen"},
    {"title":"The Devil Wears Prada 2","genre":"Comedy, Drama","rating":7.4,"language":"English","duration":122,"release_date":date(2026,5,1),"poster_url":"https://images.unsplash.com/photo-1524985069026-dd778a71c7b4?auto=format&fit=crop&w=700&q=80","description":"The fashion world gets another shake-up when old alliances meet new ambition.","cast":"Meryl Streep, Anne Hathaway, Emily Blunt"},
    {"title":"Ready or Not 2","genre":"Horror, Comedy","rating":7.1,"language":"English","duration":104,"release_date":date(2026,7,10),"poster_url":"https://images.unsplash.com/photo-1505635552518-3448f9f9a7a1?auto=format&fit=crop&w=700&q=80","description":"One family game gets even more dangerous in this darkly comic sequel.","cast":"Samara Weaving, Ensemble"},
    {"title":"Scream 7","genre":"Horror, Thriller","rating":7.0,"language":"English","duration":115,"release_date":date(2026,2,27),"poster_url":"https://images.unsplash.com/photo-1509248961158-e54f6934749c?auto=format&fit=crop&w=700&q=80","description":"A new mystery begins when the mask returns to a familiar town.","cast":"Melissa Barrera, Ensemble"},
    {"title":"The Mummy","genre":"Horror, Mystery","rating":7.0,"language":"English","duration":120,"release_date":date(2026,4,17),"poster_url":"https://images.unsplash.com/photo-1534447677768-be436bb09401?auto=format&fit=crop&w=700&q=80","description":"An archaeological discovery awakens something that should have remained buried.","cast":"Ensemble"},
    {"title":"Mayday","genre":"Drama, Thriller","rating":7.2,"language":"English","duration":121,"release_date":date(2026,4,24),"poster_url":"https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=700&q=80","description":"When a flight goes off course, every decision carries a consequence.","cast":"Ensemble"},
    {"title":"The Mandalorian & Grogu","genre":"Sci-Fi, Adventure","rating":8.1,"language":"English","duration":135,"release_date":date(2026,5,22),"poster_url":"https://images.unsplash.com/photo-1440404653325-ab127d49abc1?auto=format&fit=crop&w=700&q=80","description":"A bounty hunter and his young companion take on a mission larger than either expects.","cast":"Pedro Pascal, Ensemble"},
]

THEATRES = [
    {"name":"Cinepolis - World Trade Park","location":"1st Floor, World Trade Park, JLN Marg, Malviya Nagar","latitude":26.8520,"longitude":75.8043},
    {"name":"INOX G.T Central","location":"GT Central Mall, D-Block, Malviya Nagar","latitude":26.8506,"longitude":75.8110},
    {"name":"PVR - Mall of Jaipur","location":"Mall Of Jaipur, Gandhi Path Road, Vaishali Nagar","latitude":26.9163,"longitude":75.7355},
    {"name":"INOX Pink Square Mall","location":"Pink Square Mall, Govind Marg, Raja Park","latitude":26.9126,"longitude":75.8334},
    {"name":"Cinepolis JOI Mall","location":"JOI Mall, Bajaj Nagar, Jaipur","latitude":26.8782,"longitude":75.7993},
    {"name":"Miraj Cinema Jaipur","location":"Jawahar Circle, Jagatpura","latitude":26.8502,"longitude":75.8060},
    {"name":"INOX Sunny Trade Center","location":"Sunny Trade Center, Mansarovar","latitude":26.8856,"longitude":75.7619},
    {"name":"Raj Mandir Cinema","location":"C-16, Bhagwan Das Road, C-Scheme","latitude":26.9161,"longitude":75.7971},
]

def seed_database():
    with db_session() as session:
        if session.query(Movie).count() == 0:
            session.add_all([Movie(**m) for m in CURRENT_MOVIES])
            session.flush()
        if session.query(Theatre).count() == 0:
            session.add_all([Theatre(**t, city="Jaipur") for t in THEATRES])
            session.flush()
        if session.query(ShowTime).count() == 0:
            movies = session.query(Movie).filter(Movie.title.in_(["Hanuman Ansh","Mirzapur: The Movie","Daayra","VIBE","Resident Evil","I’m Game","Haiwaan"])).all()
            theatres = session.query(Theatre).all()
            today = date.today()
            show_rows = []
            for d in range(0, 6):
                dt = today + timedelta(days=d)
                for movie in movies:
                    if dt < movie.release_date:
                        continue
                    for theatre in theatres:
                        times = [("09:30","2D"),("12:50","2D"),("16:25","2D"),("19:40","2D"),("22:15","2D")]
                        if theatre.name.startswith("PVR") and movie.title in {"Resident Evil","Project Hail Mary"}:
                            times = [("11:00","4DX"),("15:15","2D"),("18:30","2D"),("21:45","2D")]
                        for t, fmt in times:
                            show_rows.append(ShowTime(movie_id=movie.movie_id,theatre_id=theatre.theatre_id,date=dt,time=t,format=fmt,language=movie.language))
            session.add_all(show_rows)
            session.flush()
            rows = []
            for show in session.query(ShowTime).all():
                for r_idx, row in enumerate("ABCDEFGHIJKL"):
                    if r_idx < 2: seat_type, price = "recliner", Decimal("420")
                    elif r_idx < 7: seat_type, price = "premium", Decimal("300")
                    else: seat_type, price = "standard", Decimal("220")
                    for n in range(1, 9):
                        rows.append(Seat(showtime_id=show.showtime_id, seat_number=f"{row}{n}", row_letter=row, seat_type=seat_type, price=price))
            session.bulk_save_objects(rows)
