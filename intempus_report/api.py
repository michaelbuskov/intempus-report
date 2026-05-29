"""HTTP client for the Intempus API.

Authentication uses Django session cookies:
  1. GET /web/login/ — fetches the CSRF token from the response cookie
  2. POST /web/login/ — submits credentials as form data, receives a session cookie
  3. All subsequent requests use the session cookie automatically via httpx.Client

The data endpoint is:
  GET /web/v1/work_report/create_stream/
  Key query params:
    format=json
    q=start_date__gte:YYYY-MM-DD start_date__lte:YYYY-MM-DD
    fields=case__name,case__number,amount,unit,work_type__name,start_date

Response is a list (or paginated object with "objects" key) of dicts:
  {"case__name": "Project X", "case__number": "P-001", "amount": 7.5,
   "unit": "hours", "work_type__name": "Development", "start_date": "2026-05-14"}
"""

from __future__ import annotations

import calendar
import json as _json
import sys
from datetime import date
from typing import Any

import httpx

from .config import AuthConfig

LOGIN_PATH = "/web/login/"
STREAM_PATH = "/web/v1/work_report/create_stream/"

STREAM_FIELDS = ",".join([
    "case__name",
    "case__number",
    "amount",
    "unit",
    "work_type__name",
    "start_date",
])


class IntempusClient:
    def __init__(self, auth: AuthConfig, *, debug: bool = False) -> None:
        self._auth = auth
        self._base = auth.base_url
        self._debug = debug
        self._client = httpx.Client(
            base_url=self._base,
            headers={"Accept": "application/json"},
            follow_redirects=True,
            timeout=60.0,
        )

    def _dbg(self, *args: object) -> None:
        if self._debug:
            print("[DEBUG]", *args, file=sys.stderr)

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def login(self) -> None:
        """Log in and obtain a session cookie."""
        self._dbg(f"GET {self._base}{LOGIN_PATH}")
        resp = self._client.get(LOGIN_PATH)
        self._dbg(f"  → {resp.status_code}, cookies: {dict(self._client.cookies)}")
        _raise_for_status(resp, "Could not reach login page")

        csrf = self._client.cookies.get("csrftoken")
        if not csrf:
            raise RuntimeError(
                "No csrftoken cookie found after GET /web/login/. "
                "The login page may have changed."
            )

        self._dbg(f"POST {self._base}{LOGIN_PATH} (username={self._auth.username!r})")
        resp = self._client.post(
            LOGIN_PATH,
            data={
                "csrfmiddlewaretoken": csrf,
                "json": "true",
                "username": self._auth.username,
                "password": self._auth.password,
            },
            headers={"X-CSRFToken": csrf, "Referer": f"{self._base}{LOGIN_PATH}"},
        )
        self._dbg(f"  → {resp.status_code}, final URL: {resp.url}")
        self._dbg(f"  cookies after login: {dict(self._client.cookies)}")
        try:
            self._dbg(f"  response body: {resp.text[:300]}")
        except Exception:
            pass
        _raise_for_status(resp, "Login failed — check your username and password")

        if not self._client.cookies.get("sessionid"):
            if "login" in str(resp.url):
                raise RuntimeError(
                    "Login appeared to fail — still on the login page. "
                    "Check your credentials."
                )

    # ------------------------------------------------------------------
    # Data fetching
    # ------------------------------------------------------------------

    def fetch_month_report(self, year: int, month: int) -> list[dict[str, Any]]:
        """Fetch all work report entries for the given month."""
        last_day = calendar.monthrange(year, month)[1]
        start = date(year, month, 1).isoformat()
        end = date(year, month, last_day).isoformat()
        query = f"start_date__gte:{start} start_date__lte:{end}"

        self._dbg(f"Fetching {STREAM_PATH} q={query!r}")

        all_entries: list[dict[str, Any]] = []
        offset = 0
        limit = 1000

        while True:
            params = {
                "format": "json",
                "q": query,
                "fields": STREAM_FIELDS,
                "limit": limit,
                "offset": offset,
            }
            resp = self._client.get(STREAM_PATH, params=params)
            self._dbg(f"  → {resp.status_code}  URL: {resp.url}")
            self._dbg(f"  raw body (first 500 chars): {resp.text[:500]}")
            _raise_for_status(resp, f"Failed to fetch work reports for {year}-{month:02d}")

            data = resp.json()
            if isinstance(data, list):
                self._dbg(f"  list response: {len(data)} entries")
                all_entries.extend(data)
                break
            else:
                # create_stream uses "first_page"; Tastypie standard uses "objects"
                objects = data.get("first_page") or data.get("objects", [])
                meta = data.get("meta", {})
                self._dbg(f"  paginated response: {len(objects)} objects, meta={meta}")
                all_entries.extend(objects)
                if meta.get("next") is None or len(objects) < limit:
                    break
                offset += limit

        return all_entries

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "IntempusClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _raise_for_status(resp: httpx.Response, message: str) -> None:
    if resp.is_error:
        raise RuntimeError(
            f"{message}\n"
            f"  Status: {resp.status_code}\n"
            f"  URL: {resp.url}\n"
            f"  Body: {resp.text[:500]}"
        )

