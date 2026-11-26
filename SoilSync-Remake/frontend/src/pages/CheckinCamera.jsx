import React, { useState } from "react";
import { Capacitor } from "@capacitor/core";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { ArrowRight, RotateCcw } from "lucide-react";
import { useSoilSync } from "../state";
import usePhoto from "../components/usePhoto";
import CameraStage from "../components/CameraStage";
import { selectedBatch } from "../model";

export default function CheckinCamera() {
  const { state, act, setNotice, busy } = useSoilSync();
  const camera = usePhoto({ autoStart: Capacitor.isNativePlatform() });
  const [note, setNote] = useState("");
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const batch = selectedBatch(state, params.get("batch"));
  if (!batch) return <Navigate to="/home" replace />;
  const path = `/batch?batch=${encodeURIComponent(batch.id)}`;
  const requestedWeek = params.get("week");
  const quest = batch.quests.find((item) =>
    item.status === "CURRENT" && item.canClaim !== false
    && (requestedWeek === null || String(item.week) === requestedWeek),
  );
  if (!quest) return <Navigate to={path} replace />;
  const { week, imageOnly } = quest;
  const riceWater = batch.fertilizerTypeId === 8;
  let photoHint = "CENTER YOUR COMPOST SURFACE";
  let photoInstructions = "Show the compost contents clearly. Approval earns 100 EcoPoints.";
  if (riceWater) {
    photoHint = "SHOW YOUR STARTER OR COMPOST";
    photoInstructions = "Show the cloudy starter and its container clearly, or show the composting scraps. Approval earns 100 EcoPoints.";
    if (week === 1) {
      photoInstructions = "Photograph the layered starter through the side of the jar, or show the cloudy liquid in its tub. Approval earns 100 EcoPoints.";
    } else if ([2, 3, 4].includes(week)) {
      photoHint = "SHOW THE COLLECTED FOOD SCRAPS";
      photoInstructions = "Show a collection of food scraps, such as fruit peels, rinds, or vegetable trimmings. A photo of the starter alone does not count. Approval earns 100 EcoPoints.";
    }
  }
  async function verify() {
    const completed = await act({
      type: "BATCH_CHECKIN",
      batchId: batch.id,
      week,
      note,
      photo: camera.file,
    });
    if (completed) {
      setNotice(
        `Week ${week} check-in saved. ${completed.pointsAwarded ? "+100 EcoPoints!" : "Already recorded."}`,
      );
      navigate(path);
    }
  }
  return (
    <div className="weekly-camera-page final-weekly-camera">
      {camera.fileInput}
      {!camera.photo ? (
        <CameraStage
          camera={camera}
          title={`WEEK ${week} CHECK-IN`}
          hint={imageOnly ? "TAKE OR CHOOSE A PHOTO" : photoHint}
          analysePhoto={!imageOnly}
          onClose={() => navigate(path)}
        />
      ) : (
        <div className="weekly-review">
          <img src={camera.photo} alt="Your weekly compost proof" />
          <div className="checkin-details">
            <span className="badge">WEEK {week} CHECK-IN</span>
            <h1>{batch.name}</h1>
            <p>{imageOnly ? "Take or choose any photo for this check-in. Saving earns 100 EcoPoints." : photoInstructions}</p>
            {!imageOnly && [6, 8].includes(batch.fertilizerTypeId) && (
              <p className="concept-note">Take a photo when your process calls for opening the container. Keep it closed during sealed fermentation.</p>
            )}
            <label htmlFor="weekly-note">
              Observation <small>(optional)</small>
            </label>
            <textarea
              id="weekly-note"
              rows={3}
              maxLength={250}
              placeholder="Colour, smell, moisture…"
              value={note}
              onChange={(event) => setNote(event.target.value)}
            />
            <button
              type="button"
              className="button"
              disabled={busy}
              onClick={verify}
            >
              {imageOnly
                ? (busy ? "Saving photo…" : "Save weekly check-in")
                : (busy ? "Checking compost…" : "Verify weekly check-in")}
              <ArrowRight size={18} />
            </button>
            <button
              type="button"
              className="text-button"
              disabled={busy}
              onClick={() => {
                camera.setPhoto("");
                void camera.start();
              }}
            >
              <RotateCcw size={16} />
              Retake photo
            </button>
            {imageOnly ? <p className="concept-note">Your photo is saved privately and skips AI review.</p> : <p className="concept-note">
              Verification sends this photo to Google AI. Approved proof is
              saved privately. A visual check does not certify compost maturity.
            </p>}
          </div>
        </div>
      )}
    </div>
  );
}
