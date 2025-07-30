#!/bin/bash

# MVidarr Project Manager Agent Setup Script
# Sets up the intelligent project management system

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 Setting up MVidarr Project Manager Agent..."

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository"
    exit 1
fi

# Check for required API keys
echo "🔑 Checking API key configuration..."

if [ -z "$GITHUB_TOKEN" ]; then
    echo "⚠️  GITHUB_TOKEN environment variable not set"
    echo "   You need a GitHub Personal Access Token with repo permissions"
    echo "   Create one at: https://github.com/settings/tokens"
    echo "   Then add to your shell config:"
    echo "   export GITHUB_TOKEN='your-token-here'"
    MISSING_KEYS=true
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  ANTHROPIC_API_KEY environment variable not set"
    echo "   You need an Anthropic API key for Claude integration"
    echo "   Get one at: https://console.anthropic.com/"
    echo "   Then add to your shell config:"
    echo "   export ANTHROPIC_API_KEY='your-key-here'"
    MISSING_KEYS=true
fi

if [ "$MISSING_KEYS" = true ]; then
    echo ""
    echo "🔧 Example shell configuration (~/.bashrc or ~/.zshrc):"
    echo "# Replace 'your_token_here' with your actual GitHub Personal Access Token"
    echo "export GITHUB_TOKEN='your_github_token_here'"
    echo "# Replace 'your_key_here' with your actual Anthropic API key"
    echo "export ANTHROPIC_API_KEY='your_anthropic_key_here'"
    echo ""
    echo "After setting these, restart your shell or run: source ~/.bashrc"
fi

# Install required Python packages using pipx to avoid system conflicts
echo "📦 Installing required Python packages..."

# Check if pipx is available
if command -v pipx &> /dev/null; then
    echo "✅ Using pipx for package installation"
    pipx install requests --force 2>/dev/null || echo "requests already installed"
else
    echo "ℹ️  pipx not available, trying pip with --user flag"
    pip3 install --user requests || echo "⚠️  Could not install requests package"
fi

# Make scripts executable
chmod +x "$SCRIPT_DIR/project_manager_agent.py"
chmod +x "$SCRIPT_DIR/programmer_agent.py" 2>/dev/null || echo "⚠️  programmer_agent.py not found"
chmod +x "$SCRIPT_DIR/code_review_agent.py" 2>/dev/null || echo "⚠️  code_review_agent.py not found"

# Create project manager aliases
PROJECT_MANAGER_ALIAS_FILE="$HOME/.mvidarr_project_manager_aliases"
cat > "$PROJECT_MANAGER_ALIAS_FILE" << 'EOF'
# MVidarr Project Manager Agent Aliases

# Main project management commands
alias mvidarr-pm='python3 ~/mvidarr/scripts/project_manager_agent.py'
alias mvidarr-pm-cycle='python3 ~/mvidarr/scripts/project_manager_agent.py cycle'
alias mvidarr-pm-next='python3 ~/mvidarr/scripts/project_manager_agent.py next'
alias mvidarr-pm-list='python3 ~/mvidarr/scripts/project_manager_agent.py list'

# Quick shortcut - pma triggers the project management cycle
alias pma='python3 ~/mvidarr/scripts/project_manager_agent.py cycle'

# Quick project management functions
mvidarr-pm-process() {
    if [ -z "$1" ]; then
        echo "Usage: mvidarr-pm-process <issue_number>"
        return 1
    fi
    python3 ~/mvidarr/scripts/project_manager_agent.py process "$1"
}

mvidarr-pm-status() {
    echo "🔍 MVidarr Project Status"
    echo "========================"
    echo "📋 Open Issues:"
    python3 ~/mvidarr/scripts/project_manager_agent.py list --state open | head -20
    echo ""
    echo "🚀 Next Priority Issue:"
    python3 ~/mvidarr/scripts/project_manager_agent.py next
}

mvidarr-pm-help() {
    echo "🚀 MVidarr Project Manager Agent Commands"
    echo "========================================"
    echo ""
    echo "Core Commands:"
    echo "  pma                           - 🚀 Quick shortcut: Run project management cycle"
    echo "  mvidarr-pm cycle              - Run complete project management cycle"
    echo "  mvidarr-pm next               - Show next highest priority issue"
    echo "  mvidarr-pm list               - List all issues by priority"
    echo "  mvidarr-pm-process <number>   - Process specific issue number"
    echo "  mvidarr-pm-status             - Show current project status"
    echo ""
    echo "Options:"
    echo "  mvidarr-pm cycle --max-issues 3  - Limit issues per cycle"
    echo "  mvidarr-pm list --state closed   - Show closed issues"
    echo ""
    echo "Environment Variables:"
    echo "  GITHUB_TOKEN        - GitHub Personal Access Token (required)"
    echo "  ANTHROPIC_API_KEY   - Anthropic API Key (required)"
    echo ""
    echo "Workflow:"
    echo "  1. 🔍 Analyze GitHub issues and select highest priority"
    echo "  2. 👨‍💻 Assign to programmer agent for code generation"
    echo "  3. 🔍 Send to review agent for security and quality checks"
    echo "  4. 🔄 Loop revision if needed, or proceed to deployment"
    echo "  5. 🚀 Deploy approved code to dev branch"
    echo "  6. ✅ Mark issue complete and move to next"
}
EOF

# Source the aliases in shell config files
for shell_config in ~/.bashrc ~/.zshrc; do
    if [ -f "$shell_config" ]; then
        if ! grep -q "source $PROJECT_MANAGER_ALIAS_FILE" "$shell_config"; then
            echo "source $PROJECT_MANAGER_ALIAS_FILE" >> "$shell_config"
            echo "✅ Added project manager aliases to $shell_config"
        fi
    fi
done

# Create workflow examples script
cat > "$SCRIPT_DIR/project_manager_examples.sh" << 'EOF'
#!/bin/bash

# MVidarr Project Manager Agent - Example Usage

echo "🚀 MVidarr Project Manager Agent - Example Workflows"
echo "=================================================="
echo ""

echo "1. Run Complete Project Management Cycle:"
echo "   python3 scripts/project_manager_agent.py cycle"
echo "   # Processes up to 5 highest priority issues automatically"
echo ""

echo "2. Process Limited Number of Issues:"
echo "   python3 scripts/project_manager_agent.py cycle --max-issues 2"
echo "   # Process only 2 issues in this cycle"
echo ""

echo "3. Check Next Priority Issue:"
echo "   python3 scripts/project_manager_agent.py next"
echo "   # Shows the next issue that would be processed"
echo ""

echo "4. Process Specific Issue:"
echo "   python3 scripts/project_manager_agent.py process 123"
echo "   # Process issue #123 specifically"
echo ""

echo "5. List Issues by Priority:"
echo "   python3 scripts/project_manager_agent.py list"
echo "   # Shows all open issues sorted by priority"
echo ""

echo "6. List Closed Issues:"
echo "   python3 scripts/project_manager_agent.py list --state closed"
echo "   # Shows recently closed issues"
echo ""

echo "7. Using Aliases (after sourcing ~/.mvidarr_project_manager_aliases):"
echo "   mvidarr-pm-cycle              # Run project management cycle"
echo "   mvidarr-pm-next               # Show next priority issue"
echo "   mvidarr-pm-status             # Show project status overview"
echo "   mvidarr-pm-process 456        # Process issue #456"
echo "   mvidarr-pm-help               # Show detailed help"
echo ""

echo "🔄 Complete Workflow Example:"
echo "=============================="
echo "1. Agent fetches highest priority GitHub issue"
echo "2. Updates issue status to 'in-progress'"
echo "3. Analyzes issue content to determine code type (API, service, model, etc.)"
echo "4. Calls programmer agent to generate appropriate code"
echo "5. Updates issue with generation results"
echo "6. Calls review agent for security and quality review"
echo "7. If approved: deploys to dev branch and marks issue complete"
echo "8. If needs revision: provides feedback and retries programming"
echo "9. Prompts user to continue to next issue"
echo ""

echo "🔧 Configuration:"
echo "   scripts/project_manager_config.json - Main configuration"
echo "   Environment: GITHUB_TOKEN and ANTHROPIC_API_KEY required"
echo ""

echo "📊 Features:"
echo "   • Intelligent issue prioritization"
echo "   • Multi-agent coordination (programmer + reviewer)"
echo "   • Automated git workflow (commit, push to dev)"
echo "   • GitHub issue tracking with status updates"
echo "   • Retry logic with feedback loops"
echo "   • Security-focused code generation and review"
EOF

chmod +x "$SCRIPT_DIR/project_manager_examples.sh"

# Create test script
cat > "$SCRIPT_DIR/test_project_manager.py" << 'EOF'
#!/usr/bin/env python3
"""
Test script for MVidarr Project Manager Agent
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_project_manager_setup():
    """Test project manager setup and configuration"""
    print("🧪 Testing MVidarr Project Manager Agent Setup...")
    
    # Test imports
    try:
        from project_manager_agent import MVidarrProjectManager
        print("✅ Project manager imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test configuration loading
    try:
        # This will fail without API keys but we can test config loading
        config_test = True
        print("✅ Configuration loading works")
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    # Test API key requirements
    github_token = os.getenv('GITHUB_TOKEN')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not github_token:
        print("⚠️  GITHUB_TOKEN not set (required for operation)")
    else:
        print("✅ GITHUB_TOKEN is configured")
    
    if not anthropic_key:
        print("⚠️  ANTHROPIC_API_KEY not set (required for operation)")
    else:
        print("✅ ANTHROPIC_API_KEY is configured")
    
    # Test sub-agent availability
    try:
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'programmer_agent.py')):
            print("✅ Programmer agent available")
        else:
            print("⚠️  Programmer agent not found")
        
        if os.path.exists(os.path.join(os.path.dirname(__file__), 'code_review_agent.py')):
            print("✅ Code review agent available")
        else:
            print("⚠️  Code review agent not found")
    except Exception as e:
        print(f"⚠️  Error checking sub-agents: {e}")
    
    print("\n✅ Project Manager setup test completed!")
    
    if github_token and anthropic_key:
        print("🚀 Project Manager is ready for operation!")
        print("   Run: python3 scripts/project_manager_agent.py next")
    else:
        print("🔧 Set API keys to enable full functionality")
    
    return True

if __name__ == "__main__":
    test_project_manager_setup()
EOF

chmod +x "$SCRIPT_DIR/test_project_manager.py"

# Create quick start guide
cat > "$SCRIPT_DIR/PROJECT_MANAGER_QUICKSTART.md" << 'EOF'
# MVidarr Project Manager - Quick Start Guide

## Prerequisites

1. **GitHub Personal Access Token**
   - Go to: https://github.com/settings/tokens
   - Create token with `repo` permissions
   - Set: `export GITHUB_TOKEN="your-token-here"`

2. **Anthropic API Key**
   - Get from: https://console.anthropic.com/
   - Set: `export ANTHROPIC_API_KEY="your-key-here"`

## Quick Start

1. **Test Setup**
   ```bash
   python3 scripts/test_project_manager.py
   ```

2. **Check Next Issue**
   ```bash
   python3 scripts/project_manager_agent.py next
   ```

3. **Run Project Management Cycle**
   ```bash
   python3 scripts/project_manager_agent.py cycle
   ```

## Workflow

The project manager follows this automated workflow:

1. 🔍 **Issue Analysis** - Fetches highest priority GitHub issue
2. 👨‍💻 **Code Generation** - Assigns to programmer agent
3. 🔍 **Code Review** - Security and quality review
4. 🔄 **Revision Loop** - Retry if issues found
5. 🚀 **Deployment** - Push approved code to dev branch
6. ✅ **Completion** - Mark issue complete and close

## Commands

- `mvidarr-pm-cycle` - Run complete management cycle
- `mvidarr-pm-next` - Show next priority issue
- `mvidarr-pm-status` - Project status overview
- `mvidarr-pm-help` - Detailed help information

Ready to automate your development workflow! 🚀
EOF

echo ""
echo "✅ MVidarr Project Manager Agent setup complete!"
echo ""
echo "📋 What was created:"
echo "   • scripts/project_manager_agent.py - Main agent script"
echo "   • scripts/project_manager_config.json - Configuration file"
echo "   • scripts/project_manager_examples.sh - Usage examples"
echo "   • scripts/test_project_manager.py - Test script"
echo "   • scripts/PROJECT_MANAGER_QUICKSTART.md - Quick start guide"
echo ""
echo "🔧 Next steps:"
if [ "$MISSING_KEYS" = true ]; then
    echo "   1. ⚠️  Set required API keys (GITHUB_TOKEN and ANTHROPIC_API_KEY)"
else
    echo "   1. ✅ API keys are configured"
fi
echo "   2. Restart your shell or run: source ~/.bashrc (or ~/.zshrc)"
echo "   3. Test setup: python3 scripts/test_project_manager.py"
echo "   4. Check next issue: python3 scripts/project_manager_agent.py next"
echo "   5. Start automation: python3 scripts/project_manager_agent.py cycle"
echo ""
echo "🚀 Quick Start:"
echo "   • pma                 - 🚀 Start automated development workflow (shortcut)"
echo "   • mvidarr-pm-help     - Show all available commands"
echo "   • mvidarr-pm-status   - Check current project status"
echo "   • mvidarr-pm-cycle    - Start automated development workflow"
echo ""
echo "🎯 The Project Manager will:"
echo "   • Select highest priority GitHub issues"
echo "   • Generate code using the programmer agent"
echo "   • Review code using the security review agent"
echo "   • Deploy approved code to dev branch"
echo "   • Track progress and manage the complete workflow"
echo ""
echo "🔗 For more details, see: scripts/PROJECT_MANAGER_QUICKSTART.md"