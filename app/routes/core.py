from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from app.auth import AuthUser, require_user
from app.recipe import get_gemini_config_status


def register(api: FastAPI, *, production: bool) -> None:
    @api.get("/")
    async def root():
        return HTMLResponse(UI_HTML)

    @api.get("/docs-redirect")
    async def docs_redirect():
        if production:
            raise HTTPException(status_code=404, detail="Docs are disabled")
        return HTMLResponse('<meta http-equiv="refresh" content="0; url=/docs">')

    @api.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.get("/config-check")
    async def config_check(user: AuthUser = Depends(require_user)):
        gemini = await get_gemini_config_status()
        return {"service": "menu-recipe-agent", "gemini": gemini, "user": user.public_id}


UI_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Menu + Recipe Agent</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #f6f8fb; color: #1b2430; }
    .wrap { max-width: 920px; margin: 0 auto; padding: 24px; }
    .card { background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 12px rgba(0,0,0,.06); }
    h1 { margin-top: 0; }
    h2 { margin: 0 0 12px 0; font-size: 18px; }
    label { display: block; font-size: 13px; margin-bottom: 6px; color: #425466; }
    input, textarea { width: 100%; padding: 10px; border: 1px solid #d7e0ea; border-radius: 8px; box-sizing: border-box; }
    textarea { min-height: 90px; resize: vertical; }
    .row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .actions { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 12px; }
    button, .linkbtn { border: 0; border-radius: 8px; padding: 10px 14px; background: #2f6fed; color: #fff; cursor: pointer; text-decoration: none; display: inline-block; }
    button.secondary { background: #516173; }
    pre { background: #0f172a; color: #d9e2f2; padding: 12px; border-radius: 8px; overflow: auto; max-height: 360px; }
    .hint { color: #5f6b7a; font-size: 13px; margin-top: 8px; }
    @media (max-width: 760px) { .row { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Menu + Recipe Agent</h1>
    <p class="hint">Use this page to test config, scrape menus, and generate dish recipes.</p>

    <div class="card">
      <h2>Bearer Token</h2>
      <label for="bearerToken">Token</label>
      <input id="bearerToken" placeholder="Paste admin CLI token" type="password" />
    </div>

    <div class="card">
      <h2>Quick Checks</h2>
      <div class="actions">
        <button onclick="callApi('/health')">Health</button>
        <button onclick="callApi('/config-check')">Config Check</button>
        <a class="linkbtn secondary" href="/docs" target="_blank" rel="noreferrer">Open Swagger</a>
      </div>
    </div>

    <div class="card">
      <h2>Menu Scraper</h2>
      <label for="restaurantUrl">Restaurant URL</label>
      <input id="restaurantUrl" placeholder="https://example.com/menu" />
      <div class="actions">
        <button onclick="runMenu()">Scrape Menu</button>
      </div>
    </div>

    <div class="card">
      <h2>Recipe Lookup</h2>
      <div class="row">
        <div>
          <label for="dishName">Dish Name</label>
          <input id="dishName" placeholder="Chicken Alfredo" />
        </div>
        <div>
          <label for="restaurantName">Restaurant Name (optional)</label>
          <input id="restaurantName" placeholder="Restaurant name" />
        </div>
      </div>
      <label for="menuDescription">Menu Description (optional)</label>
      <textarea id="menuDescription" placeholder="Creamy pasta with grilled chicken"></textarea>
      <div class="actions">
        <button onclick="runRecipe()">Get Recipe</button>
        <button class="secondary" onclick="runAgent()">Run Full Flow (Menu + Recipe)</button>
      </div>
    </div>

    <div class="card">
      <h2>Response</h2>
      <pre id="output">Ready.</pre>
    </div>
  </div>

  <script>
    const output = document.getElementById("output");

    function pretty(data) {
      return JSON.stringify(data, null, 2);
    }

    async function callApi(path, options = {}) {
      output.textContent = "Loading...";
      try {
        const token = document.getElementById("bearerToken").value.trim();
        const headers = new Headers(options.headers || {});
        if (token) {
          headers.set("Authorization", `Bearer ${token}`);
        }
        const response = await fetch(path, { ...options, headers });
        const data = await response.json();
        output.textContent = pretty(data);
      } catch (err) {
        output.textContent = `Request failed: ${err}`;
      }
    }

    function runMenu() {
      const restaurantUrl = document.getElementById("restaurantUrl").value.trim();
      if (!restaurantUrl) {
        output.textContent = "Please provide a restaurant URL.";
        return;
      }
      callApi(`/menu?restaurant_url=${encodeURIComponent(restaurantUrl)}`);
    }

    function runRecipe() {
      const dishName = document.getElementById("dishName").value.trim();
      const restaurantName = document.getElementById("restaurantName").value.trim();
      const menuDescription = document.getElementById("menuDescription").value.trim();
      if (!dishName) {
        output.textContent = "Please provide a dish name.";
        return;
      }
      callApi("/recipe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dish_name: dishName,
          restaurant_name: restaurantName || null,
          menu_description: menuDescription || null
        })
      });
    }

    function runAgent() {
      const restaurantUrl = document.getElementById("restaurantUrl").value.trim();
      const dishName = document.getElementById("dishName").value.trim();
      if (!restaurantUrl || !dishName) {
        output.textContent = "Please provide both restaurant URL and dish name for full flow.";
        return;
      }
      callApi(`/agent/run?restaurant_url=${encodeURIComponent(restaurantUrl)}&dish_name=${encodeURIComponent(dishName)}`);
    }
  </script>
</body>
</html>
"""
