-- Run in the soilsync_remake_test database using pgAdmin Query Tool.
SELECT current_database() AS database_name;

SELECT 'fertilizer_types' AS section, count(*) AS records FROM fertilizer_types
UNION ALL
SELECT 'plants' AS section, count(*) AS records FROM plants
UNION ALL
SELECT 'rewards' AS section, count(*) AS records FROM rewards
UNION ALL
SELECT 'users' AS section, count(*) AS records FROM users
UNION ALL
SELECT 'waste_types' AS section, count(*) AS records FROM waste_types
UNION ALL
SELECT 'auth_sessions' AS section, count(*) AS records FROM auth_sessions
UNION ALL
SELECT 'batches' AS section, count(*) AS records FROM batches
UNION ALL
SELECT 'daily_checkins' AS section, count(*) AS records FROM daily_checkins
UNION ALL
SELECT 'fertilizer_maintenance_guides' AS section, count(*) AS records FROM fertilizer_maintenance_guides
UNION ALL
SELECT 'fertilizer_recipe_steps' AS section, count(*) AS records FROM fertilizer_recipe_steps
UNION ALL
SELECT 'fertilizer_suitable_plants' AS section, count(*) AS records FROM fertilizer_suitable_plants
UNION ALL
SELECT 'points_ledger' AS section, count(*) AS records FROM points_ledger
UNION ALL
SELECT 'reward_claims' AS section, count(*) AS records FROM reward_claims
UNION ALL
SELECT 'scan_logs' AS section, count(*) AS records FROM scan_logs
UNION ALL
SELECT 'user_settings' AS section, count(*) AS records FROM user_settings
UNION ALL
SELECT 'waste_fertilizer_matches' AS section, count(*) AS records FROM waste_fertilizer_matches
UNION ALL
SELECT 'weekly_checkin_quests' AS section, count(*) AS records FROM weekly_checkin_quests
ORDER BY section;

SELECT u.id, u.username, u.points_balance, coalesce(sum(l.points),0) AS ledger_balance
FROM users u LEFT JOIN points_ledger l ON l.user_id=u.id
GROUP BY u.id
HAVING u.points_balance <> coalesce(sum(l.points),0);
-- Last query should return zero rows.

-- After migration 0002: inspect the database-backed scan -> recipe -> plant chain.
SELECT w.id AS waste_type_id, w.name AS waste_name, f.id AS fertilizer_type_id,
       f.name AS fertilizer_name, s.step_number, s.instruction,
       p.name AS plant, fp.is_recommended
FROM waste_types w
JOIN waste_fertilizer_matches m ON m.waste_type_id = w.id
JOIN fertilizer_types f ON f.id = m.fertilizer_type_id
JOIN fertilizer_recipe_steps s ON s.fertilizer_type_id = f.id
JOIN fertilizer_suitable_plants fp ON fp.fertilizer_type_id = f.id
JOIN plants p ON p.id = fp.plant_id
WHERE w.id = 1
ORDER BY f.id, s.step_number, p.id;

SELECT id, batch_id, week_number, status, verification->>'status' AS visual_approval,
       verification->>'confidence' AS model_estimate
FROM weekly_checkin_quests
ORDER BY id;
-- NULL verification means earlier/mock proof, not AI approval.
