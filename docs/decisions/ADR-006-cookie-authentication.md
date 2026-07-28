# ADR-006: HttpOnly cookie JWT authentication

- Status: Accepted
- Date: 2026-07-14

## Context
JWTs were stored in `localStorage` (XSS-exposed) and returned in the login body.

## Decision
Store access + refresh tokens in **HttpOnly cookies**. `CookieJWTAuthentication` reads the
access cookie (header still allowed for tooling) and enforces CSRF on unsafe methods. Short
access lifetime; refresh rotation with blacklist via `/api/auth/refresh/`. Logout blacklists
and clears cookies. Tokens are never in the response body or JS-readable.

## Consequences
- JS cannot read tokens. The SPA uses `credentials: "include"` + `X-CSRFToken`.
- CSRF is required for cookie-authenticated unsafe requests (never disabled).
