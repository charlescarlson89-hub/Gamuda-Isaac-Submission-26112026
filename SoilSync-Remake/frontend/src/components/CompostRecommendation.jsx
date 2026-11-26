import React from "react";
import { Link } from "react-router-dom";

export default function CompostRecommendation({ result, methods, options, selectedRecipe, hasExcludedWaste }) {
  const recommendation = result?.recommendation;
  const choices = recommendation ? [recommendation, ...(recommendation.alternatives || [])] : [];
  const mix = selectedRecipe == null
    ? recommendation
    : choices.find((choice) => choice.recipeId === selectedRecipe);
  return (
    <section className="panel suggested-mix" aria-live="polite" aria-busy={!result}>
      <h2>
        {mix && mix !== recommendation ? "Other suitable compost method" : "Compost recommendation"}
      </h2>
      {!result && <p>Matching your scraps to the recipe library…</p>}
      {result?.error && <p>{result.error}</p>}
      {result && !result.error && !recommendation && <p>No recipe matches all the identified food scraps.</p>}
      {recommendation && hasExcludedWaste && <p>Keep rejected and unidentified items out of the mix.</p>}
      {result && !result.error && methods.length > 0 && (
        <nav className="mix-alternatives" aria-label="Compost method options">
          {methods.map((method) => {
            const matches = choices.some((choice) => choice.recipeId === method.id);
            const selectable = options.some((option) => option.id === method.id);
            const status = matches
              ? hasExcludedWaste ? "Matches accepted scraps" : "Matches this scan"
              : "No match for this scan";
            return (
              <div className="mix-method-status" key={method.id}>
                <span className="mix-method-mark" aria-hidden="true">{matches ? "✅" : "❌"}</span>
                <span>
                  {selectable
                    ? <Link to={`/fertilizer?recipe=${method.id}`} aria-current={selectedRecipe === method.id ? "true" : undefined}>
                        {method.name}
                      </Link>
                    : method.name}
                  <small className="mix-ingredient-match">{status}</small>
                </span>
              </div>
            );
          })}
        </nav>
      )}
      {mix && (
        <>
          <h3>{mix.recipeName} {mix === recommendation && <span className="mix-best">Best match</span>}</h3>
          <p>{mix.templateName}</p>
          {mix.templateSource && <p className="mix-ingredient-match">{mix.templateSource}</p>}
          <p>Suggested ingredient proportions</p>
          <ul>
            {mix.ingredients.map((ingredient) => (
              <li key={ingredient.id}>
                <span>
                  {ingredient.name}
                  <small className="mix-ingredient-match">
                    {ingredient.matched ? "Matches your scan" : "Add to match this recipe"}
                  </small>
                </span>
                <strong>{ingredient.percentage}%</strong>
              </li>
            ))}
          </ul>
          {selectedRecipe !== mix.recipeId && (
            <Link className="button button-secondary" to={`/fertilizer?recipe=${mix.recipeId}`}>
              Open compost guide
            </Link>
          )}
        </>
      )}
    </section>
  );
}
