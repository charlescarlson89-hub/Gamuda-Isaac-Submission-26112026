import React, { useEffect, useState } from "react";
import { ArrowRight, Lightbulb } from "lucide-react";
import { dailyCompostTip } from "../data/compostTips";
import { localDay } from "../model";
import LeaffyMascot from "./LeaffyMascot";
import "./LeaffyBoard.css";

export default function DailyTipBoard() {
  const [view, setView] = useState(() => ({ day: localDay(), offset: 0 }));
  useEffect(() => {
    const refreshDay = () => {
      const day = localDay();
      setView(current => current.day === day ? current : { day, offset: 0 });
    };
    const timer = window.setInterval(refreshDay, 60000);
    document.addEventListener("visibilitychange", refreshDay);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", refreshDay);
    };
  }, []);
  const tip = dailyCompostTip(view.day, view.offset);
  return (
    <aside className="tip-card daily-tip-board" aria-labelledby="daily-tip-heading">
      <span><Lightbulb size={23} strokeWidth={1.4} aria-hidden="true" /></span>
      <div className="daily-tip-copy">
        <strong id="daily-tip-heading">DID YOU KNOW?</strong>
        <p aria-live="polite" aria-atomic="true">{tip.text}</p>
        <div className="daily-tip-actions">
          <a href={tip.source.url} target="_blank" rel="noreferrer" aria-label={`Read source: ${tip.source.label} (opens a new tab)`}>Tip source</a>
          <button type="button" onClick={() => setView(current => ({ day: localDay(), offset: current.day === localDay() ? current.offset + 1 : 1 }))}>
            Another tip <ArrowRight size={14} aria-hidden="true" />
          </button>
        </div>
      </div>
      <LeaffyMascot placement="board" />
    </aside>
  );
}
