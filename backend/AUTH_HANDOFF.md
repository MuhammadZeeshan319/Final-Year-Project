# Handoff: accounts - email verification & password reset

**Owner:** next team member (backend).

## What already works
- **Sign up** with email + strong password - `POST /auth/signup {email, password}` (name optional)
  - Strong password = 8+ characters, upper case, lower case, number, symbol. Checked in the browser
    (`frontend/js/auth-forms.js`) **and** on the server (`password_problem()` in `backend/auth.py`).
- **Log in** - `POST /auth/login {email, password}`; log out - `POST /auth/logout`; `GET /auth/me`.
- Passwords: salted PBKDF2-SHA256 (200,000 iterations). Sessions: random token, only its SHA-256 stored, 30 days.
- 5 failed logins per email -> 15-minute lock.
- Saved progress `GET/PUT /me/state`, result history `GET /me/assessments` (`backend/auth.py`, tables in `backend/db.py`).
- **No guest mode:** pages with `<body data-auth="required">` (questionnaire, results, fields, skill gap,
  dashboard) send logged-out visitors to `login.html?next=...` (`frontend/js/content.js`, bottom).
- Tests: `python -m pytest backend/test_api.py` (account tests at the end).

## Your tasks

### 1. Email verification code (after sign-up)
Planned flow: sign up with email + password -> we email a **6-digit code** -> student enters it -> account verified.

Suggested endpoints:
| Endpoint | Request | Responses |
|---|---|---|
| `POST /auth/send-code` | `{email, purpose: "verify" \| "reset"}` | `200 {"sent": true, "expires_in": 600}` · `429` too many requests |
| `POST /auth/verify-email` | `{email, code}` | `200 {"verified": true}` · `400 "That code is wrong or has expired."` · `429` |

Backend changes:
- `users.email_verified` (bool, default false) + `users.verified_at`.
- New table `email_codes`: `email`, `purpose`, `code_hash` (never store the plain code), `expires_at` (10 min),
  `attempts`, `created_at`. Code: `f"{secrets.randbelow(10**6):06d}"`; compare hashes with `hmac.compare_digest`.
- Limits: 5 attempts per code, ~3 codes per email per 15 minutes.
- Decide with the team: block log-in until verified, or allow log-in and show a "verify your email" banner.
- Sending email: Python `smtplib` with SMTP (e.g. a Gmail app password for the demo) or a service
  (SendGrid / Mailgun / Brevo). Credentials in environment variables only. For local development, an env
  flag that prints the code in the server console instead of emailing it.

Frontend changes needed (small): after `EP.auth.signup()` in `frontend/js/auth-forms.js`, show a code step
(a single 6-digit numeric input with `autocomplete="one-time-code"`, plus "resend code") and call `/auth/verify-email`.

### 2. Forgot password
`login.html` shows "Forgot password? Reset is coming soon." Suggested: `POST /auth/send-code {purpose: "reset"}`
then `POST /auth/reset-password {email, code, new_password}` (apply `password_problem()`; delete the user's
other sessions after a reset).

### 3. Production hardening
- Serve over HTTPS; consider an HttpOnly, Secure cookie instead of the token in localStorage.
- Move the in-memory login throttle (`_failed` in `auth.py`) to the database or Redis if running several workers.
- PostgreSQL: set `DATABASE_URL` (see `backend/db.py`); no code changes needed.
