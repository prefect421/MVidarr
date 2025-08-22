#!/usr/bin/env python3
"""
Analysis script to identify blank metadata fields across artists
Part of 0.9.7 todo item: Review and create action plan for blank metadata fields
"""

import sys
from pathlib import Path
from collections import defaultdict, Counter
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def analyze_blank_metadata():
    """Analyze which metadata fields are most commonly blank"""
    print("=== Blank Metadata Fields Analysis ===")
    print("Analyzing artist metadata to identify improvement opportunities\n")
    
    try:
        # Import database components
        from src.database.connection import get_db
        from src.database.models import Artist
        
        with get_db() as session:
            artists = session.query(Artist).all()
            
            if not artists:
                print("No artists found in database")
                return
            
            print(f"Analyzing {len(artists)} artists...")
            
            # Track blank fields
            blank_counts = Counter()
            total_artists = len(artists)
            
            # Standard fields to check
            standard_fields = [
                'genres', 'overview', 'formed_year', 'disbanded_year', 
                'origin_country', 'spotify_id', 'lastfm_name', 'imvdb_id'
            ]
            
            # Extended metadata fields to check (from imvdb_metadata)
            extended_fields = [
                'biography', 'images', 'related_artists', 'popularity', 
                'followers', 'playcount', 'listeners', 'external_links'
            ]
            
            for artist in artists:
                # Check standard fields
                for field in standard_fields:
                    value = getattr(artist, field, None)
                    if not value or (isinstance(value, str) and not value.strip()):
                        blank_counts[f"standard.{field}"] += 1
                
                # Check extended metadata fields
                metadata = artist.imvdb_metadata or {}
                for field in extended_fields:
                    if not metadata.get(field):
                        blank_counts[f"extended.{field}"] += 1
            
            # Generate report
            print("\n" + "="*60)
            print("BLANK METADATA FIELDS REPORT")
            print("="*60)
            
            print("\n📊 STANDARD FIELDS (Most Critical):")
            print("-" * 40)
            standard_blanks = [(k, v) for k, v in blank_counts.items() if k.startswith('standard.')]
            standard_blanks.sort(key=lambda x: x[1], reverse=True)
            
            for field_name, count in standard_blanks:
                field = field_name.replace('standard.', '')
                percentage = (count / total_artists) * 100
                print(f"  {field:15} : {count:4d}/{total_artists} artists ({percentage:5.1f}% blank)")
            
            print("\n🔍 EXTENDED FIELDS (Enrichment Opportunities):")
            print("-" * 40)
            extended_blanks = [(k, v) for k, v in blank_counts.items() if k.startswith('extended.')]
            extended_blanks.sort(key=lambda x: x[1], reverse=True)
            
            for field_name, count in extended_blanks:
                field = field_name.replace('extended.', '')
                percentage = (count / total_artists) * 100
                print(f"  {field:15} : {count:4d}/{total_artists} artists ({percentage:5.1f}% blank)")
            
            # Generate action plan
            print("\n" + "="*60)
            print("📋 ACTION PLAN")
            print("="*60)
            
            # Identify top priorities
            high_priority = [item for item in standard_blanks if item[1] / total_artists > 0.7]
            medium_priority = [item for item in standard_blanks if 0.3 < item[1] / total_artists <= 0.7]
            enrichment_priority = [item for item in extended_blanks if item[1] / total_artists > 0.8]
            
            if high_priority:
                print("\n🚨 HIGH PRIORITY (>70% blank - critical fixes needed):")
                for field_name, count in high_priority:
                    field = field_name.replace('standard.', '')
                    print(f"  • {field}: Implement mandatory data collection")
            
            if medium_priority:
                print("\n⚠️  MEDIUM PRIORITY (30-70% blank - improvement needed):")
                for field_name, count in medium_priority:
                    field = field_name.replace('standard.', '')
                    print(f"  • {field}: Enhance data validation and prompts")
            
            if enrichment_priority:
                print("\n🎯 ENRICHMENT PRIORITY (>80% blank - automation opportunities):")
                for field_name, count in enrichment_priority:
                    field = field_name.replace('extended.', '')
                    print(f"  • {field}: Implement automatic enrichment from external APIs")
            
            # Service integration recommendations
            print("\n🔗 SERVICE INTEGRATION RECOMMENDATIONS:")
            spotify_blank = blank_counts.get('standard.spotify_id', 0)
            lastfm_blank = blank_counts.get('standard.lastfm_name', 0)
            imvdb_blank = blank_counts.get('standard.imvdb_id', 0)
            
            if spotify_blank > total_artists * 0.5:
                print(f"  • Spotify: {spotify_blank} artists missing IDs - improve search integration")
            if lastfm_blank > total_artists * 0.5:
                print(f"  • Last.fm: {lastfm_blank} artists missing names - enhance name matching")
            if imvdb_blank > total_artists * 0.5:
                print(f"  • IMVDb: {imvdb_blank} artists missing IDs - improve video discovery")
            
            print("\n" + "="*60)
            print(f"Analysis complete. Total artists: {total_artists}")
            print("="*60)
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_blank_metadata()