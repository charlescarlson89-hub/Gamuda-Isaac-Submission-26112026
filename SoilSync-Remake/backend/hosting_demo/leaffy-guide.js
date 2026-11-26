// Generated-demo wrapper: never imported by the real API-connected app.
import { findLeaffyAnswer as appGuide, leaffySuggestions } from "./leaffyKnowledge-app.js";
export { leaffySuggestions };

export function findLeaffyAnswer(question) {
  const q = question.toLowerCase();
  if (/reward|point|voucher|redeem|partner/.test(q))
    return "Demo daily check-in adds 10 EcoPoints (sample only); a demo weekly stage adds 100. AI scanning is off and earns no points here. Chat earns no points. Browse the current reward concepts and sample costs. Real partner fulfilment is not connected.";
  if (/privacy|data|account|password|saved|database/.test(q))
    return "This trainer demo creates no online account and saves no passwords. Sample progress stays in this browser. Photos are local previews, not uploaded or saved. Chat uses the bundled project guide without sending questions to Gemini. Log Out leaves your local demo progress available for a later visit.";
  if (/technology|tech stack|architecture|built with/.test(q))
    return "This trainer demo runs entirely in the browser on Firebase Hosting, with sample data and AI off. The separate full SoilSync app uses React/Capacitor, FastAPI on Vercel, Google Gemini and shared Neon PostgreSQL.";
  if (/\bai\b|gemini|scan|camera|model|offline|backend|chat/.test(q))
    return "Live AI is off in this trainer demo. Open Snap Waste, then Use sample photo to explore an illustrative classification. Your own photos only preview locally; they are never uploaded or analysed. Leaffy answers from the bundled project guide, without Gemini requests.";
  if (/batch|quest|check.?in|progress/.test(q))
    return "Demo batches and notes stay in this browser. Open a batch's next weekly stage and choose Use sample photo to preview the flow. Saving a demo stage adds sample points, without photo storage, AI verification or a maturity claim.";
  if (/register|workflow|journey|get started|how to use/.test(q))
    return "Choose Explore SoilSync, then open the demo with the supplied sample fields. No online account or real password is needed. Browse sample scans, recipes, batches, rewards and settings. Your sample progress stays in this browser.";
  return `Trainer demo · AI off. ${appGuide(question)}`;
}
