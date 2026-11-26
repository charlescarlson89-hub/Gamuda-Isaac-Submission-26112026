import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  Check,
  Leaf,
  LockKeyhole,
  Plus,
  Settings2,
} from "lucide-react";
import { useSoilSync } from "../state";
import { batchProgress, localDay } from "../model";
import {
  DeleteCompletedBatch,
  NewBatchButton,
} from "../components/BatchControls";
import DailyTipBoard from "../components/DailyTipBoard";

function daysOfWeek() {
  const date = new Date(`${localDay()}T12:00:00+08:00`);
  const offset = (date.getUTCDay() + 6) % 7;
  return Array.from({ length: 7 }, (_, index) => ({
    key: localDay(new Date(date.getTime() + (index - offset) * 86400000)),
    label: ["M", "T", "W", "T", "F", "S", "S"][index],
  }));
}

export function DailyCheckin({ reward = false }) {
  const { state, act, setNotice, busy } = useSoilSync();
  const today = localDay();
  return (
    <section
      className={`daily-checkin ${reward ? "daily-reward" : ""}`}
      aria-label="Daily check-in"
    >
      <div className="row-between">
        <strong>{reward ? "Daily check-in" : "Daily Check-in"}</strong>
        <small>
          {reward
            ? "+10 pts today"
            : `${state.profile.streakDays || 0}-Day Streak`}
        </small>
      </div>
      <div className="checkin-week">
        {daysOfWeek().map((day, index) => {
          const done = state.checkins.includes(day.key);
          const current = day.key === today;
          const future = day.key > today;
          const symbol = done ? (
            <Check size={15} />
          ) : future && reward ? (
            <LockKeyhole size={12} />
          ) : current ? (
            <Plus size={15} />
          ) : (
            <i />
          );
          return (
            <div key={day.key}>
              {!reward && <span>{day.label}</span>}
              {current ? (
                <button
                  type="button"
                  className={done ? "day-done" : "day-today"}
                  disabled={done || busy}
                  aria-label={
                    done ? "Checked in today" : "Check in today for 10 points"
                  }
                  onClick={async () => {
                    const result = await act({ type: "CHECKIN" });
                    if (result)
                      setNotice(
                        result.pointsAwarded
                          ? "+10 points. Daily check-in recorded."
                          : "You have already checked in today.",
                      );
                  }}
                >
                  {symbol}
                </button>
              ) : (
                <span className={`day-circle ${done ? "day-done" : ""}`}>
                  {symbol}
                </span>
              )}
              {reward && <span>Day {index + 1}</span>}
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default function Home() {
  const { state } = useSoilSync();
  const [all, setAll] = useState(false);
  const batches = [...state.batches].sort(
    (a, b) =>
      Number(batchProgress(a) === 100) - Number(batchProgress(b) === 100),
  );
  return (
    <div className="page-stack home-page final-home">
      <section className="dashboard-wallet">
        <div className="wallet-greeting">
          <span className="wallet-leaf">
            <Leaf size={24} strokeWidth={1.4} />
          </span>
          <div>
            <small>Welcome back</small>
            <h1>{state.profile.name}</h1>
          </div>
          <Link to="/settings" aria-label="Open settings">
            <Settings2 size={17} />
          </Link>
        </div>
        <Link className="wallet-amount" to="/rewards">
          <strong>{state.balance.toLocaleString()}</strong>
          <span>PTS</span>
        </Link>
        <DailyCheckin />
      </section>
      <section
        className="dashboard-batches"
        aria-label="Weekly composting progress"
      >
        {batches.length ? (
          batches.slice(0, all ? undefined : 1).map((batch) => (
            <article className="dashboard-batch" key={batch.id}>
              <div className="row-between">
                <strong className="eyebrow">
                  <i /> WEEKLY COMPOSTING PROGRESS
                </strong>
                <span className="badge">
                  {batchProgress(batch) === 100
                    ? "Completed"
                    : `Week ${batch.checkins.length + 1} of ${batch.quests?.length || 3}`}
                </span>
                <DeleteCompletedBatch batch={batch} />
              </div>
              <Link
                to={`/batch?batch=${encodeURIComponent(batch.id)}`}
                className="dashboard-batch-link"
              >
                <h2>
                  {batch.number} · {batch.name}
                </h2>
                <p>
                  {state.catalog.fertilizers.find(
                    (recipe) => recipe.id === batch.fertilizerTypeId,
                  )?.name || batch.fertilizerName || "Your composting routine"}
                </p>
                <div className="row-between progress-meta">
                  <span>Check-in Progress</span>
                  <b>{batchProgress(batch)}% recorded</b>
                </div>
                <progress
                  value={batchProgress(batch)}
                  max="100"
                  aria-label={`${batch.name} check-in progress`}
                />
              </Link>
            </article>
          ))
        ) : (
          <article className="dashboard-batch">
            <strong className="eyebrow">
              <i /> WEEKLY COMPOSTING PROGRESS
            </strong>
            <h2>Your next green beginning</h2>
            <p>
              Give food scraps a second life. Start your first compost batch.
            </p>
            <Link to="/fertilizer" className="quiet-link">
              Explore a recipe →
            </Link>
          </article>
        )}
        {(batches.length > 1 || all) && (
          <button
            type="button"
            className="text-button more-batches"
            aria-expanded={all}
            onClick={() => setAll(!all)}
          >
            {all ? "Show less" : `View all ${batches.length} batches`}
          </button>
        )}
        {all && <NewBatchButton />}
      </section>
      <DailyTipBoard />
    </div>
  );
}
