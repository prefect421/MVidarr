#!/usr/bin/env python3
"""
Simple enrichment test without Flask app initialization
"""

import sys
import os
import asyncio
sys.path.insert(0, 'src')

# Direct imports without db initialization
from src.services.spotify_service import spotify_service
from src.services.lastfm_service import lastfm_service

async def test_services():
    """Test service configurations"""
    print("=== Service Status ===")
    
    # Test Spotify
    print(f"Spotify enabled: {spotify_service.enabled}")
    if spotify_service.enabled:
        print(f"  Client ID configured: {'✓' if spotify_service.client_id else '✗'}")
        print(f"  Client Secret configured: {'✓' if spotify_service.client_secret else '✗'}")
        
        # Test Spotify search (uses client credentials, no user auth needed)
        try:
            # Get client credentials token
            token_data = spotify_service.get_client_credentials_token()
            spotify_service.access_token = token_data['access_token']
            
            # Test search
            results = spotify_service.search_artist("Metallica", limit=1)
            if results.get('artists', {}).get('items'):
                print("  ✓ Spotify API working - found test artist")
                artist = results['artists']['items'][0]
                print(f"    Found: {artist['name']} (popularity: {artist.get('popularity', 'N/A')})")
            else:
                print("  ✗ Spotify API search returned no results")
        except Exception as e:
            print(f"  ✗ Spotify API error: {e}")
    
    print()
    
    # Test Last.fm
    print(f"Last.fm enabled: {lastfm_service.enabled}")
    if lastfm_service.enabled:
        print(f"  API Key configured: {'✓' if lastfm_service.api_key else '✗'}")
        
        # Test Last.fm search (no auth needed for basic info)
        try:
            artist_info = lastfm_service.get_artist_info("Metallica")
            if artist_info and artist_info.get('name'):
                print("  ✓ Last.fm API working - found test artist")
                print(f"    Found: {artist_info['name']} (listeners: {artist_info.get('listeners', 'N/A')})")
            else:
                print("  ✗ Last.fm API returned no results")
        except Exception as e:
            print(f"  ✗ Last.fm API error: {e}")
    
    print()
    
    # Check IMVDb via settings
    from src.services.settings_service import settings
    imvdb_key = settings.get("imvdb_api_key", "")
    print(f"IMVDb API key configured: {'✓' if imvdb_key else '✗'}")
    
    if imvdb_key:
        from src.services.imvdb_service import imvdb_service
        try:
            results = imvdb_service.search_artist("Metallica")
            if results and results.get('results'):
                print("  ✓ IMVDb API working - found test artist")
                artist = results['results'][0]
                print(f"    Found: {artist['name']} (ID: {artist.get('id', 'N/A')})")
            else:
                print("  ✗ IMVDb API returned no results")
        except Exception as e:
            print(f"  ✗ IMVDb API error: {e}")
    
    print("\n=== Summary ===")
    working_services = []
    if spotify_service.enabled:
        working_services.append("Spotify")
    if lastfm_service.enabled:
        working_services.append("Last.fm")
    if imvdb_key:
        working_services.append("IMVDb")
    
    print(f"Working services: {', '.join(working_services) if working_services else 'None'}")
    print(f"Total: {len(working_services)}/3")
    
    if len(working_services) >= 1:
        print("✓ Enrichment should work with at least one service")
    else:
        print("✗ No services configured - enrichment will fail")

if __name__ == "__main__":
    asyncio.run(test_services())