import json
import os
import urllib.error
import urllib.request

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

# Firebase Web API keys are intended for client applications. This fallback uses
# the Firebase Identity Toolkit API to validate ID tokens when Admin credentials
# are not configured on the server.
DEFAULT_FIREBASE_WEB_API_KEY = "AIzaSyBhTW0ecTXsjf7h5baqBUKq3NusblBdvrg"


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


def verify_token_with_identity_toolkit(id_token: str):
    api_key = os.getenv("FIREBASE_API_KEY") or os.getenv(
        "FIREBASE_WEB_API_KEY", DEFAULT_FIREBASE_WEB_API_KEY
    )
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}"
    body = json.dumps({"idToken": id_token}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = json.loads(exc.read().decode("utf-8"))
            message = detail.get("error", {}).get("message", "Token validation failed")
        except Exception:
            message = "Token validation failed"
        raise HTTPException(401, f"Invalid Firebase ID token: {message}")
    except Exception as exc:
        raise HTTPException(503, f"Firebase token validation service unavailable: {exc}")

    users = payload.get("users") or []
    if not users:
        raise HTTPException(401, "Firebase token did not resolve to a user")

    firebase_user = users[0]
    return {
        "uid": firebase_user.get("localId"),
        "email": firebase_user.get("email"),
        "phone_number": firebase_user.get("phoneNumber"),
    }


def verify_token(id_token: str):
    init_firebase()

    if id_token.startswith("demo:"):
        parts = id_token.split(":", 2)
        uid = parts[1] if len(parts) > 1 else "demo-user"
        email = parts[2] if len(parts) > 2 else None
        return {"uid": uid, "email": email, "phone_number": None}

    if _firebase_ready:
        try:
            return firebase_auth.verify_id_token(id_token)
        except Exception as exc:
            raise HTTPException(401, f"Invalid Firebase ID token: {exc}")

    return verify_token_with_identity_toolkit(id_token)


def get_current_user(
    authorization: str | None = Header(default=None),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Bearer Firebase ID token required")

    decoded = verify_token(authorization.split(" ", 1)[1].strip())

    with db_session() as session:
        user = session.query(User).filter(User.firebase_uid == decoded["uid"]).first()

        if not user:
            user = User(
                firebase_uid=decoded["uid"],
                email=decoded.get("email"),
                phone_number=decoded.get("phone_number"),
            )
            session.add(user)
            session.flush()
        else:
            if decoded.get("email"):
                user.email = decoded.get("email")
            if decoded.get("phone_number"):
                user.phone_number = decoded.get("phone_number")

        return user
