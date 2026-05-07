export function MenuList({ filteredItems, menu, pickItem, selectedItem }) {
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
    </section>
  );
}
