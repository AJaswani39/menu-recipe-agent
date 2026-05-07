export function RecipePanel({ recipe }) {
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
          </div>
          <div>
            <h3>Ingredients</h3>
            <ul>
              {recipe.ingredients.map((ingredient) => (
                <li key={ingredient}>{ingredient}</li>
              ))}
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
}
