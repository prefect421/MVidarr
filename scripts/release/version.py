#!/usr/bin/env python3
"""
MVidarr - Version Management Script
Handles semantic versioning, changelog generation, and release preparation.
"""

import os
import sys
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class VersionManager:
    """Manages application versioning and release automation"""
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent.parent
        self.version_file = self.project_root / 'version.json'
        self.changelog_file = self.project_root / 'CHANGELOG.md'
        
    def get_current_version(self) -> str:
        """Get current version from version file or git tags"""
        # Try version file first
        if self.version_file.exists():
            try:
                with open(self.version_file, 'r') as f:
                    data = json.load(f)
                    return data.get('version', '0.0.0')
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Fallback to git tags
        try:
            result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                return result.stdout.strip().lstrip('v')
        except subprocess.SubprocessError:
            pass
        
        return '0.0.0'
    
    def parse_version(self, version: str) -> Tuple[int, int, int, Optional[str]]:
        """Parse semantic version string"""
        # Remove 'v' prefix if present
        version = version.lstrip('v')
        
        # Handle pre-release versions (e.g., 1.0.0-alpha.1)
        if '-' in version:
            version, prerelease = version.split('-', 1)
        else:
            prerelease = None
        
        try:
            major, minor, patch = map(int, version.split('.'))
            return major, minor, patch, prerelease
        except ValueError:
            raise ValueError(f"Invalid version format: {version}")
    
    def increment_version(self, current_version: str, increment_type: str) -> str:
        """Increment version based on type (major, minor, patch)"""
        major, minor, patch, _ = self.parse_version(current_version)
        
        if increment_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif increment_type == 'minor':
            minor += 1
            patch = 0
        elif increment_type == 'patch':
            patch += 1
        else:
            raise ValueError(f"Invalid increment type: {increment_type}")
        
        return f"{major}.{minor}.{patch}"
    
    def update_version_file(self, version: str, build_info: Dict = None):
        """Update version.json file"""
        data = {
            'version': version,
            'build_date': datetime.now().isoformat(),
            'git_commit': self.get_git_commit(),
            'git_branch': self.get_git_branch()
        }
        
        if build_info:
            data.update(build_info)
        
        with open(self.version_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Updated version file: {version}")
    
    def get_git_commit(self) -> str:
        """Get current git commit hash"""
        try:
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except subprocess.SubprocessError:
            return 'unknown'
    
    def get_git_branch(self) -> str:
        """Get current git branch"""
        try:
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except subprocess.SubprocessError:
            return 'unknown'
    
    def get_commits_since_tag(self, tag: str = None) -> List[str]:
        """Get commit messages since last tag"""
        if not tag:
            try:
                result = subprocess.run(['git', 'describe', '--tags', '--abbrev=0'], 
                                      capture_output=True, text=True, cwd=self.project_root)
                tag = result.stdout.strip() if result.returncode == 0 else None
            except subprocess.SubprocessError:
                tag = None
        
        if tag:
            cmd = ['git', 'log', '--pretty=format:%s', f'{tag}..HEAD']
        else:
            cmd = ['git', 'log', '--pretty=format:%s']
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.split('\n') if line.strip()]
        except subprocess.SubprocessError:
            pass
        
        return []
    
    def categorize_commits(self, commits: List[str]) -> Dict[str, List[str]]:
        """Categorize commits by type"""
        categories = {
            'features': [],
            'fixes': [],
            'improvements': [],
            'breaking': [],
            'other': []
        }
        
        for commit in commits:
            commit_lower = commit.lower()
            
            if any(keyword in commit_lower for keyword in ['feat:', 'feature:', 'add:', 'implement']):
                categories['features'].append(commit)
            elif any(keyword in commit_lower for keyword in ['fix:', 'bug:', 'resolve', 'fixed']):
                categories['fixes'].append(commit)
            elif any(keyword in commit_lower for keyword in ['improve:', 'enhance:', 'update:', 'refactor']):
                categories['improvements'].append(commit)
            elif any(keyword in commit_lower for keyword in ['breaking:', 'break:', 'major:']):
                categories['breaking'].append(commit)
            else:
                categories['other'].append(commit)
        
        return categories
    
    def generate_changelog_entry(self, version: str, commits: List[str]) -> str:
        """Generate changelog entry for version"""
        categories = self.categorize_commits(commits)
        
        entry = f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        if categories['breaking']:
            entry += "### 💥 Breaking Changes\n"
            for commit in categories['breaking']:
                entry += f"- {commit}\n"
            entry += "\n"
        
        if categories['features']:
            entry += "### ✨ New Features\n"
            for commit in categories['features']:
                entry += f"- {commit}\n"
            entry += "\n"
        
        if categories['improvements']:
            entry += "### 🚀 Improvements\n"
            for commit in categories['improvements']:
                entry += f"- {commit}\n"
            entry += "\n"
        
        if categories['fixes']:
            entry += "### 🐛 Bug Fixes\n"
            for commit in categories['fixes']:
                entry += f"- {commit}\n"
            entry += "\n"
        
        if categories['other']:
            entry += "### 📋 Other Changes\n"
            for commit in categories['other']:
                entry += f"- {commit}\n"
            entry += "\n"
        
        return entry
    
    def update_changelog(self, version: str, commits: List[str]):
        """Update CHANGELOG.md with new version"""
        # Create changelog if it doesn't exist
        if not self.changelog_file.exists():
            with open(self.changelog_file, 'w') as f:
                f.write("# Changelog\n\nAll notable changes to MVidarr will be documented in this file.\n\n")
        
        # Read existing content
        with open(self.changelog_file, 'r') as f:
            existing_content = f.read()
        
        # Generate new entry
        new_entry = self.generate_changelog_entry(version, commits)
        
        # Insert new entry after header
        lines = existing_content.split('\n')
        header_end = 0
        for i, line in enumerate(lines):
            if line.startswith('# ') or line.startswith('All notable changes'):
                header_end = i + 1
            elif line.strip() == '':
                continue
            else:
                break
        
        # Insert new entry
        new_lines = lines[:header_end] + [''] + new_entry.split('\n') + lines[header_end:]
        
        with open(self.changelog_file, 'w') as f:
            f.write('\n'.join(new_lines))
        
        print(f"✅ Updated changelog: {version}")
    
    def create_git_tag(self, version: str, message: str = None):
        """Create and push git tag"""
        tag_name = f"v{version}"
        
        if not message:
            message = f"Release {tag_name}"
        
        try:
            # Create tag
            subprocess.run(['git', 'tag', '-a', tag_name, '-m', message], 
                         check=True, cwd=self.project_root)
            
            # Push tag
            subprocess.run(['git', 'push', 'origin', tag_name], 
                         check=True, cwd=self.project_root)
            
            print(f"✅ Created and pushed git tag: {tag_name}")
            return True
        except subprocess.SubprocessError as e:
            print(f"❌ Failed to create git tag: {e}")
            return False
    
    def prepare_release(self, increment_type: str, dry_run: bool = False) -> str:
        """Prepare a new release"""
        current_version = self.get_current_version()
        new_version = self.increment_version(current_version, increment_type)
        
        print(f"🚀 Preparing release: {current_version} → {new_version}")
        
        # Get commits since last version
        commits = self.get_commits_since_tag()
        
        if not dry_run:
            # Update version file
            self.update_version_file(new_version)
            
            # Update changelog
            self.update_changelog(new_version, commits)
            
            # Commit changes
            subprocess.run(['git', 'add', str(self.version_file), str(self.changelog_file)], 
                         cwd=self.project_root)
            subprocess.run(['git', 'commit', '-m', f'Prepare release {new_version}'], 
                         cwd=self.project_root)
            
            # Create tag
            self.create_git_tag(new_version)
        else:
            print("🔍 Dry run - no changes made")
            print(f"Would update to version: {new_version}")
            print(f"Found {len(commits)} commits since last release")
        
        return new_version

def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MVidarr Version Management')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Current version
    current_parser = subparsers.add_parser('current', help='Show current version')
    
    # Increment version
    increment_parser = subparsers.add_parser('increment', help='Increment version')
    increment_parser.add_argument('type', choices=['major', 'minor', 'patch'], 
                                help='Version increment type')
    increment_parser.add_argument('--dry-run', action='store_true', 
                                help='Show what would be done without making changes')
    
    # Release
    release_parser = subparsers.add_parser('release', help='Prepare release')
    release_parser.add_argument('type', choices=['major', 'minor', 'patch'], 
                               help='Release type')
    release_parser.add_argument('--dry-run', action='store_true', 
                               help='Show what would be done without making changes')
    
    # Changelog
    changelog_parser = subparsers.add_parser('changelog', help='Generate changelog')
    changelog_parser.add_argument('--version', help='Version for changelog entry')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    vm = VersionManager()
    
    if args.command == 'current':
        version = vm.get_current_version()
        print(f"Current version: {version}")
    
    elif args.command == 'increment':
        current = vm.get_current_version()
        new_version = vm.increment_version(current, args.type)
        if not args.dry_run:
            vm.update_version_file(new_version)
        print(f"Version: {current} → {new_version}")
    
    elif args.command == 'release':
        vm.prepare_release(args.type, args.dry_run)
    
    elif args.command == 'changelog':
        version = args.version or vm.get_current_version()
        commits = vm.get_commits_since_tag()
        if not args.dry_run:
            vm.update_changelog(version, commits)
        else:
            entry = vm.generate_changelog_entry(version, commits)
            print(entry)

if __name__ == '__main__':
    main()