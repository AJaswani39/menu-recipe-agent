export function MenuList({
  explainSelectedItem,
  filteredItems,
  itemExplanation,
  loading,
  menu,
  pickItem,
  selectedItem,
}) {
  return (
    <section className="panel menu-list" aria-live="polite">
      <div className="panel-heading">
        <h2>Menu Items</h2>
        <span>{filteredItems.length || 0}</span>
      </div>
      {!menu && <p className="empty">Scrape a menu to see dish candidates here.</p>}
      {menu && filteredItems.length === 0 && <p className="empty">No dishes match that search.</p>}
      <div className="items">
        {filteredItems.map((item) => (
          <button
            type="button"
            key={item.id}
            className={`menu-item ${selectedItem?.id === item.id ? "selected" : ""}`}
            onClick={() => pickItem(item)}
          >
            <span className="item-main">
              <strong>{item.name}</strong>
              {item.description && <small>{item.description}</small>}
            </span>
            <span className="item-meta">
              {item.category && <em>{item.category}</em>}
              {item.price && <b>{item.price}</b>}
            </span>
          </button>
        ))}
      </div>
      {selectedItem && (
        <div className="dish-explainer">
          <div className="section-heading">
            <h3>{selectedItem.name}</h3>
            <button
              type="button"
              className="secondary-button"
              onClick={explainSelectedItem}
              disabled={loading === "explain"}
            >
              {loading === "explain" ? "Explaining" : "Explain"}
            </button>
          </div>
          {!itemExplanation && (
            <p className="empty">Get likely flavors, allergens, and substitutions.</p>
          )}
          {itemExplanation && (
            <div className="explanation-grid">
              <p>{itemExplanation.summary}</p>
              <ExplanationList title="Flavor" items={itemExplanation.flavor_profile} />
              <ExplanationList title="Allergens" items={itemExplanation.likely_allergens} />
              <ExplanationList title="Swaps" items={itemExplanation.substitutions} />
              <p className="source">
                {itemExplanation.confidence} · {itemExplanation.source}
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
}

function ExplanationList({ title, items }) {
  if (!items?.length) return null;
  return (
    <div>
      <h4>{title}</h4>
      <ul className="compact-list">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
