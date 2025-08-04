-- Final theme migration for MVidarr
-- This script:
-- 1. Removes old LCARS themes (DS9, Voy, TNG-E) from user customizations
-- 2. Adds new themes (LCARS New, Punk'77, TARDIS, MTV) as built-in themes

-- Get admin user ID (create if doesn't exist)
INSERT IGNORE INTO users (username, email, password_hash, role, is_active, created_at, updated_at)
VALUES ('admin', 'admin@mvidarr.local', 'pbkdf2:sha256:600000$temp$temp', 'ADMIN', 1, NOW(), NOW());

SET @admin_user_id = (SELECT id FROM users WHERE username = 'admin' LIMIT 1);

-- Remove old LCARS theme customizations (user-created versions)
DELETE FROM custom_themes WHERE name IN ('lcars_ds9', 'lcars_voy', 'lcars_tng_e');

-- Remove existing new themes to avoid duplicates
DELETE FROM custom_themes WHERE name IN ('lcars_new', 'punk77', 'tardis', 'mtv');

-- Add the four new built-in themes

-- 1. LCARS (New) - Star Trek TNG with goldenrod sidebar/topbar
INSERT INTO custom_themes (
    name, display_name, description, created_by, is_public, is_built_in, 
    theme_data, light_theme_data, created_at, updated_at
) VALUES (
    'lcars_new',
    'LCARS (New)',
    'Star Trek TNG LCARS interface with goldenrod command sections',
    @admin_user_id,
    1,
    1,
    JSON_OBJECT(
        '--bg-primary', '#000000',
        '--bg-secondary', '#1a1a1a',
        '--bg-tertiary', '#2a2a2a',
        '--bg-modal', '#111111',
        '--bg-card', '#1e1e1e',
        '--bg-hover', '#333333',
        '--sidebar-bg', '#DAA520',
        '--topbar-bg', '#DAA520',
        '--text-primary', '#ffffff',
        '--text-secondary', '#e0e0e0',
        '--text-muted', '#999999',
        '--text-accent', '#ff9900',
        '--text-inverse', '#000000',
        '--btn-primary-bg', '#ff9900',
        '--btn-primary-text', '#000000',
        '--btn-secondary-bg', '#99ccff',
        '--btn-secondary-text', '#000000',
        '--btn-danger-bg', '#ff6666',
        '--btn-danger-text', '#000000',
        '--border-primary', '#ff9900',
        '--border-focus', '#99ccff',
        '--border-secondary', '#666666',
        '--success', '#99ff99',
        '--warning', '#ffcc00',
        '--error', '#ff6666',
        '--info', '#99ccff',
        '--accent-color', '#ff9900',
        '--highlight-color', '#99ccff',
        '--muted-color', '#666666'
    ),
    NULL,
    NOW(),
    NOW()
);

-- 2. Punk'77 - The Clash and Sex Pistols aesthetics
INSERT INTO custom_themes (
    name, display_name, description, created_by, is_public, is_built_in, 
    theme_data, light_theme_data, created_at, updated_at
) VALUES (
    'punk77',
    'Punk ''77',
    'Raw punk rock aesthetic inspired by The Clash and Sex Pistols',
    @admin_user_id,
    1,
    1,
    JSON_OBJECT(
        '--bg-primary', '#0d0d0d',
        '--bg-secondary', '#1a1a1a',
        '--bg-tertiary', '#262626',
        '--bg-modal', '#1f1f1f',
        '--bg-card', '#1e1e1e',
        '--bg-hover', '#333333',
        '--sidebar-bg', '#000000',
        '--topbar-bg', '#1a0000',
        '--text-primary', '#ffffff',
        '--text-secondary', '#e0e0e0',
        '--text-muted', '#999999',
        '--text-accent', '#ff0040',
        '--text-inverse', '#000000',
        '--btn-primary-bg', '#ff0040',
        '--btn-primary-text', '#ffffff',
        '--btn-secondary-bg', '#ffff00',
        '--btn-secondary-text', '#000000',
        '--btn-danger-bg', '#cc0000',
        '--btn-danger-text', '#ffffff',
        '--border-primary', '#ff0040',
        '--border-focus', '#ffff00',
        '--border-secondary', '#666666',
        '--success', '#00ff00',
        '--warning', '#ffff00',
        '--error', '#ff0000',
        '--info', '#ff0080',
        '--accent-color', '#ff0040',
        '--highlight-color', '#ffff00',
        '--muted-color', '#666666'
    ),
    NULL,
    NOW(),
    NOW()
);

-- 3. TARDIS - Doctor Who Tennant era with Oxford Blue
INSERT INTO custom_themes (
    name, display_name, description, created_by, is_public, is_built_in, 
    theme_data, light_theme_data, created_at, updated_at
) VALUES (
    'tardis',
    'TARDIS',
    'Doctor Who TARDIS interior inspired by the Tennant era console room',
    @admin_user_id,
    1,
    1,
    JSON_OBJECT(
        '--bg-primary', '#0f1419',
        '--bg-secondary', '#1a2332',
        '--bg-tertiary', '#253447',
        '--bg-modal', '#1e2a3a',
        '--bg-card', '#1c2633',
        '--bg-hover', '#2d3e52',
        '--sidebar-bg', '#002147',
        '--topbar-bg', '#002147',
        '--text-primary', '#ffffff',
        '--text-secondary', '#b8d4f0',
        '--text-muted', '#7a9cc6',
        '--text-accent', '#4db8ff',
        '--text-inverse', '#000000',
        '--btn-primary-bg', '#4db8ff',
        '--btn-primary-text', '#ffffff',
        '--btn-secondary-bg', '#ff8c42',
        '--btn-secondary-text', '#000000',
        '--btn-danger-bg', '#ff4757',
        '--btn-danger-text', '#ffffff',
        '--border-primary', '#4db8ff',
        '--border-focus', '#70c1ff',
        '--border-secondary', '#4a6b8a',
        '--success', '#26d0ce',
        '--warning', '#ff8c42',
        '--error', '#ff4757',
        '--info', '#4db8ff',
        '--accent-color', '#4db8ff',
        '--highlight-color', '#70c1ff',
        '--muted-color', '#4a6b8a'
    ),
    NULL,
    NOW(),
    NOW()
);

-- 4. MTV - Early 80s neon MTV logo colors
INSERT INTO custom_themes (
    name, display_name, description, created_by, is_public, is_built_in, 
    theme_data, light_theme_data, created_at, updated_at
) VALUES (
    'mtv',
    'MTV',
    'Early 80s MTV neon aesthetic with electric colors and bold contrasts',
    @admin_user_id,
    1,
    1,
    JSON_OBJECT(
        '--bg-primary', '#0a0a0a',
        '--bg-secondary', '#1a1a1a',
        '--bg-tertiary', '#2a2a2a',
        '--bg-modal', '#1f1f1f',
        '--bg-card', '#1e1e1e',
        '--bg-hover', '#333333',
        '--sidebar-bg', '#ff1493',
        '--topbar-bg', '#ff1493',
        '--text-primary', '#ffffff',
        '--text-secondary', '#f0f0f0',
        '--text-muted', '#cccccc',
        '--text-accent', '#00ffff',
        '--text-inverse', '#000000',
        '--btn-primary-bg', '#00ffff',
        '--btn-primary-text', '#000000',
        '--btn-secondary-bg', '#ffff00',
        '--btn-secondary-text', '#000000',
        '--btn-danger-bg', '#ff0080',
        '--btn-danger-text', '#ffffff',
        '--border-primary', '#00ffff',
        '--border-focus', '#ffff00',
        '--border-secondary', '#666666',
        '--success', '#00ff00',
        '--warning', '#ffff00',
        '--error', '#ff0080',
        '--info', '#00ffff',
        '--accent-color', '#ff1493',
        '--highlight-color', '#00ffff',
        '--secondary-accent', '#ffff00',
        '--muted-color', '#666666'
    ),
    NULL,
    NOW(),
    NOW()
);

-- Verify the themes were created
SELECT 
    id,
    name,
    display_name,
    description,
    is_public,
    is_built_in,
    created_at
FROM custom_themes 
WHERE name IN ('lcars_new', 'punk77', 'tardis', 'mtv')
   OR is_built_in = 1
ORDER BY 
    CASE 
        WHEN name IN ('lcars_new', 'punk77', 'tardis', 'mtv') THEN 1 
        ELSE 2 
    END,
    created_at;

-- Show total theme count
SELECT 
    COUNT(*) as total_themes,
    SUM(CASE WHEN is_built_in = 1 THEN 1 ELSE 0 END) as built_in_themes,
    SUM(CASE WHEN is_built_in = 0 THEN 1 ELSE 0 END) as custom_themes
FROM custom_themes;