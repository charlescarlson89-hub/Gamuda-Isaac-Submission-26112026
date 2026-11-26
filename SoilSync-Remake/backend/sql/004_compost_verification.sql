-- Additive upgrade for existing SoilSync databases. Existing proof stays unverified.
ALTER TABLE weekly_checkin_quests ADD COLUMN image_sha256 varchar(64);
ALTER TABLE weekly_checkin_quests ADD COLUMN verification jsonb;
ALTER TABLE weekly_checkin_quests ADD CONSTRAINT uq_weekly_batch_image UNIQUE (batch_id, image_sha256);
