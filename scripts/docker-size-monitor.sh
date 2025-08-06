#!/bin/bash
# Docker Image Size Monitoring and Validation Tool
# Tracks image size changes and validates optimization targets

set -e

# Configuration
TARGET_SIZE_GB=1.5  # Adjusted based on current optimized build size
WARNING_SIZE_GB=1.8  # Critical threshold for size regression alerts
IMAGE_NAME="${1:-ghcr.io/prefect421/mvidarr}"
TAG="${2:-dev}"
FULL_IMAGE="${IMAGE_NAME}:${TAG}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 MVidarr Docker Image Size Monitor${NC}"
echo "=========================================="

# Pull latest image
echo -e "${BLUE}📥 Pulling latest image: ${FULL_IMAGE}${NC}"
docker pull "${FULL_IMAGE}" --quiet

# Get image size
SIZE_RAW=$(docker images --format "{{.Size}}" "${FULL_IMAGE}")
SIZE_INFO=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" "${FULL_IMAGE}" | tail -n1)

echo -e "${BLUE}📊 Current Image Analysis${NC}"
echo "$SIZE_INFO"

# Convert size to comparable format
if [[ $SIZE_RAW == *"GB"* ]]; then
    SIZE_GB=$(echo $SIZE_RAW | sed 's/GB//')
    SIZE_MB=$(echo "$SIZE_GB * 1024" | bc)
elif [[ $SIZE_RAW == *"MB"* ]]; then
    SIZE_MB=$(echo $SIZE_RAW | sed 's/MB//')
    SIZE_GB=$(echo "scale=2; $SIZE_MB / 1024" | bc)
else
    echo -e "${RED}❌ Cannot parse image size: $SIZE_RAW${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🎯 Size Validation${NC}"
echo "Current size: ${SIZE_GB}GB (${SIZE_MB}MB)"
echo "Target size: ${TARGET_SIZE_GB}GB"
echo "Warning threshold: ${WARNING_SIZE_GB}GB"

# Validate against targets
if (( $(echo "$SIZE_GB < $TARGET_SIZE_GB" | bc -l) )); then
    echo -e "${GREEN}✅ SUCCESS: Image size is under target (${TARGET_SIZE_GB}GB)${NC}"
    EXIT_CODE=0
elif (( $(echo "$SIZE_GB < $WARNING_SIZE_GB" | bc -l) )); then
    echo -e "${YELLOW}⚠️  WARNING: Image size is above target but under warning threshold${NC}"
    echo -e "${YELLOW}   Consider further optimization to reach <${TARGET_SIZE_GB}GB target${NC}"
    EXIT_CODE=1
else
    echo -e "${RED}❌ CRITICAL: Image size exceeds warning threshold (${WARNING_SIZE_GB}GB)${NC}"
    echo -e "${RED}   Immediate optimization required${NC}"
    EXIT_CODE=2
fi

# Layer analysis
echo ""
echo -e "${BLUE}🔍 Layer Analysis (Top 10 largest layers)${NC}"
docker history "$FULL_IMAGE" --format "table {{.Size}}\t{{.CreatedBy}}" --human | head -11

# Historical comparison if data exists
HISTORY_FILE="/tmp/mvidarr-size-history.txt"
CURRENT_TIMESTAMP=$(date +%s)
echo "${CURRENT_TIMESTAMP},${TAG},${SIZE_GB},${SIZE_MB}" >> "$HISTORY_FILE"

echo ""
echo -e "${BLUE}📈 Size History (Last 5 measurements)${NC}"
if [[ -f "$HISTORY_FILE" ]]; then
    echo "Timestamp,Tag,Size(GB),Size(MB)"
    tail -5 "$HISTORY_FILE" | while read line; do
        TIMESTAMP=$(echo "$line" | cut -d',' -f1)
        TAG_HIST=$(echo "$line" | cut -d',' -f2)
        SIZE_GB_HIST=$(echo "$line" | cut -d',' -f3)
        SIZE_MB_HIST=$(echo "$line" | cut -d',' -f4)
        DATE_HIST=$(date -d "@$TIMESTAMP" "+%Y-%m-%d %H:%M")
        echo "$DATE_HIST,$TAG_HIST,${SIZE_GB_HIST}GB,${SIZE_MB_HIST}MB"
    done
else
    echo "No historical data available yet"
fi

# Optimization suggestions  
echo ""
echo -e "${BLUE}💡 Optimization Suggestions${NC}"
if (( $(echo "$SIZE_GB > 1.6" | bc -l) )); then
    echo "🚨 CRITICAL: Investigate significant size regression"
    echo "🔧 Check for new heavy dependencies in requirements-prod.txt"
    echo "🔧 Verify .dockerignore is excluding development files"
    echo "🔧 Review recent changes for build bloat"
elif (( $(echo "$SIZE_GB > 1.4" | bc -l) )); then
    echo "⚠️  MONITORING: Size above target but within acceptable range"
    echo "🔧 Monitor for continued growth trend"
    echo "🔧 Consider dependency audit if trend continues"
    echo "🔧 Review heavy packages: opencv (~150MB), moviepy (~100MB)"
else
    echo "🎉 Image size is optimal! Build reliability maintained."
    echo "✅ Continue monitoring for regressions"
fi

echo ""
echo -e "${BLUE}🏁 Monitoring Complete${NC}"
exit $EXIT_CODE