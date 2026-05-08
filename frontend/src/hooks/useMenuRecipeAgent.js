import { useEffect, useMemo, useState } from "react";
import { apiRequest } from "../api";

const TOKEN_STORAGE_KEY = "menu_recipe_agent_bearer_token";
const DEFAULT_RECIPE_OPTIONS = {
  servings: "4",
  dietaryPreference: "",
  spiceLevel: "",
  equipment: "",
  timeLimitMinutes: "",
};

export function useMenuRecipeAgent() {
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_STORAGE_KEY) || "");
  const [tokenDraft, setTokenDraft] = useState("");
  const [restaurantUrl, setRestaurantUrl] = useState("");
  const [menu, setMenu] = useState(null);
  const [selectedItem, setSelectedItem] = useState(null);
  const [itemExplanation, setItemExplanation] = useState(null);
  const [manualDish, setManualDish] = useState("");
  const [query, setQuery] = useState("");
  const [recipe, setRecipe] = useState(null);
  const [historyItems, setHistoryItems] = useState([]);
  const [activeHistoryId, setActiveHistoryId] = useState(null);
  const [restaurantName, setRestaurantName] = useState("");
  const [uploadFile, setUploadFile] = useState(null);
  const [recipeOptions, setRecipeOptions] = useState(DEFAULT_RECIPE_OPTIONS);
  const [status, setStatus] = useState("Ready");
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");

  const filteredItems = useMemo(() => {
    const items = menu?.menu_items || [];
    const needle = query.trim().toLowerCase();
    if (!needle) return items;
    return items.filter((item) =>
      [item.name, item.description, item.category]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(needle),
    );
  }, [menu, query]);

  useEffect(() => {
    if (token) {
      loadHistory();
    } else {
      setHistoryItems([]);
      setActiveHistoryId(null);
    }
  }, [token]);

  async function request(path, options = {}) {
    return apiRequest(path, token, options);
  }

  async function scrapeMenu(event) {
    event.preventDefault();
    if (!restaurantUrl.trim()) {
      setError("Enter a restaurant menu URL.");
      return;
    }
    setLoading("menu");
    setError("");
    setRecipe(null);
    setSelectedItem(null);
    setItemExplanation(null);
    setStatus("Scraping menu");
    try {
      const data = await request(`/menu?restaurant_url=${encodeURIComponent(restaurantUrl.trim())}`);
      setMenu(data);
      setActiveHistoryId(null);
      setStatus(`Found ${data.menu_items.length} likely menu items`);
    } catch (err) {
      setMenu(null);
      setStatus("Menu scrape failed");
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function uploadMenu(event) {
    event.preventDefault();
    if (!token) {
      setError("Add your bearer token before uploading a menu.");
      return;
    }
    if (!uploadFile) {
      setError("Choose an image or PDF menu to upload.");
      return;
    }
    setLoading("upload");
    setError("");
    setRecipe(null);
    setSelectedItem(null);
    setItemExplanation(null);
    setStatus("Extracting uploaded menu");
    try {
      const body = new FormData();
      body.append("file", uploadFile);
      if (restaurantName.trim()) {
        body.append("restaurant_name", restaurantName.trim());
      }
      const data = await request("/uploads/menu", {
        method: "POST",
        body,
      });
      setMenu(data.menu);
      setRestaurantUrl(data.menu.source_url);
      setActiveHistoryId(data.history.id);
      setStatus(`Extracted ${data.menu.menu_items.length} menu items`);
      await loadHistory();
    } catch (err) {
      setStatus("Upload extraction failed");
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  async function generateRecipe(item = selectedItem) {
    if (!token) {
      setError("Add your bearer token before generating a recipe.");
      return;
    }
    const typedDish = manualDish.trim();
    const dishName = item?.name || typedDish;
    if (!restaurantUrl.trim()) {
      setError("Enter a restaurant menu URL first.");
      return;
    }
    if (!dishName) {
      setError("Select a dish or type one manually.");
      return;
    }
    setLoading("recipe");
    setError("");
    setRecipe(null);
    setStatus("Generating recipe");
    try {
      const data = await request("/agent/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          restaurant_url: restaurantUrl.trim(),
          dish_name: dishName,
          menu,
          selected_item: item || null,
          menu_description: item?.description || null,
          category: item?.category || null,
          price: item?.price || null,
          history_id: activeHistoryId,
          ...buildRecipeCustomizationPayload(recipeOptions),
        }),
      });
      setMenu(data.menu);
      setRecipe(data.recipe);
      setStatus("Recipe ready");
      await loadHistory();
    } catch (err) {
      setStatus("Recipe generation failed");
      setError(err.message);
    } finally {
      setLoading("");
    }
  }

  function pickItem(item) {
    setSelectedItem(item);
    setItemExplanation(null);
    setManualDish(item.name);
    setRecipe(null);
    setError("");
  }

  async function explainSelectedItem() {
    if (!token) {
      setError("Add your bearer token before explaining a dish.");
      return;
    }
    if (!selectedItem) {
      setError("Select a dish first.");
      return;
    }
    setLoading("explain");
    setError("");
    setStatus("Explaining dish");
    try {
      const data = await request("/menu/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          item: selectedItem,
          restaurant_name: menu?.restaurant || restaurantName || null,
        }),
      });
      setItemExplanation(data);
      setStatus("Dish explanation ready");
    } catch (err) {
      setError(err.message);
      setStatus("Dish explanation failed");
    } finally {
      setLoading("");
    }
  }

  async function loadHistory() {
    if (!token) {
      setHistoryItems([]);
      return;
    }
    try {
      const data = await request("/history");
      setHistoryItems(data.items || []);
    } catch {
      setHistoryItems([]);
    }
  }

  async function openHistory(id) {
    if (!token) {
      setError("Add your bearer token to open history.");
      return;
    }
    setLoading("history");
    setError("");
    try {
      const data = await request(`/history/${id}`);
      setMenu(data.menu);
      setRecipe(data.recipe || null);
      setSelectedItem(null);
      setItemExplanation(null);
      setManualDish(data.recipe?.dish || "");
      setRestaurantUrl(data.source_url || data.menu?.source_url || "");
      setActiveHistoryId(data.id);
      setStatus(`Opened ${data.source_label}`);
    } catch (err) {
      setError(err.message);
      setStatus("History load failed");
    } finally {
      setLoading("");
    }
  }

  async function deleteHistory(id) {
    if (!token) {
      setError("Add your bearer token to delete history.");
      return;
    }
    setLoading("history");
    setError("");
    try {
      await request(`/history/${id}`, { method: "DELETE" });
      if (activeHistoryId === id) {
        setActiveHistoryId(null);
      }
      await loadHistory();
      setStatus("History item deleted");
    } catch (err) {
      setError(err.message);
      setStatus("Delete failed");
    } finally {
      setLoading("");
    }
  }

  function saveToken(event) {
    event.preventDefault();
    const cleaned = tokenDraft.trim();
    if (!cleaned) {
      setError("Paste a bearer token first.");
      return;
    }
    localStorage.setItem(TOKEN_STORAGE_KEY, cleaned);
    setToken(cleaned);
    setTokenDraft("");
    setError("");
    setStatus("Token saved");
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken("");
    setTokenDraft("");
    setStatus("Token cleared");
  }

  return {
    activeHistoryId,
    clearToken,
    deleteHistory,
    error,
    filteredItems,
    generateRecipe,
    historyItems,
    itemExplanation,
    loading,
    manualDish,
    menu,
    openHistory,
    pickItem,
    query,
    recipe,
    recipeOptions,
    restaurantName,
    restaurantUrl,
    saveToken,
    scrapeMenu,
    selectedItem,
    explainSelectedItem,
    setManualDish,
    setQuery,
    setRecipeOptions,
    setRestaurantName,
    setRestaurantUrl,
    setSelectedItem,
    setUploadFile,
    status,
    token,
    tokenDraft,
    uploadMenu,
    setTokenDraft,
  };
}

function buildRecipeCustomizationPayload(options) {
  return {
    servings: toOptionalNumber(options.servings),
    dietary_preference: toOptionalText(options.dietaryPreference),
    spice_level: toOptionalText(options.spiceLevel),
    equipment: toOptionalText(options.equipment),
    time_limit_minutes: toOptionalNumber(options.timeLimitMinutes),
  };
}

function toOptionalNumber(value) {
  const parsed = Number.parseInt(String(value).trim(), 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function toOptionalText(value) {
  const cleaned = String(value || "").trim();
  return cleaned || null;
}
