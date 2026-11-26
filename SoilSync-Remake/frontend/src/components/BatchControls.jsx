import React, { useState } from "react";
import { Plus, Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { batchProgress } from "../model";
import { useSoilSync } from "../state";
import { Dialog } from "./UI";
import { approvedRecipes } from "../data/compostGuides";

export function NewBatchButton({
  className = "small-button",
  children = "New batch",
  fertilizerTypeId,
}) {
  const { state, act, setNotice, busy } = useSoilSync();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [recipeId, setRecipeId] = useState("");
  const navigate = useNavigate();
  const recipes = approvedRecipes(state.catalog.fertilizers);
  return (
    <>
      <button
        type="button"
        className={className}
        disabled={busy || !recipes.length}
        onClick={() => {
          setName(`Compost batch ${state.batches.length + 1}`);
          setRecipeId(
            String(fertilizerTypeId || recipes[0]?.id || ""),
          );
          setOpen(true);
        }}
      >
        <Plus size={20} aria-hidden="true" /> {children}
      </button>
      {open && (
        <Dialog title="Start a compost batch" onClose={() => setOpen(false)}>
          <p>
            Give each batch its own name. Check-ins and progress are tracked
            separately.
          </p>
          <form
            onSubmit={async (event) => {
              event.preventDefault();
              const id = crypto.randomUUID();
              const created = await act({
                type: "START_BATCH",
                id,
                name,
                fertilizerTypeId: recipeId,
              });
              if (created) {
                setOpen(false);
                setNotice(`${name.trim()} started.`);
                navigate(`/batch?batch=${encodeURIComponent(created.id)}`);
              }
            }}
          >
            <label htmlFor="new-batch-name">Batch name</label>
            <input
              id="new-batch-name"
              value={name}
              maxLength={60}
              required
              onChange={(event) => setName(event.target.value)}
            />
            <label htmlFor="new-batch-recipe">Compost recipe</label>
            <select
              id="new-batch-recipe"
              value={recipeId}
              required
              onChange={(event) => setRecipeId(event.target.value)}
            >
              {recipes.map((recipe) => (
                <option key={recipe.id} value={recipe.id}>
                  {recipe.name}
                </option>
              ))}
            </select>
            <button type="submit" className="button" disabled={busy}>
              {busy ? "Starting…" : "Start batch"}
            </button>
          </form>
        </Dialog>
      )}
    </>
  );
}

export function DeleteCompletedBatch({ batch, onDeleted }) {
  const { act, setNotice, busy } = useSoilSync();
  const [confirm, setConfirm] = useState(false);
  if (batchProgress(batch) < 100) return null;
  return (
    <>
      <button
        type="button"
        className="icon-button batch-delete"
        disabled={busy}
        aria-label={`Delete completed batch ${batch.name}`}
        onClick={() => setConfirm(true)}
      >
        <Trash2 size={20} aria-hidden="true" />
      </button>
      {confirm && (
        <Dialog
          title="Delete completed batch?"
          onClose={() => setConfirm(false)}
        >
          <p>
            This removes <strong>{batch.name}</strong> and its three check-in
            notes and photos from your account. Your other batches and EcoPoints
            stay as they are.
          </p>
          <button
            className="button button-danger"
            disabled={busy}
            onClick={async () => {
              if (await act({ type: "DELETE_BATCH", batchId: batch.id })) {
                setConfirm(false);
                setNotice("Completed batch deleted.");
                onDeleted?.();
              }
            }}
          >
            Delete batch
          </button>
          <button
            className="text-button cancel-button"
            onClick={() => setConfirm(false)}
          >
            Keep batch
          </button>
        </Dialog>
      )}
    </>
  );
}
