import json
import os
from fastapi import Header, HTTPException
try:
    import firebase_admin
    from firebase_admin import auth as firebase_auth, credentials
except ImportError:
    firebase_admin = None
    firebase_auth = None
    credentials = None
from .db import db_session
from .models import User

_firebase_ready = False

def init_firebase():
    global _firebase_ready
    if _firebase_ready or firebase_admin is None:
        return
    service_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if not service_json:
        return
    try:
        cred = credentials.Certificate(service_json)
    except Exception:
        cred = credentials.Certificate(json.loads(service_json))
    firebase_admin.initialize_app(cred)
    _firebase_ready = True

def verify_token(id_token: str):
    init_firebase()
    if not _firebase_ready:
        if not id_token.startswith("demo:"):
            raise HTTPException(503, "Firebase Admin is not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON or use demo mode.")
        parts=id_token.split(":",2)
        uid=parts[1] if len(parts)>1 else "demo-user"
        email=parts[2] if len(parts)>2 else None
        return {"uid": uid, "email": email, "phone_number": None}
    try:
        return firebase_auth.verify_id_token(id_token)
    except Exception as exc:
        raise HTTPException(401, f"Invalid Firebase ID token: {exc}")

def get_current_user(authorization: str | None = Header(default=None)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Bearer Firebase ID token required")
    decoded = verify_token(authorization.split(" ", 1)[1].strip())
    with db_session() as session:
        user = session.query(User).filter(User.firebase_uid == decoded["uid"]).first()
        if not user:
            user = User(firebase_uid=decoded["uid"], email=decoded.get("email"), phone_number=decoded.get("phone_number"))
            session.add(user)
            session.flush()
        else:
            if decoded.get("email"):
                user.email = decoded.get("email")
            if decoded.get("phone_number"):
                user.phone_number = decoded.get("phone_number")
        return user
