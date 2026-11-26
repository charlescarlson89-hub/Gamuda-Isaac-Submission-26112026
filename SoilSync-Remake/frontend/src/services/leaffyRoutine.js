export const LEAFFY_TIME_ZONE = "Asia/Kuala_Lumpur";
export const LEAFFY_IDLE_MS = 45000;
export const LEAFFY_YAWN_MS = 4000;
export const LEAFFY_YAWN_COOLDOWN_MS = 65000;
export const LEAFFY_SUN_MS = 6000;

export function getLeaffyPeriod(date = new Date()) {
  const hour = Number(
    new Intl.DateTimeFormat("en-GB", {
      timeZone: LEAFFY_TIME_ZONE,
      hour: "2-digit",
      hourCycle: "h23",
    }).format(date),
  );
  return hour >= 7 && hour < 19 ? "day" : "night";
}

export function nextSunshineDelay(random = Math.random()) {
  return 24000 + Math.floor(Math.max(0, Math.min(1, random)) * 24000);
}

export function shouldLeaffyYawn(now, lastActivity, lastYawn) {
  return (
    now - lastActivity >= LEAFFY_IDLE_MS &&
    now - lastYawn >= LEAFFY_YAWN_COOLDOWN_MS
  );
}
