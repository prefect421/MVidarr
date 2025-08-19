#!/usr/bin/env python3
"""
Simple script to check service configurations directly from database
"""

import pymysql

def check_service_configs():
    """Check service configurations in database"""
    try:
        # Connect to database
        conn = pymysql.connect(
            host='localhost',
            user='mvidarr', 
            password='change_me_to_your_password',
            database='mvidarr'
        )
        
        cursor = conn.cursor()
        
        # Get service-related settings
        cursor.execute("""
            SELECT `key`, value FROM settings 
            WHERE `key` LIKE '%spotify%' OR `key` LIKE '%lastfm%' OR `key` LIKE '%imvdb%'
            ORDER BY `key`
        """)
        
        settings = cursor.fetchall()
        
        print("=== Current Service Configurations ===")
        for key, value in settings:
            # Mask sensitive values
            if 'secret' in key.lower() or 'key' in key.lower():
                display_value = f"{value[:10]}..." if value and len(value) > 10 else "NOT SET" if not value else "SET"
            else:
                display_value = value
            print(f"{key}: {display_value}")
        
        # Check which services are properly configured
        print("\n=== Service Status Summary ===")
        
        settings_dict = dict(settings)
        
        # Spotify
        spotify_enabled = settings_dict.get('spotify_enabled', 'false') == 'true'
        spotify_client_id = settings_dict.get('spotify_client_id', '')
        spotify_client_secret = settings_dict.get('spotify_client_secret', '')
        spotify_ready = spotify_enabled and spotify_client_id and spotify_client_secret
        print(f"Spotify: {'✓ READY' if spotify_ready else '✗ NOT READY'} (enabled={spotify_enabled}, has_credentials={bool(spotify_client_id and spotify_client_secret)})")
        
        # Last.fm
        lastfm_enabled = settings_dict.get('lastfm_enabled', 'false') == 'true'
        lastfm_api_key = settings_dict.get('lastfm_api_key', '')
        lastfm_ready = lastfm_enabled and bool(lastfm_api_key) and lastfm_api_key != 'your_lastfm_api_key_here'
        print(f"Last.fm: {'✓ READY' if lastfm_ready else '✗ NOT READY'} (enabled={lastfm_enabled}, has_api_key={bool(lastfm_api_key and lastfm_api_key != 'your_lastfm_api_key_here')})")
        
        # IMVDb  
        imvdb_api_key = settings_dict.get('imvdb_api_key', '')
        imvdb_ready = bool(imvdb_api_key)
        print(f"IMVDb: {'✓ READY' if imvdb_ready else '✗ NOT READY'} (has_api_key={bool(imvdb_api_key)})")
        
        ready_services = int(spotify_ready) + int(lastfm_ready) + int(imvdb_ready)
        print(f"\nTotal ready services: {ready_services}/3")
        
        if ready_services == 0:
            print("\n⚠️  NO SERVICES ARE READY FOR ENRICHMENT")
            print("This is why enrichment fails with 'No metadata found from any source'")
            print("\nTo fix:")
            print("1. Go to Settings > Services in the web interface")
            print("2. Configure at least one service (Spotify, Last.fm, or check IMVDb key)")
            print("3. Make sure to enable the service and provide valid API credentials")
        else:
            print(f"\n✓ {ready_services} service(s) ready for enrichment")
        
        conn.close()
        
    except Exception as e:
        print(f"Error checking service configs: {e}")

if __name__ == "__main__":
    check_service_configs()