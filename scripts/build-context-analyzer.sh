#!/bin/bash
# Docker Build Context Analysis Tool
# Analyzes what files are included in Docker build context

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 MVidarr Build Context Analyzer${NC}"
echo "========================================"

# Get build context size
echo -e "${BLUE}📊 Build Context Analysis${NC}"
TOTAL_SIZE=$(du -sh . --exclude=data 2>/dev/null | cut -f1)
echo "Total context size (excluding data/): $TOTAL_SIZE"

echo ""
echo -e "${BLUE}📁 Top 10 Largest Directories${NC}"
du -sh */ 2>/dev/null | grep -v "data/" | sort -hr | head -10

echo ""
echo -e "${BLUE}🔍 Large Files (>10MB) in Build Context${NC}"
find . -name "data" -prune -o -type f -size +10M -exec ls -lh {} \; 2>/dev/null | grep -v "data/" | head -20 || echo "No large files found"

echo ""
echo -e "${BLUE}📋 .dockerignore Effectiveness Check${NC}"

# Check if common bloat sources are properly excluded
BLOAT_SOURCES=(
    "venv/"
    "pdf_env/"
    "screenshot_env/" 
    "docs/"
    "tests/"
    "*.pyc"
    "__pycache__"
    ".git/"
    "comprehensive-security-scan-*"
)

echo "Checking exclusion of common bloat sources:"
for source in "${BLOAT_SOURCES[@]}"; do
    if [[ -e "$source" ]] || find . -path "./$source" -o -name "$source" 2>/dev/null | grep -q .; then
        if grep -q "$source" .dockerignore 2>/dev/null; then
            echo -e "✅ $source - Excluded by .dockerignore"
        else
            echo -e "${RED}❌ $source - EXISTS but NOT excluded!${NC}"
        fi
    else
        echo -e "ℹ️  $source - Not present"
    fi
done

echo ""
echo -e "${BLUE}🚨 Potential Build Context Issues${NC}"

# Check for files that should be excluded
echo "Scanning for files that should potentially be excluded:"

# Check for backup files
BACKUP_COUNT=$(find . -name "*.backup" -o -name "*.bak" -o -name "*.old" 2>/dev/null | wc -l)
if [[ $BACKUP_COUNT -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Found $BACKUP_COUNT backup files${NC}"
    find . -name "*.backup" -o -name "*.bak" -o -name "*.old" 2>/dev/null | head -5
fi

# Check for temp files  
TEMP_COUNT=$(find . -name "*.tmp" -o -name "*.temp" -o -name ".DS_Store" 2>/dev/null | wc -l)
if [[ $TEMP_COUNT -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Found $TEMP_COUNT temporary files${NC}"
    find . -name "*.tmp" -o -name "*.temp" -o -name ".DS_Store" 2>/dev/null | head -5
fi

# Check for large log files
LOG_COUNT=$(find . -name "*.log" -size +1M 2>/dev/null | wc -l)  
if [[ $LOG_COUNT -gt 0 ]]; then
    echo -e "${YELLOW}⚠️  Found $LOG_COUNT large log files${NC}"
    find . -name "*.log" -size +1M -exec ls -lh {} \; 2>/dev/null | head -5
fi

echo ""
echo -e "${BLUE}📈 Build Context Health Score${NC}"

# Calculate health score based on size and exclusions
SCORE=100
if [[ $TOTAL_SIZE == *"G"* ]]; then
    SIZE_NUM=$(echo $TOTAL_SIZE | sed 's/G//')
    if command -v bc >/dev/null && (( $(echo "$SIZE_NUM > 2" | bc -l) )); then
        SCORE=$((SCORE - 30))
        echo -e "${RED}❌ Context too large (>2GB): -30 points${NC}"
    elif command -v bc >/dev/null && (( $(echo "$SIZE_NUM > 1" | bc -l) )); then
        SCORE=$((SCORE - 15))  
        echo -e "${YELLOW}⚠️  Context large (>1GB): -15 points${NC}"
    fi
fi

if [[ $BACKUP_COUNT -gt 0 ]]; then
    SCORE=$((SCORE - 10))
    echo -e "${YELLOW}⚠️  Backup files present: -10 points${NC}"
fi

if [[ $TEMP_COUNT -gt 0 ]]; then
    SCORE=$((SCORE - 5))
    echo -e "${YELLOW}⚠️  Temp files present: -5 points${NC}"
fi

if [[ $LOG_COUNT -gt 0 ]]; then
    SCORE=$((SCORE - 10))
    echo -e "${YELLOW}⚠️  Large log files present: -10 points${NC}"
fi

echo ""
if [[ $SCORE -ge 90 ]]; then
    echo -e "${GREEN}🎉 Build Context Health Score: $SCORE/100 - EXCELLENT${NC}"
elif [[ $SCORE -ge 75 ]]; then
    echo -e "${YELLOW}✅ Build Context Health Score: $SCORE/100 - GOOD${NC}" 
elif [[ $SCORE -ge 50 ]]; then
    echo -e "${YELLOW}⚠️  Build Context Health Score: $SCORE/100 - NEEDS IMPROVEMENT${NC}"
else
    echo -e "${RED}❌ Build Context Health Score: $SCORE/100 - CRITICAL${NC}"
fi

echo ""
echo -e "${BLUE}💡 Recommendations${NC}"
if [[ $SCORE -ge 90 ]]; then
    echo "✅ Build context is well-optimized"
    echo "🔍 Continue monitoring for regressions"
else
    echo "🔧 Update .dockerignore to exclude identified bloat sources"
    echo "🧹 Clean up temporary and backup files"
    echo "📊 Re-run analysis after cleanup"
fi

echo ""
echo -e "${BLUE}🏁 Analysis Complete${NC}"

# Return appropriate exit code
if [[ $SCORE -ge 75 ]]; then
    exit 0
else
    exit 1  
fi