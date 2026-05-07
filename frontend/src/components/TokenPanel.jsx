export function TokenPanel({ saveToken, setTokenDraft, tokenDraft }) {
  return (
    <form className="panel token-panel" onSubmit={saveToken}>
      <div>
        <h2>Bearer token</h2>
        <p className="empty">Paste the one-time token from the admin CLI to unlock uploads, recipes, and history.</p>
      </div>
      <div className="input-row">
        <input
          value={tokenDraft}
          onChange={(event) => setTokenDraft(event.target.value)}
          placeholder="Bearer token"
          type="password"
          autoComplete="off"
        />
        <button type="submit">Save</button>
      </div>
    </form>
  );
}
