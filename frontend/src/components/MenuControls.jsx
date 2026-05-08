export function MenuControls({
  error,
  generateRecipe,
  loading,
  manualDish,
  menu,
  query,
  recipeOptions,
  restaurantName,
  restaurantUrl,
  scrapeMenu,
  setManualDish,
  setQuery,
  setRecipeOptions,
  setRestaurantName,
  setRestaurantUrl,
  setSelectedItem,
  setUploadFile,
  uploadMenu,
}) {
  return (
    <form className="panel controls" onSubmit={scrapeMenu}>
      <label htmlFor="restaurant-url">Restaurant menu URL</label>
      <div className="input-row">
        <input
          id="restaurant-url"
          value={restaurantUrl}
          onChange={(event) => setRestaurantUrl(event.target.value)}
          placeholder="https://restaurant.example/menu"
        />
        <button type="submit" disabled={loading === "menu"}>
          {loading === "menu" ? "Scraping" : "Scrape"}
        </button>
      </div>

      <div className="divider">or upload a menu</div>

      <label htmlFor="restaurant-name">Restaurant name hint</label>
      <input
        id="restaurant-name"
        value={restaurantName}
        onChange={(event) => setRestaurantName(event.target.value)}
        placeholder="Optional restaurant name"
      />

      <label htmlFor="menu-upload">Image or PDF menu</label>
      <div className="input-row">
        <input
          id="menu-upload"
          type="file"
          accept="image/png,image/jpeg,application/pdf"
          onChange={(event) => setUploadFile(event.target.files?.[0] || null)}
        />
        <button type="button" onClick={uploadMenu} disabled={loading === "upload"}>
          {loading === "upload" ? "Extracting" : "Upload"}
        </button>
      </div>

      <label htmlFor="menu-search">Search scraped dishes</label>
      <input
        id="menu-search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="pizza, curry, tacos"
        disabled={!menu}
      />

      <label htmlFor="manual-dish">Selected or manual dish</label>
      <div className="input-row">
        <input
          id="manual-dish"
          value={manualDish}
          onChange={(event) => {
            setManualDish(event.target.value);
            setSelectedItem(null);
          }}
          placeholder="Type a dish if it was not found"
        />
        <button type="button" onClick={() => generateRecipe()} disabled={loading === "recipe"}>
          {loading === "recipe" ? "Cooking" : "Recipe"}
        </button>
      </div>

      <div className="customization-grid">
        <div>
          <label htmlFor="servings">Servings</label>
          <input
            id="servings"
            type="number"
            min="1"
            max="24"
            value={recipeOptions.servings}
            onChange={(event) => updateRecipeOption("servings", event.target.value)}
          />
        </div>
        <div>
          <label htmlFor="time-limit">Time limit</label>
          <input
            id="time-limit"
            type="number"
            min="5"
            max="480"
            value={recipeOptions.timeLimitMinutes}
            onChange={(event) => updateRecipeOption("timeLimitMinutes", event.target.value)}
            placeholder="Minutes"
          />
        </div>
      </div>

      <label htmlFor="dietary-preference">Dietary preference</label>
      <input
        id="dietary-preference"
        value={recipeOptions.dietaryPreference}
        onChange={(event) => updateRecipeOption("dietaryPreference", event.target.value)}
        placeholder="Vegetarian, gluten-free, high protein"
      />

      <div className="customization-grid">
        <div>
          <label htmlFor="spice-level">Spice level</label>
          <select
            id="spice-level"
            value={recipeOptions.spiceLevel}
            onChange={(event) => updateRecipeOption("spiceLevel", event.target.value)}
          >
            <option value="">No preference</option>
            <option value="mild">Mild</option>
            <option value="medium">Medium</option>
            <option value="hot">Hot</option>
          </select>
        </div>
        <div>
          <label htmlFor="equipment">Equipment</label>
          <input
            id="equipment"
            value={recipeOptions.equipment}
            onChange={(event) => updateRecipeOption("equipment", event.target.value)}
            placeholder="Air fryer, skillet"
          />
        </div>
      </div>

      {error && <div className="error">{error}</div>}
    </form>
  );

  function updateRecipeOption(key, value) {
    setRecipeOptions((current) => ({ ...current, [key]: value }));
  }
}
