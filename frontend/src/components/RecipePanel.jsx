import { useEffect, useMemo, useState } from "react";

export function RecipePanel({ recipe }) {
  const [checkedIngredients, setCheckedIngredients] = useState({});
  const [copyStatus, setCopyStatus] = useState("");
  const [targetServings, setTargetServings] = useState(4);
  const baseServings = recipe?.servings || 4;
  const scaledServings = Number.isFinite(targetServings) ? targetServings : baseServings;
  const scaleMultiplier = scaledServings / baseServings;
  const shoppingListText = useMemo(
    () => buildShoppingListText(recipe, scaleMultiplier),
    [recipe, scaleMultiplier],
  );

  useEffect(() => {
    setCheckedIngredients({});
    setCopyStatus("");
    setTargetServings(recipe?.servings || 4);
  }, [recipe]);

  return (
    <section className="panel recipe-panel">
      <div className="panel-heading">
        <h2>Recipe</h2>
        {recipe && <span>{recipe.confidence}</span>}
      </div>
      {!recipe && <p className="empty">Choose a dish and generate a recipe.</p>}
      {recipe && (
        <div className="recipe-grid">
          <div>
            <h3>{recipe.dish}</h3>
            <p className="source">{recipe.source}</p>
            {recipe.notes && <p>{recipe.notes}</p>}
            <div className="serving-control">
              <label htmlFor="target-servings">Scale servings</label>
              <div className="serving-stepper">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => updateTargetServings(scaledServings - 1)}
                >
                  -
                </button>
                <input
                  id="target-servings"
                  type="number"
                  min="1"
                  max="24"
                  value={targetServings}
                  onChange={(event) => updateTargetServings(event.target.value)}
                />
                <button
                  type="button"
                  className="secondary-button"
                  onClick={() => updateTargetServings(scaledServings + 1)}
                >
                  +
                </button>
              </div>
              <p className="serving-note">Original: {baseServings} servings</p>
            </div>
          </div>
          <div>
            <div className="section-heading">
              <h3>Shopping List</h3>
              <div className="compact-actions">
                <button type="button" className="secondary-button" onClick={copyShoppingList}>
                  {copyStatus || "Copy"}
                </button>
                <button type="button" className="secondary-button" onClick={downloadShoppingList}>
                  Download
                </button>
              </div>
            </div>
            <ul className="shopping-list">
              {recipe.ingredients.map((ingredient) => {
                const checked = Boolean(checkedIngredients[ingredient]);
                return (
                  <li key={ingredient}>
                    <label className={checked ? "checked-ingredient" : ""}>
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={() => toggleIngredient(ingredient)}
                      />
                      <span>{scaleIngredient(ingredient, scaleMultiplier)}</span>
                    </label>
                  </li>
                );
              })}
            </ul>
          </div>
          <div>
            <h3>Steps</h3>
            <ol>
              {recipe.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </section>
  );

  function toggleIngredient(ingredient) {
    setCheckedIngredients((current) => ({
      ...current,
      [ingredient]: !current[ingredient],
    }));
  }

  function updateTargetServings(value) {
    const parsed = Number.parseInt(String(value), 10);
    if (!Number.isFinite(parsed)) {
      setTargetServings("");
      return;
    }
    setTargetServings(Math.min(24, Math.max(1, parsed)));
  }

  async function copyShoppingList() {
    if (!shoppingListText) return;
    try {
      await navigator.clipboard.writeText(shoppingListText);
      setCopyStatus("Copied");
      window.setTimeout(() => setCopyStatus(""), 1800);
    } catch {
      setCopyStatus("Copy failed");
      window.setTimeout(() => setCopyStatus(""), 1800);
    }
  }

  function downloadShoppingList() {
    if (!shoppingListText) return;
    const blob = new Blob([shoppingListText], { type: "text/plain;charset=utf-8" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `${slugify(recipe.dish)}-shopping-list.txt`;
    link.click();
    URL.revokeObjectURL(link.href);
  }
}

function buildShoppingListText(recipe, scaleMultiplier) {
  if (!recipe) return "";
  const lines = recipe.ingredients.map(
    (ingredient) => `- ${scaleIngredient(ingredient, scaleMultiplier)}`,
  );
  return [`Shopping list for ${recipe.dish}`, "", ...lines].join("\n");
}

function scaleIngredient(ingredient, multiplier) {
  if (!Number.isFinite(multiplier) || multiplier === 1) return ingredient;
  const rangeMatch = ingredient.match(/^(\d+(?:\.\d+)?|\d+\s+\d+\/\d+|\d+\/\d+)\s*-\s*(\d+(?:\.\d+)?|\d+\s+\d+\/\d+|\d+\/\d+)\b/);
  if (rangeMatch) {
    const scaledStart = formatAmount(parseAmount(rangeMatch[1]) * multiplier);
    const scaledEnd = formatAmount(parseAmount(rangeMatch[2]) * multiplier);
    return `${scaledStart}-${scaledEnd}${ingredient.slice(rangeMatch[0].length)}`;
  }

  const amountMatch = ingredient.match(/^(\d+\s+\d+\/\d+|\d+\/\d+|\d+(?:\.\d+)?)\b/);
  if (!amountMatch) return ingredient;

  const scaled = formatAmount(parseAmount(amountMatch[1]) * multiplier);
  return `${scaled}${ingredient.slice(amountMatch[0].length)}`;
}

function parseAmount(value) {
  const parts = value.trim().split(/\s+/);
  if (parts.length === 2) {
    return Number.parseFloat(parts[0]) + parseFraction(parts[1]);
  }
  if (value.includes("/")) {
    return parseFraction(value);
  }
  return Number.parseFloat(value);
}

function parseFraction(value) {
  const [numerator, denominator] = value.split("/").map(Number);
  return denominator ? numerator / denominator : 0;
}

function formatAmount(value) {
  if (!Number.isFinite(value)) return "";
  const rounded = Math.round(value * 8) / 8;
  const whole = Math.floor(rounded);
  const fraction = rounded - whole;
  const fractionText = formatFraction(fraction);
  if (!fractionText) return String(whole);
  return whole ? `${whole} ${fractionText}` : fractionText;
}

function formatFraction(value) {
  const eighths = Math.round(value * 8);
  const fractions = {
    1: "1/8",
    2: "1/4",
    3: "3/8",
    4: "1/2",
    5: "5/8",
    6: "3/4",
    7: "7/8",
  };
  return fractions[eighths] || "";
}

function slugify(value) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "");
}
