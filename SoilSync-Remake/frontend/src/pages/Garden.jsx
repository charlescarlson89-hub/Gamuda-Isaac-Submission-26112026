import React, { useRef, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  ArrowRight,
  CalendarDays,
  Check,
  ChevronDown,
  ClipboardCheck,
  Droplets,
  Eye,
  FlaskConical,
  Leaf,
  LockKeyhole,
  Sprout,
  Thermometer,
  TriangleAlert,
} from "lucide-react";
import { useSoilSync } from "../state";
import { Badge, Dialog, FIcon, Heading, PreviewNote } from "../components/UI";
import { Classification } from "./Scan";
import PrivatePhoto from "../components/PrivatePhoto";
import {
  DeleteCompletedBatch,
  NewBatchButton,
} from "../components/BatchControls";
import { availableCompostMethods, batchProgress, selectedBatch } from "../model";
import { approvedRecipes, compostGuideImages, compostMethodDetails } from "../data/compostGuides";
import CompostRecommendation from "../components/CompostRecommendation";
import { useCompostMatch } from "../services/compostMatch";
import { compostPlantPhoto } from "../data/compostPlantPhotos";

function PlantCarousel({ children }) {
  const gesture = useRef(null);
  const suppressClick = useRef(false);
  function finish(event) {
    gesture.current = null;
    delete event.currentTarget.dataset.dragging;
    if (event.currentTarget.hasPointerCapture(event.pointerId))
      event.currentTarget.releasePointerCapture(event.pointerId);
    // A drag must not open the plant card when the mouse is released.
    setTimeout(() => { suppressClick.current = false; }, 0);
  }
  return (
    <div
      className="plant-carousel"
      role="region"
      aria-label="Garden inspiration"
      onPointerDown={(event) => {
        suppressClick.current = false;
        // Touch scrolling keeps the browser's native swipe and momentum.
        if (event.pointerType !== "mouse" || event.button !== 0) return;
        gesture.current = { x: event.clientX, scroll: event.currentTarget.scrollLeft };
      }}
      onPointerMove={(event) => {
        if (!gesture.current) return;
        const distance = event.clientX - gesture.current.x;
        if (!suppressClick.current && Math.abs(distance) < 6) return;
        suppressClick.current = true;
        event.currentTarget.dataset.dragging = "true";
        event.currentTarget.setPointerCapture(event.pointerId);
        event.preventDefault();
        event.currentTarget.scrollLeft = gesture.current.scroll - distance;
      }}
      onPointerUp={finish}
      onPointerCancel={finish}
      onLostPointerCapture={finish}
      onPointerLeave={(event) => {
        if (!event.currentTarget.hasPointerCapture(event.pointerId)) gesture.current = null;
      }}
      onClickCapture={(event) => {
        if (!suppressClick.current) return;
        event.preventDefault();
        event.stopPropagation();
      }}
    >
      {children}
    </div>
  );
}

export function Fertilizer() {
  const [plant, setPlant] = useState(null);
  const [params, setParams] = useSearchParams();
  const { state } = useSoilSync();
  const match = useCompostMatch(state.scan?.id);
  const methods = approvedRecipes(state.catalog.fertilizers);
  const recipes = availableCompostMethods(methods, match);
  const recipeId =
    params.get("recipe") || match?.recommendation?.recipeId || state.scan?.fertilizer_ids?.[0] || recipes[0]?.id;
  const recipe = recipes.find((row) => String(row.id) === String(recipeId)) || recipes[0];
  if (!recipe)
    return (
      <div className="page-stack">
        <section className="empty-card">
          <h1>Composting guides are being updated</h1>
          <p>Hot, Cold and Bokashi Composting will appear when the latest catalogue is available.</p>
          <Link className="button" to="/scan">
            Scan your scraps
          </Link>
        </section>
      </div>
    );
  const recommended = recipe.plants.filter((item) => item.recommended);
  const avoid = recipe.plants.filter((item) => !item.recommended);
  const selectedPlantPhoto = plant && compostPlantPhoto(plant.name);
  const phases = recipe.stages || [];
  const methodDetails = compostMethodDetails[recipe.method];
  return (
    <div className="page-stack fertilizer-page">
      <div className="page-heading">
        <h1>Make Fertilizer</h1>
      </div>
      <div className="pipeline-label">
        <strong>
          <Sprout size={18} /> YOUR COMPOSTING JOURNEY
        </strong>
        <Badge>HOME RECIPE</Badge>
      </div>
      <Classification compact />
      {state.scan?.id && (
        <CompostRecommendation
          result={match}
          methods={methods}
          options={recipes}
          selectedRecipe={recipe.id}
          hasExcludedWaste={state.scan.items?.some((item) => !item.is_supported)}
        />
      )}
      <section className="panel recipe-selector">
        <label htmlFor="compost-recipe">Choose a compost recipe</label>
        <select
          id="compost-recipe"
          value={recipe.id}
          disabled={Boolean(state.scan?.id && !match)}
          onChange={(event) => setParams({ recipe: event.target.value })}
        >
          {recipes.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <h2>{recipe.name}</h2>
        <p>{recipe.description}</p>
        <small>
          {recipe.timeline || `Planning estimate: ${recipe.estimatedDays} days. Actual maturity varies.`}
        </small>
      </section>
      {(recipe.suitableWaste?.length || methodDetails) && <section className="panel recipe-materials">
        <Heading icon={Leaf} title="What goes in" />
        <dl>
          <dt>Use</dt>
          <dd>{recipe.suitableWaste?.join(", ") || methodDetails?.use}</dd>
          <dt>Keep out</dt>
          <dd>{recipe.excludedWaste?.join(", ") || methodDetails?.avoid}</dd>
        </dl>
      </section>}
      <section className="panel plants-panel">
        <Heading icon={Sprout} title="Suitable Plants" />
        <p>
          General garden inspiration. Check plant, soil and drainage needs
          before applying mature compost.
        </p>
        <PlantCarousel>
          {recommended.map((item) => {
            const photo = compostPlantPhoto(item.name);
            return (
              <article key={item.id}>
                {photo ? (
                  <img
                    src={photo.src}
                    alt={photo.alt}
                    draggable={false}
                    loading="lazy"
                  />
                ) : (
                  <div className="plant-placeholder" aria-hidden="true">
                    <Sprout size={35} />
                  </div>
                )}
                <button
                  type="button"
                  className="plant-name-button"
                  onClick={() => setPlant(item)}
                >
                  <strong>{item.name}</strong>
                </button>
                <small>{item.type}</small>
              </article>
            );
          })}
        </PlantCarousel>
        {!recipe.suitableWaste && methodDetails && <p className="local-plant-examples">
          <strong>Malaysian garden examples.</strong> {methodDetails.gardenExamples}
        </p>}
      </section>
      <section className="panel caution-panel">
        <Heading icon={TriangleAlert} title="Avoid Plants" />
        <p>
          Fresh scraps and unfinished compost can damage roots. Specialist
          plants need their own growing-medium guidance.
        </p>
        <div className="caution-tags">
          {avoid.map((item) => (
            <span key={item.id}>{item.name}</span>
          ))}
          <span>Unfinished compost</span>
          <span>Fresh scraps on roots</span>
        </div>
      </section>
      {phases.length > 0 && <section className="panel recipe-panel">
        <Heading
          icon={FlaskConical}
          title="Step to Do Fertilizer"
          aside={`${phases.length} stages`}
        />
        <p className="recipe-method-intro">{recipe.description}</p>
        <p className="step-guide-hint">Tap a step to see its image guide.</p>
        {phases.map((phase, index) => {
          const image = compostGuideImages[phase.imageKey];
          const tip = methodDetails?.stageTips[phase.imageKey];
          return (
            <details className="recipe-stage" key={`${recipe.id}-${index}`}>
              <summary>
                <span className="recipe-stage-number" aria-hidden="true">{index + 1}</span>
                <span className="recipe-stage-title">Step {index + 1}: {phase.title}</span>
                <ChevronDown className="recipe-stage-chevron" size={20} aria-hidden="true" />
              </summary>
              <div className="recipe-stage-content">
                {image?.position && (
                  <div
                    className="recipe-stage-illustration"
                    role="img"
                    aria-label={image.alt}
                    style={{ backgroundImage: `url(${image.src})`, backgroundPosition: image.position }}
                  />
                )}
                {image && !image.position && (
                  <img src={image.src} alt={image.alt} width="600" height="320" loading="lazy" />
                )}
                {phase.steps.map((step) => <p key={step.number}>{step.instruction}</p>)}
                {tip && <p>{tip}</p>}
              </div>
            </details>
          );
        })}
        {(recipe.guideCredit || recipe.sources?.length > 0) && (
          <div className="recipe-sources">
            <span>Guide sources:</span>
            {recipe.guideCredit && <span>{recipe.guideCredit}</span>}
            {recipe.sources?.map((source) => (
              <a key={source.url} href={source.url} target="_blank" rel="noopener noreferrer">{source.label} ↗</a>
            ))}
          </div>
        )}
      </section>}
      {recipe.maintenance && (
        <details className="panel monitoring-panel">
          <summary>Care & maintenance</summary>
          <Heading icon={Leaf} title="How to Monitor" />
          <div>
            <CalendarDays size={24} />
            <p>{recipe.maintenance.cadence}</p>
          </div>
          <div>
            <Thermometer size={24} />
            <p>{recipe.maintenance.temperature}</p>
          </div>
          <div>
            <Droplets size={24} />
            <p>{recipe.maintenance.moisture}</p>
          </div>
        </details>
      )}
      <NewBatchButton className="button" fertilizerTypeId={recipe.id}>
        Start this recipe batch
      </NewBatchButton>
      {plant && (
        <Dialog title={plant.name} onClose={() => setPlant(null)}>
          <p>{plant.notes}</p>
          {selectedPlantPhoto?.credit && (
            <p className="preview-note">
              Photo by <a href={selectedPlantPhoto.source} target="_blank" rel="noreferrer">{selectedPlantPhoto.credit}</a>
              {" · "}<a href={selectedPlantPhoto.licenseUrl} target="_blank" rel="noreferrer">{selectedPlantPhoto.license}</a>
              {" · " }Cropped to fit the card
            </p>
          )}
          <p className="preview-note">
            This guide does not measure your soil or nutrients.
          </p>
        </Dialog>
      )}
      <PreviewNote>
        Your check-ins track a routine. They do not measure nutrients or prove
        compost maturity.
      </PreviewNote>
    </div>
  );
}

export function Batch() {
  const { state } = useSoilSync();
  const [view, setView] = useState(null);
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const batch = selectedBatch(state, params.get("batch"));
  if (!batch)
    return (
      <div className="page-stack">
        <section className="empty-card">
          <Sprout size={42} />
          <h1>
            {params.has("batch")
              ? "Batch not found"
              : "A fresh start for your scraps"}
          </h1>
          <p>
            Start a batch from the home compost guide. Your weekly check-ins
            will live here.
          </p>
          <Link className="button" to="/fertilizer">
            Explore the recipe <ArrowRight size={21} />
          </Link>
          <Link className="quiet-link" to="/home">
            Back to my batches
          </Link>
        </section>
      </div>
    );
  const count = batch.checkins.length;
  const quests = batch.quests;
  const active = quests.find((quest) => quest.status === "CURRENT");
  const openQuestCount = quests.filter((quest) => quest.status === "CURRENT" && quest.canClaim !== false).length;
  const complete = count === quests.length;
  const progress = batchProgress(batch);
  const checkinPath = `/batch/check-in?batch=${encodeURIComponent(batch.id)}`;
  return (
    <div className="page-stack batch-page">
      <div className="batch-switcher">
        <div>
          <label htmlFor="selected-batch">Your compost batches</label>
          <select
            id="selected-batch"
            value={batch.id}
            onChange={(event) => {
              setView(null);
              setParams({ batch: event.target.value });
            }}
          >
            {state.batches.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </div>
        <NewBatchButton />
      </div>
      <div className="pipeline-label">
        <strong>
          <Sprout size={18} /> COMPOSTING PROGRESS
        </strong>
        <Badge>{batch.number}</Badge>
      </div>
      <section className="batch-status-card">
        <div className="row-between">
          <h1>
            <Leaf size={23} /> Active Batch Status
          </h1>
          <DeleteCompletedBatch
            batch={batch}
            onDeleted={() => navigate("/home")}
          />
        </div>
        <Badge dark>
          {complete ? "COMPLETED" : batch.status.toUpperCase()}
        </Badge>
        <p>{batch.name}</p>
        <div className="batch-progress">
          <div
            className="progress-ring"
            style={{ "--progress": `${progress}%` }}
            role="img"
            aria-label={`${progress}% of weekly check-ins recorded`}
          >
            <div>
              <strong>{progress}%</strong>
              <small>CHECK-INS</small>
            </div>
          </div>
        </div>
        <div className="batch-status-meta">
          <div className="row-between">
            <span>
              Type:{" "}
              {state.catalog.fertilizers.find(
                (recipe) => recipe.id === batch.fertilizerTypeId,
              )?.name || batch.fertilizerName || "Home compost"}
            </span>
            <strong>{count}/{quests.length} check-ins</strong>
          </div>
          <progress
            value={count}
            max={quests.length}
            aria-label="Recorded weekly check-ins"
          />
          <p>Progress reflects check-ins, not measured fermentation.</p>
        </div>
      </section>
      <Heading
        icon={CalendarDays}
        title="Check In Stages"
        aside={complete ? "ALL RECORDED" : openQuestCount > 1 ? `${openQuestCount} AVAILABLE` : `WEEK ${active?.week ?? count + 1}`}
      />
      <div className="weekly-stages">
        {quests.map((quest) => {
          const { week, availableOn, canClaim } = quest;
          const done = quest.status === "DONE";
          const current = quest.status === "CURRENT";
          return (
            <div
              className={`weekly-stage ${current ? "current" : ""}`}
              key={week}
            >
              <span className="week-symbol">
                {done ? (
                  <Check size={22} />
                ) : current ? (
                  <FlaskConical size={22} />
                ) : (
                  <LockKeyhole size={21} />
                )}
              </span>
              <strong>Week {week}</strong>
              <Badge>{done ? "DONE" : (current && canClaim !== false) ? "CURRENT" : availableOn || "UPCOMING"}</Badge>
              {done ? (
                <button
                  className="icon-button"
                  aria-label={`View week ${week} log`}
                  onClick={() => setView(batch.checkins.find((checkin) => checkin.week === week))}
                >
                  <Eye size={21} />
                </button>
              ) : current && canClaim !== false ? (
                <Link
                  to={`${checkinPath}&week=${week}`}
                  className="icon-button week-go"
                  aria-label={`Open week ${week} check-in`}
                >
                  <ArrowRight size={23} />
                </Link>
              ) : (
                <LockKeyhole size={17} className="week-lock" />
              )}
            </div>
          );
        })}
      </div>
      {active && active.canClaim !== false && (
        <Link className="button" to={checkinPath}>
          <ClipboardCheck size={21} /> Perform weekly check-in
        </Link>
      )}
      {active?.canClaim === false && <PreviewNote>Week {active.week} opens on {active.availableOn}.</PreviewNote>}
      {complete && (
        <section className="panel">
          <h2>A little care goes a long way</h2>
          <p>
            All scheduled check-ins are recorded. Continue observing the batch and
            check compost maturity before use.
          </p>
        </section>
      )}
      <PreviewNote>
        Check-in photos, dates and notes are saved to your account. Completing a
        quest does not prove compost maturity.
      </PreviewNote>
      {view && (
        <Dialog
          title={`Week ${view.week} check-in`}
          onClose={() => setView(null)}
        >
          <p>
            Recorded{" "}
            {new Date(view.at).toLocaleString("en-MY", {
              dateStyle: "medium",
              timeStyle: "short",
            })}
          </p>
          <p>{view.note || "A little check-in for a greener routine."}</p>
          <p>
            {view.verification?.status === "approved"
              ? "Visible compost check passed."
              : view.verification?.status === "recorded"
                ? "Photo saved without AI review."
                : "Earlier or sample record · no AI compost check recorded."}
          </p>
          {view.photoUrl && (
            <PrivatePhoto
              className="saved-checkin-photo"
              path={view.photoUrl}
              alt={`Week ${view.week} compost observation`}
            />
          )}
          <p className="preview-note">
            This photo is private to your account. It records an observation,
            not verified compost maturity.
          </p>
        </Dialog>
      )}
    </div>
  );
}

const wasteItems = [
  {
    tag: "EXCLUDE FROM BATCH",
    kind: "STRONG COMPOUNDS",
    title: "Alternative Eco-Friendly Processing Options",
    text: "Keep treated or chemically contaminated materials out of compost. Ask your local authority about suitable disposal options.",
    icon: 4,
  },
  {
    tag: "DO NOT COMPOST",
    kind: "LIPID / PROTEIN",
    title: "Community & Municipal Drop-Offs",
    text: "Meat, fish and dairy can attract pests in a beginner home compost bin. Use an approved local food-waste collection service where available.",
    icon: 5,
  },
  {
    tag: "NON-BIODEGRADABLE",
    kind: "SYNTHETIC PLASTIC",
    title: "Proper General Waste Disposal",
    text: "Remove plastics and packaging. Follow local recycling or general-waste guidance; do not mix packaging into food scraps.",
    icon: 6,
  },
  {
    tag: "EXCLUDE FROM BATCH",
    kind: "CHEMICAL RESIDUE",
    title: "Prevention: Reducing “Unusable” Waste",
    text: "Plan meals, store food well and use edible ingredients first. Separate scraps from cleaning products and other household chemicals.",
    icon: 7,
  },
];
export function WasteGuide() {
  const [params] = useSearchParams();
  const [open, setOpen] = useState(null);
  const query = (params.get("q") || "").trim();
  return (
    <div className="page-stack waste-page">
      <div className="page-heading">
        <h1>Waste Guide</h1>
      </div>
      {query && (
        <p className="search-context">
          Guidance for “{query}”. Choose the closest material below.
        </p>
      )}
      {wasteItems.map((item, index) => (
        <section
          className={`waste-accordion ${open === index ? "expanded" : ""}`}
          key={item.title}
        >
          <button
            aria-expanded={open === index}
            aria-controls={`waste-answer-${index}`}
            onClick={() => setOpen(open === index ? null : index)}
          >
            <div>
              <div className="waste-category">
                <Badge>{item.tag}</Badge>
                <small>{item.kind}</small>
              </div>
              <h2>{item.title}</h2>
            </div>
            <span className="waste-glyph">
              <FIcon page="waste" index={item.icon} />
            </span>
            <ChevronDown className="accordion-chevron" size={20} />
          </button>
          <div id={`waste-answer-${index}`} hidden={open !== index}>
            <p>{item.text}</p>
          </div>
        </section>
      ))}
      <Link className="button button-secondary" to="/scan">
        <FIcon page="waste" index={0} /> Re-scan scraps
      </Link>
    </div>
  );
}
