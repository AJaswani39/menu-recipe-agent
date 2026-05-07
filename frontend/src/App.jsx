import React from "react";
import { createRoot } from "react-dom/client";
import { HistoryPanel } from "./components/HistoryPanel";
import { MenuControls } from "./components/MenuControls";
import { MenuList } from "./components/MenuList";
import { RecipePanel } from "./components/RecipePanel";
import { TokenPanel } from "./components/TokenPanel";
import { useMenuRecipeAgent } from "./hooks/useMenuRecipeAgent";
import "./styles.css";

function App() {
  const agent = useMenuRecipeAgent();

  return (
    <main className="shell">
      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Menu Recipe Agent</p>
            <h1>Turn a restaurant menu item into a cookable recipe.</h1>
          </div>
          <div className="topbar-actions">
            <div className={`token-state ${agent.token ? "ready" : ""}`}>
              {agent.token ? "Token ready" : "Token needed"}
            </div>
            <div className="status">{agent.status}</div>
          </div>
        </header>

        {!agent.token && (
          <TokenPanel
            saveToken={agent.saveToken}
            setTokenDraft={agent.setTokenDraft}
            tokenDraft={agent.tokenDraft}
          />
        )}

        <section className="app-layout">
          <HistoryPanel
            activeHistoryId={agent.activeHistoryId}
            clearToken={agent.clearToken}
            deleteHistory={agent.deleteHistory}
            historyItems={agent.historyItems}
            loading={agent.loading}
            openHistory={agent.openHistory}
            token={agent.token}
          />

          <div>
            <section className="grid">
              <MenuControls
                error={agent.error}
                generateRecipe={agent.generateRecipe}
                loading={agent.loading}
                manualDish={agent.manualDish}
                menu={agent.menu}
                query={agent.query}
                restaurantName={agent.restaurantName}
                restaurantUrl={agent.restaurantUrl}
                scrapeMenu={agent.scrapeMenu}
                setManualDish={agent.setManualDish}
                setQuery={agent.setQuery}
                setRestaurantName={agent.setRestaurantName}
                setRestaurantUrl={agent.setRestaurantUrl}
                setSelectedItem={agent.setSelectedItem}
                setUploadFile={agent.setUploadFile}
                uploadMenu={agent.uploadMenu}
              />
              <MenuList
                filteredItems={agent.filteredItems}
                menu={agent.menu}
                pickItem={agent.pickItem}
                selectedItem={agent.selectedItem}
              />
            </section>

            <RecipePanel recipe={agent.recipe} />
          </div>
        </section>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
