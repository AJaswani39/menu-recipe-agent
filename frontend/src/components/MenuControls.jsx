export function MenuControls({
  error,
  generateRecipe,
  loading,
  manualDish,
  menu,
  query,
  restaurantName,
  restaurantUrl,
  scrapeMenu,
  setManualDish,
  setQuery,
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

      {error && <div className="error">{error}</div>}
    </form>
  );
}
