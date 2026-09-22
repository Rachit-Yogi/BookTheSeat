from app.db import Base, engine
from app.seed import seed_database

Base.metadata.create_all(bind=engine)
seed_database()
print('Seeded BookTheSeat database.')
