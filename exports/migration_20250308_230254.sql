-- Generated schema migration script
-- Generated at: 2025-03-08T23:02:54.145610

ALTER TABLE reports ADD COLUMN IF NOT EXISTS file_path TEXT;
-- TODO: Update the column type and constraints for file_path

ALTER TABLE reports ALTER COLUMN type TYPE text;

ALTER TABLE reports ALTER COLUMN status TYPE text;
