# Security Best Practices Report

## Executive Summary

Security review completed for the FastAPI + React menu recipe app after adding image/PDF uploads and SQLite history. I fixed the most concrete implementation risks found during the review: unbounded upload reads, weak upload content validation, overly permissive credentialed CORS, and SSRF exposure in URL scraping. The remaining notable concern is deployment posture: the app has no authentication or authorization, which is acceptable for local development but should not be exposed publicly as-is.

## Fixed Findings

### F-1: Uploads Were Read Into Memory Before Size Enforcement

- Severity: Medium
- Location: `app/main.py`, upload route and `_save_upload_file`
- Evidence: `POST /uploads/menu` now streams chunks and enforces `MAX_UPLOAD_BYTES` at `app/main.py:22`, `app/main.py:118`, and `app/main.py:161`.
- Impact: A large multipart upload could previously consume excessive memory before processing completed.
- Fix applied: Added chunked upload saving with a 50MB cap and regression coverage.

### F-2: Upload MIME Type Trusted Browser-Provided Content Type

- Severity: Medium
- Location: `app/main.py`, `_matches_declared_type`
- Evidence: Upload route now checks declared MIME at `app/main.py:104` and validates PNG/JPEG/PDF magic bytes at `app/main.py:119` and `app/main.py:174`.
- Impact: A client could upload non-menu active content while claiming it was an image/PDF.
- Fix applied: Added allowlisted MIME validation plus basic content signature checks.

### F-3: Credentialed CORS Was Enabled Without Cookies/Auth

- Severity: Low
- Location: `app/main.py:42`
- Evidence: `allow_credentials=False`
- Impact: Credentialed CORS was unnecessary and would increase risk if cookies/auth were later added carelessly.
- Fix applied: Disabled credentialed CORS while keeping explicit localhost origins.

### F-4: URL Scraper Allowed Private/Local Network Targets

- Severity: Medium, High if deployed in a private/cloud network
- Location: `app/scraper.py:197`, `app/scraper.py:223`
- Evidence: `scrape_menu` now calls `_reject_private_destination`, which resolves hostnames and blocks loopback/private/link-local/reserved/multicast IPs at `app/scraper.py:227` and `app/scraper.py:234`.
- Impact: A user-provided URL could previously make the server request internal services.
- Fix applied: Added SSRF destination blocking for URL scraping.

### F-5: Protected APIs Had No Authentication or Authorization

- Severity: High if publicly deployed; Low for localhost-only development
- Location: `app/auth.py`, `app/main.py`, `app/admin.py`
- Evidence: Protected endpoints now require `Authorization: Bearer ...` via `require_user`, users are created with `python -m app.admin create-user`, and tokens are stored as SHA-256 hashes.
- Impact: Upload, history, recipe, and agent APIs previously had no user boundary.
- Fix applied: Added bearer-token users, owner-scoped history access, and per-user rate limits.

### F-6: Public History IDs Were Sequential

- Severity: Low locally; Medium with public access
- Location: `app/history.py`
- Evidence: History routes now accept random `public_id` values, while internal SQLite integer IDs stay private.
- Impact: Sequential IDs could make record enumeration easier if auth were incomplete.
- Fix applied: Added random public IDs and a migration backfill for existing records.

### F-7: Uploaded Files Had No Automatic Retention Cleanup

- Severity: Low to Medium depending on file sensitivity
- Location: `app/history.py`, `app/main.py`, `app/admin.py`
- Evidence: `cleanup_expired_uploads` soft-deletes old upload records and removes stored files at startup or through `python -m app.admin cleanup-uploads`.
- Impact: Uploaded menus could accumulate indefinitely.
- Fix applied: Added `UPLOAD_RETENTION_DAYS`, per-user storage quotas, and explicit cleanup command support.

## Remaining Findings

No high-confidence implementation findings remain from this pass. Before public deployment, review operational controls such as TLS termination, secret rotation, backup retention, structured audit logging, and whether uploaded image/PDF metadata should be stripped before storage.

## Positive Checks

- SQLite statements use parameterized queries in `app/history.py`.
- Uploaded files are stored under an app-managed directory and are not mounted as static files.
- React renders API data through normal JSX escaping; no `dangerouslySetInnerHTML`, `innerHTML`, `eval`, or localStorage secret storage was found in app source.
- Frontend API base is `VITE_API_BASE`, which is non-secret configuration and does not expose the Gemini API key.

## Verification

- `python -m unittest discover -s tests`: 23 tests passing.
- `npm run build`: passing.
