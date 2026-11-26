import guide from "../data/leaffy-guide.json" with { type: "json" };

export const leaffySuggestions = [
  "What is SoilSync?",
  "How do EcoPoints work?",
  "Can I compost banana peels?",
  "Who built SoilSync?",
];

export function findLeaffyAnswer(question) {
  const q = question.toLowerCase();
  if (/reward|point|skin|animation|voucher|redeem|partner/.test(q))
    return "Daily check-in earns 10 EcoPoints, a new scan with compostable waste 50, and an approved weekly batch quest 100. Repeated uploads do not earn points again. Browse Rewards for the current coffee offers, eco-bags, seeds and their point costs. Chat earns no points. Real partner fulfilment is not connected.";
  if (/privacy|data|account|password|saved|database/.test(q))
    return "SoilSync has account login and registration. Passwords are stored as secure hashes, and your profile, progress and claims belong to your account. Weekly check-in photos are private. Scan photos go to Google Gemini for analysis. Logging out ends this session without deleting your data.";
  if (/play|game|pet|leaffy/.test(q))
    return "That’s me! I’m SoilSync’s little leaf companion. Find me beside the daily tip board on Home, or on the landing page. Tap me to ask about SoilSync, food scraps and beginner composting. I rest at night, but you can wake me for a chat.";
  if (/bokashi/.test(q))
    return "Bokashi Composting uses inoculated bran and a sealed bucket. Press out air, keep the lid closed and drain the tap as directed. After about two weeks sealed once full, finish breaking down the pre-compost in soil or a compost system away from roots. Open Fertilizer for the illustrated steps.";
  if (/composting method|hot compost|cold compost|worm compost|leafmould|which recipe/.test(q))
    return "SoilSync offers Hot Composting, Cold Composting and Bokashi Composting. Hot composting needs active care, cold composting takes longer with less turning, and Bokashi starts with sealed fermentation. In Fertilizer, tap each of the three steps for its image guide and instructions.";
  if (/batch|check.?in|progress/.test(q))
    return "Create named batches from Home or the Fertilizer guide. Each has a weekly check-in schedule based on its method. Switch batches in the tracker and delete a completed batch at 100%. Check-ins record your routine and compost maturity needs a separate assessment.";
  if (/\bai\b|gemini|scan|camera|model|offline|backend/.test(q))
    return "Take or upload a clear photo on Snap Waste, then select Identify waste. The server asks Gemini for catalogue matches and uses SoilSync database guidance for the result. Unknown materials stay out of the recipe. If Gemini is unavailable, no live scan result or points are invented.";
  if (/register|workflow|journey|get started|how to use/.test(q))
    return "Create an account after reading the data-use notice, or log in. Scan scraps, review the recommended method and choose a compost recipe. Track separate batches with weekly photo check-ins, then explore eco rewards.";
  let best = null,
    score = 0;
  for (const item of guide) {
    const n = item.keywords.reduce(
      (sum, word) => sum + (q.includes(word.toLowerCase()) ? word.length : 0),
      0,
    );
    if (n > score) {
      score = n;
      best = item;
    }
  }
  return (
    best?.answer ||
    "I can help with SoilSync, food scraps and beginner composting. My project guide is available now; try again later for live AI, or ask a project-guide question. Try “Can I compost banana peels?”"
  );
}
