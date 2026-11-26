import React, { useEffect, useRef, useState } from "react";
import { Capacitor } from "@capacitor/core";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Camera,
  ChevronDown,
  CircleHelp,
  ImagePlus,
  Leaf,
  LoaderCircle,
  RotateCcw,
  ScanLine,
  X,
} from "lucide-react";
import { useSoilSync } from "../state";
import usePhoto from "../components/usePhoto";
import CameraStage from "../components/CameraStage";
import CompostRecommendation from "../components/CompostRecommendation";
import { approvedRecipes } from "../data/compostGuides";
import { availableCompostMethods } from "../model";
import { useCompostMatch } from "../services/compostMatch";

export function Classification({ compact = false, result: provided }) {
  const { state } = useSoilSync();
  const result = provided || state.scan;
  return (
    <section
      className={`classification-card ${compact ? "classification-compact" : ""}`}
    >
      <div className="classification-heading">
        <ScanLine size={23} strokeWidth={1.5} />
        <h2>
          {compact ? "Material" : "AI Waste"}
          <br />
          Classification
        </h2>
        {result && (
          <span className="analysis-points">
            {compact
              ? `${result.items.length} material${result.items.length === 1 ? "" : "s"} detected`
              : result.pointsEarned
                ? `+${result.pointsEarned} PTS Earned`
                : "No points earned"}
          </span>
        )}
      </div>
      {(!compact || !result) && (
        <p>
          {result
            ? "Scanned materials matched to the SoilSync waste catalogue."
            : "Scan your scraps to see matched materials and recipes."}
        </p>
      )}
      <div className="ingredient-list">
        {result?.items.map((item, index) => {
          const identified = item.waste_type_id != null;
          const supported = identified && item.is_supported === true;
          const outcome = supported ? "supported" : identified ? "rejected" : "unknown";
          return (
            <div
              className="ingredient-row"
              key={`${item.waste_type_id}-${index}`}
            >
              <span className={`ingredient-icon ingredient-icon-${outcome}`} aria-hidden="true">
                {supported ? <Leaf size={18} strokeWidth={1.3} /> : identified ? <X size={18} /> : <CircleHelp size={18} />}
              </span>
              <div>
                <h3>
                  {item.name}{" "}
                  <span className="material-category">{item.category}</span>
                </h3>
                <span className={`material-outcome material-outcome-${outcome}`}>
                  <span aria-hidden="true">{supported ? "✅" : "❌"}</span>
                  {supported
                    ? item.category === "Small Animal Scraps" ? "Sealed fermentation only" : "Compostable"
                    : identified ? "Rejected" : "Not identified"}
                </span>
                {!compact && supported && item.description && (
                  <small className="material-guidance">{item.description}</small>
                )}
                {!supported && (
                  <small className="material-guidance">
                    {identified
                      ? item.guide_recommendation || item.rejection_reason || "Keep this material out of your compost."
                      : "Retake a clearer photo. Keep unidentified items out of compost."}
                  </small>
                )}
              </div>
              <strong className="confidence-score">
                {Math.round(item.confidence * 100)}%
              </strong>
            </div>
          );
        })}
      </div>
      <small className="classification-disclaimer">
        Identification confidence, not nutrient composition.
      </small>
    </section>
  );
}

export default function Scan() {
  const location = useLocation();
  const camera = usePhoto({
    autoStart: Capacitor.isNativePlatform() || location.state?.openCamera === true,
  });
  const { state, scanPhoto, busy } = useSoilSync();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const compostMatch = useCompostMatch(result?.id);
  const methods = approvedRecipes(state.catalog.fertilizers);
  const recipeOptions = availableCompostMethods(methods, compostMatch);
  const [expanded, setExpanded] = useState(false);
  const started = useRef(null);
  const gesture = useRef(null);
  const rejected = result?.items.filter((item) => !item.is_supported) || [];
  useEffect(() => {
    if (!camera.file || started.current === camera.file) return;
    started.current = camera.file;
    setError("");
    setResult(null);
    scanPhoto(camera.file)
      .then((next) => {
        if (next) setResult(next);
      })
      .catch((err) => setError(err.message));
  }, [camera.file, scanPhoto]);
  async function retry() {
    setError("");
    try {
      const next = await scanPhoto(camera.file);
      if (next) setResult(next);
    } catch (err) {
      setError(err.message);
    }
  }
  function retake() {
    setResult(null);
    setError("");
    setExpanded(false);
    started.current = null;
    camera.setPhoto("");
    void camera.start();
  }
  return (
    <div
      className={`scan-page final-scan ${expanded ? "details-expanded" : ""}`}
    >
      {camera.fileInput}
      {!camera.photo ? (
        <CameraStage camera={camera} onClose={() => navigate("/home")} />
      ) : (
        <>
          <section className="story-photo" aria-label="Captured waste photo">
            <img src={camera.photo} alt="Your captured waste" />
            <div className="photo-shade" />
            <div className="photo-toolbar">
              <span>
                <Leaf size={12} />{" "}
                {busy
                  ? "Analysing materials…"
                  : result
                    ? "Materials identified"
                    : "Photo captured"}
              </span>
              <button
                type="button"
                onClick={() => camera.input.current?.click()}
                disabled={busy}
              >
                <ImagePlus size={14} /> Gallery
              </button>
            </div>
            <button
              className="photo-retake"
              type="button"
              onClick={retake}
              disabled={busy}
              aria-label="Retake waste photo"
            >
              <RotateCcw size={18} />
            </button>
          </section>
          <section
            className="scan-story-details"
            aria-label="Waste analysis"
            onPointerDown={(event) => {
              gesture.current = event.clientY;
            }}
            onPointerUp={(event) => {
              if (
                gesture.current !== null &&
                Math.abs(event.clientY - gesture.current) > 45
              )
                setExpanded(event.clientY < gesture.current);
              gesture.current = null;
            }}
          >
            <button
              className="story-handle"
              type="button"
              aria-label={
                expanded ? "Expand captured photo" : "Expand waste details"
              }
              aria-expanded={expanded}
              onClick={() => setExpanded(!expanded)}
            >
              <span />
              <ChevronDown size={16} />
            </button>
            {busy && (
              <div className="analysis-loading" role="status">
                <LoaderCircle className="scan-spinner" size={23} />
                <div>
                  <strong>Identifying your scraps</strong>
                  <p>Matching the waste catalogue with Google AI.</p>
                </div>
              </div>
            )}
            {error && (
              <div className="inline-error" role="alert">
                <p>{error}</p>
                <button className="text-button" onClick={retry} disabled={busy}>
                  Try analysis again
                </button>
              </div>
            )}
            {result && (
              <>
                <Classification result={result} />
                {rejected.length > 0 && (
                  <Link className="button button-secondary" to="/learn">
                    Waste guide for unsupported materials{" "}
                    <ArrowRight size={17} />
                  </Link>
                )}
                {result.id && (
                  <CompostRecommendation
                    result={compostMatch}
                    methods={methods}
                    options={recipeOptions}
                    hasExcludedWaste={rejected.length > 0}
                  />
                )}
                {!result.items.some((item) => item.waste_type_id) && (
                  <p className="concept-note">
                    No catalogue material identified. Retake a clear photo in
                    good light.
                  </p>
                )}
              </>
            )}
            {!busy && !result && !error && (
              <button type="button" className="button" onClick={retry}>
                <Camera size={18} />
                Identify waste
              </button>
            )}
          </section>
        </>
      )}
    </div>
  );
}
