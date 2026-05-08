# Menu + Recipe Agent (Python)

Starter FastAPI service that:
- Scrapes a restaurant page for likely menu entries.
- Extracts menu items from uploaded image/PDF menus.
- Returns a recipe for a selected dish with scraped menu context (Gemini-backed when configured).
- Stores uploaded menus, extracted items, and generated recipes in local SQLite history.
- Exposes an end-to-end agent endpoint and a React frontend workflow.

## Quick start

1. Create and activate a virtual environment:

```powershell
cd menu-recipe-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Configure environment variables:

```powershell
$env:GEMINI_API_KEY="your_gemini_key_here"
# optional:
$env:GEMINI_MODEL="gemini-2.5-pro"
$env:UPLOAD_RETENTION_DAYS="30"
```

You can also place these in `.env` (preferred). The app auto-loads `.env` and
then `.env.example` as fallback values.

4. Create a bearer-token user:

```powershell
python -m app.admin create-user --name "Local Admin"
```

Copy the generated bearer token into the frontend token field, or pass it in
the `Authorization: Bearer ...` header for protected API calls.

5. Run the API:

```powershell
uvicorn app.main:app --reload
```

6. Run the frontend in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Or start both the API and frontend with one command from the project root:

```powershell
.\scripts\dev.ps1
```

7. Open the app or docs:

- http://127.0.0.1:5173
- http://127.0.0.1:8000/docs

## Endpoints

- `GET /health`
- `GET /config-check`
- `GET /menu?restaurant_url=...`
- `POST /uploads/menu` requires bearer token
- `GET /history` requires bearer token
- `GET /history/{id}` requires bearer token
- `DELETE /history/{id}` requires bearer token
- `POST /recipe` requires bearer token
- `GET /agent/run?restaurant_url=...&dish_name=...` requires bearer token
- `POST /agent/run` requires bearer token

`POST /agent/run` is the preferred frontend endpoint. It accepts:

```json
{
  "restaurant_url": "https://example.com/menu",
  "dish_name": "Spicy Rigatoni",
  "selected_item": {
    "id": "abc123",
    "name": "Spicy Rigatoni",
    "description": "Vodka sauce, basil, parmesan",
    "price": "$18",
    "category": "Pasta",
    "url": "https://example.com/menu"
  }
}
```

## Tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## Static checks

Install development dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
cd frontend
npm install
```

Run lint checks:

```powershell
.\.venv\Scripts\ruff.exe check app api scripts tests
cd frontend
npm run lint
```

## Administration

```powershell
python -m app.admin create-user --name "Local Admin"
python -m app.admin cleanup-uploads
python -m app.admin cleanup-uploads --retention-days 7
```

## Vercel Preview Deploy

This repo includes `vercel.json` and `api/index.py` so Vercel can build the
React frontend and run the FastAPI app as a Python serverless function.

Before deploying, add these environment variables in Vercel Project Settings:

- `GEMINI_API_KEY`
- `GEMINI_MODEL`
- `APP_ENV=production`
- `CORS_ALLOWED_ORIGINS=https://your-vercel-domain.vercel.app`
- `UPLOAD_RETENTION_DAYS=30`
- `USER_STORAGE_QUOTA_BYTES=262144000`
- `UPLOAD_RATE_LIMIT_PER_MINUTE=10`
- `RECIPE_RATE_LIMIT_PER_MINUTE=20`

Then deploy a preview. If the Vercel CLI is not installed globally, use `npx`:

```powershell
npx vercel deploy . -y
```

The frontend uses same-origin API requests in production, so `VITE_API_BASE`
does not need to be set for Vercel.

Vercel serverless storage is ephemeral. This config is good for previewing the
full app, but production history, users, and uploads should move to durable
services such as a managed database and object storage before real users rely on
it.

## Notes

- Current scraping logic is generic and extracts likely names, descriptions, prices, and categories.
- Uploaded images/PDFs are stored locally under `data/uploads`, scoped to bearer-token users, counted against each user's quota, and cleaned up after `UPLOAD_RETENTION_DAYS` days.
- History routes use random public IDs instead of sequential SQLite IDs.
- Recipe retrieval tries Gemini first, then falls back to a starter dataset/template.
- Use `GET /config-check` to confirm Gemini key/model are configured and reachable.
- Next upgrades:
  - Add domain-specific restaurant parsers.
  - Add trusted recipe API integration.
  - Add caching and fuzzy matching.
