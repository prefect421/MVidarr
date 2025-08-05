-- Remove deprecated themes from MVidarr database
-- This script removes: LCARS (New), TARDIS, MTV themes

-- Check what themes exist before removal
SELECT name, display_name FROM custom_themes WHERE name IN ('lcars_new', 'tardis', 'mtv');

-- Remove the deprecated themes
DELETE FROM custom_themes WHERE name IN ('lcars_new', 'tardis', 'mtv');

-- Show remaining themes after removal
SELECT COUNT(*) as remaining_themes FROM custom_themes;
SELECT name, display_name FROM custom_themes ORDER BY display_name;