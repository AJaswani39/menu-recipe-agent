export function HistoryPanel({
  activeHistoryId,
  clearToken,
  deleteHistory,
  historyItems,
  loading,
  openHistory,
  token,
}) {
  return (
    <aside className="panel history-panel">
      <div className="panel-heading">
        <h2>History</h2>
        <div className="history-tools">
          <span>{historyItems.length}</span>
          {token && (
            <button type="button" className="clear-token" onClick={clearToken}>
              Clear token
            </button>
          )}
        </div>
      </div>
      {historyItems.length === 0 && (
        <p className="empty">
          {token ? "Saved uploads and recipes appear here." : "Save a token to load your history."}
        </p>
      )}
      <div className="history-list">
        {historyItems.map((item) => (
          <div
            className={`history-item ${activeHistoryId === item.id ? "active" : ""}`}
            key={item.id}
          >
            <button type="button" onClick={() => openHistory(item.id)}>
              <strong>{item.restaurant}</strong>
              <small>{item.source_label}</small>
              <span>{item.recipe_dish || `${item.menu_item_count} items`}</span>
            </button>
            <button
              className="icon-button"
              type="button"
              aria-label={`Delete ${item.source_label}`}
              onClick={() => deleteHistory(item.id)}
              disabled={loading === "history"}
            >
              x
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}
