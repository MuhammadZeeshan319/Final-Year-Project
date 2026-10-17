"""
Accounts: sign up, log in, log out, and per-user saved progress.

Security
  - passwords: PBKDF2-HMAC-SHA256, 200,000 iterations, 16-byte random salt per user (Python stdlib)
  - sessions: random 256-bit token returned once; only its SHA-256 is stored; expires after 30 days
  - login throttling: 5 failed attempts per email per 15 minutes
  - generic "email or password is incorrect" message (does not reveal which accounts exist)
The browser sends the token as  Authorization: Bearer <token>.

Endpoints
  POST /auth/signup   {name, email, password}  -> {token, user}
  POST /auth/login    {email, password}        -> {token, user}
  POST /auth/logout
  GET  /auth/me                                  -> user
  GET  /me/state                                 -> {key: value} saved progress
  PUT  /me/state      {items: {key: value|null}} -> save (null deletes)
  GET  /me/assessments                           -> field-questionnaire history (newest first)
"""
import base64
import hashlib
import hmac
import re
import secrets
import time
from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from db import Assessment, AuthSession, User, UserState, get_db, now

router = APIRouter()
ITERATIONS = 200_000
SESSION_DAYS = 30
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# progress keys the browser may store on the server (mirrors localStorage keys)
STATE_KEY_RE = re.compile(r"^ep_(result|quiz|shortlist|career|career_.{1,40}|skill_levels|skillgap|marks|progprefs)$")
MAX_STATE_BYTES = 64_000
_failed = {}  # email -> [timestamps] (in memory; resets on restart)


# ---------------- passwords & tokens ----------------
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return f"pbkdf2_sha256${ITERATIONS}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_b64, hash_b64 = stored.split("$")
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), base64.b64decode(salt_b64), int(iters))
        return algo == "pbkdf2_sha256" and hmac.compare_digest(dk, base64.b64decode(hash_b64))
    except (ValueError, TypeError):
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _new_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(AuthSession(token_hash=_token_hash(token), user_id=user.id, expires_at=now() + timedelta(days=SESSION_DAYS)))
    db.commit()
    return token


def _public(user: User):
    return {"id": user.id, "name": user.name, "email": user.email, "created_at": user.created_at.isoformat()}


# ---------------- dependencies ----------------
def _user_from_header(authorization: str | None, db: Session):
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    sess = db.get(AuthSession, _token_hash(authorization[7:].strip()))
    if sess is None:
        return None
    expires = sess.expires_at if sess.expires_at.tzinfo else sess.expires_at.replace(tzinfo=now().tzinfo)
    if expires < now():
        db.delete(sess); db.commit()
        return None
    return db.get(User, sess.user_id)


def current_user(authorization: str | None = Header(None), db: Session = Depends(get_db)) -> User:
    user = _user_from_header(authorization, db)
    if user is None:
        raise HTTPException(401, "Please log in.")
    return user


def optional_user(authorization: str | None = Header(None), db: Session = Depends(get_db)):
    return _user_from_header(authorization, db)


# ---------------- request models ----------------
class SignupIn(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., max_length=128)
    name: str | None = Field(None, max_length=80)  # optional; defaults to the part of the email before "@"


# strong password: 8+ characters with upper case, lower case, a number and a symbol (same rule as the frontend)
def password_problem(pw: str):
    if len(pw) < 8:
        return "Password must be at least 8 characters."
    missing = [what for what, rx in (("an upper-case letter", r"[A-Z]"), ("a lower-case letter", r"[a-z]"),
                                     ("a number", r"\d"), ("a symbol", r"[^A-Za-z0-9]")) if not re.search(rx, pw)]
    return f"Password needs {', '.join(missing)}." if missing else None


class LoginIn(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., max_length=128)


class StateIn(BaseModel):
    items: dict[str, object]


# ---------------- endpoints ----------------
@router.post("/auth/signup")
def signup(body: SignupIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    if not EMAIL_RE.match(email):
        raise HTTPException(422, "Please enter a valid email address.")
    problem = password_problem(body.password)
    if problem:
        raise HTTPException(422, problem)
    name = " ".join((body.name or "").split()) or email.split("@")[0]
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists. Please log in.")
    user = User(name=name, email=email, password_hash=hash_password(body.password))
    db.add(user); db.commit(); db.refresh(user)
    return {"token": _new_session(db, user), "user": _public(user)}


@router.post("/auth/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    email = body.email.strip().lower()
    recent = [t for t in _failed.get(email, []) if time.time() - t < 900]
    if len(recent) >= 5:
        raise HTTPException(429, "Too many attempts. Please wait 15 minutes and try again.")
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(body.password, user.password_hash):
        _failed[email] = recent + [time.time()]
        raise HTTPException(401, "Email or password is incorrect.")
    _failed.pop(email, None)
    return {"token": _new_session(db, user), "user": _public(user)}


@router.post("/auth/logout")
def logout(authorization: str | None = Header(None), db: Session = Depends(get_db)):
    if authorization and authorization.lower().startswith("bearer "):
        db.execute(delete(AuthSession).where(AuthSession.token_hash == _token_hash(authorization[7:].strip())))
        db.commit()
    return {"ok": True}


@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return _public(user)


@router.get("/me/state")
def get_state(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(UserState).where(UserState.user_id == user.id)).all()
    return {r.key: r.value for r in rows}


@router.put("/me/state")
def put_state(body: StateIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    import json
    bad = [k for k in body.items if not STATE_KEY_RE.match(k)]
    if bad:
        raise HTTPException(422, f"Not a saveable key: {bad}")
    for k, v in body.items.items():
        if v is not None and len(json.dumps(v)) > MAX_STATE_BYTES:
            raise HTTPException(413, f"{k} is too large")
        row = db.scalar(select(UserState).where(UserState.user_id == user.id, UserState.key == k))
        if v is None:
            if row:
                db.delete(row)
        elif row:
            row.value = v
            row.updated_at = now()
        else:
            db.add(UserState(user_id=user.id, key=k, value=v))
    db.commit()
    return {"saved": sorted(body.items)}


@router.get("/me/assessments")
def assessments(user: User = Depends(current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(Assessment).where(Assessment.user_id == user.id)
                      .order_by(Assessment.created_at.desc()).limit(20)).all()
    return [{"id": a.id, "kind": a.kind, "created_at": a.created_at.isoformat(),
             "top_fields": [{"field": t["field"], "probability": t["probability"]} for t in a.result.get("top_fields", [])]}
            for a in rows]


def save_assessment(db: Session, user: User, answers: dict, result: dict):
    db.add(Assessment(user_id=user.id, kind="field", answers=answers, result=result))
    db.commit()
