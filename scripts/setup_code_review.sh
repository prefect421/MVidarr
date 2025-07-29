#!/bin/bash

# MVidarr Code Review Agent Setup Script
# Sets up the Claude-powered code review agent for security analysis

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🔧 Setting up MVidarr Code Review Agent..."

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

# Install required Python packages
echo "📦 Installing required Python packages..."
pip3 install --user requests

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  ANTHROPIC_API_KEY environment variable not set"
    echo "   You can set it by adding this to your ~/.bashrc or ~/.zshrc:"
    echo "   export ANTHROPIC_API_KEY='your-api-key-here'"
    echo ""
    echo "   Or provide it via --api-key when running the agent"
fi

# Make scripts executable
chmod +x "$SCRIPT_DIR/code_review_agent.py"

# Create alias for easy usage
ALIAS_FILE="$HOME/.mvidarr_aliases"
cat > "$ALIAS_FILE" << 'EOF'
# MVidarr Code Review Agent Aliases
alias mvidarr-review-diff='python3 ~/mvidarr/scripts/code_review_agent.py diff'
alias mvidarr-review-staged='python3 ~/mvidarr/scripts/code_review_agent.py staged'
alias mvidarr-review-files='python3 ~/mvidarr/scripts/code_review_agent.py files'
EOF

# Source the aliases in shell config files
for shell_config in ~/.bashrc ~/.zshrc; do
    if [ -f "$shell_config" ]; then
        if ! grep -q "source $ALIAS_FILE" "$shell_config"; then
            echo "source $ALIAS_FILE" >> "$shell_config"
            echo "✅ Added aliases to $shell_config"
        fi
    fi
done

# Create sample usage script
cat > "$SCRIPT_DIR/example_usage.sh" << 'EOF'
#!/bin/bash

# Example usage of MVidarr Code Review Agent

echo "🔍 MVidarr Code Review Agent - Example Usage"
echo ""

echo "1. Review changes against main branch:"
echo "   python3 scripts/code_review_agent.py diff --target-branch main"
echo ""

echo "2. Review staged changes:"
echo "   python3 scripts/code_review_agent.py staged"
echo ""

echo "3. Review specific files:"
echo "   python3 scripts/code_review_agent.py files --files src/api/auth.py src/utils/security.py"
echo ""

echo "4. Save review to file:"
echo "   python3 scripts/code_review_agent.py diff --output review_$(date +%Y%m%d_%H%M%S).md"
echo ""

echo "5. Using aliases (after sourcing ~/.mvidarr_aliases):"
echo "   mvidarr-review-diff"
echo "   mvidarr-review-staged"
echo "   mvidarr-review-files --files src/security_config.py"
EOF

chmod +x "$SCRIPT_DIR/example_usage.sh"

echo ""
echo "✅ MVidarr Code Review Agent setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Set your ANTHROPIC_API_KEY environment variable"
echo "   2. Restart your shell or run: source ~/.bashrc (or ~/.zshrc)"
echo "   3. Test with: python3 scripts/code_review_agent.py --help"
echo ""
echo "📖 Usage examples:"
echo "   • Review current changes: python3 scripts/code_review_agent.py diff"
echo "   • Review staged files: python3 scripts/code_review_agent.py staged"
echo "   • Review specific files: python3 scripts/code_review_agent.py files --files src/api/auth.py"
echo ""
echo "🔗 Configuration file: scripts/code_review_config.json"
echo "📚 Examples script: scripts/example_usage.sh"
echo ""
echo "🔒 Security Focus: This agent is designed for defensive security analysis only"