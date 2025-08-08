# API Performance Monitoring

## Overview

MVidarr now includes comprehensive API performance monitoring to identify bottlenecks and optimize response times. This system provides real-time monitoring, statistics collection, and performance analysis for critical API endpoints.

## Features

### 🔍 **Automatic Performance Tracking**
- Response time measurement for all monitored endpoints
- Automatic logging of slow responses (>500ms and >1s)
- Thread-safe statistics collection
- Memory-efficient rolling window of recent measurements

### 📊 **Performance Statistics**
- Average, minimum, and maximum response times
- Request count tracking
- Identification of slow endpoints
- Historical performance data

### 🚨 **Performance Alerts**
- Automatic logging of slow API responses
- Configurable thresholds for performance warnings
- Real-time detection of performance degradation

## API Endpoints

### Performance Statistics
- `GET /api/performance/stats` - Comprehensive performance statistics
- `GET /api/performance/slow?threshold=500` - Endpoints slower than threshold (ms)
- `GET /api/performance/summary` - Concise performance summary with recommendations
- `POST /api/performance/log-summary` - Manually trigger performance logging
- `GET /api/performance/health` - Performance monitoring health check

## Monitored Endpoints

The following critical endpoints are currently monitored:

### Videos API
- `api.videos.list` - Main video listing endpoint
- `api.videos.search` - Video search with filters
- `api.videos.universal_search` - Universal search across all content

### Artists API
- `api.artists.list` - Artist listing with search/filtering
- `api.artists.advanced_search` - Advanced artist search

### Settings API
- `api.settings.get_all` - Application settings retrieval

## Usage Examples

### Check Overall Performance
```bash
curl http://localhost:5001/api/performance/summary
```

### Find Slow Endpoints
```bash
# Get endpoints slower than 300ms
curl "http://localhost:5001/api/performance/slow?threshold=300"
```

### Get Detailed Statistics
```bash
curl http://localhost:5001/api/performance/stats
```

## Implementation Details

### Performance Decorator
```python
from src.utils.performance_monitor import monitor_performance

@monitor_performance("api.custom.endpoint")
def my_api_endpoint():
    # Your endpoint implementation
    pass
```

### Manual Performance Tracking
```python
from src.utils.performance_monitor import perf_stats

# Record response time manually
perf_stats.record_time("custom.operation", 0.250)  # 250ms

# Get statistics
stats = perf_stats.get_stats("custom.operation")
```

## Performance Targets

Based on issue #68 requirements:

- **Search APIs**: Target <500ms response time
- **Core APIs**: Target <200ms response time  
- **Critical Operations**: Monitor for >1s responses

## Logging Levels

- **Debug**: All API responses with timing
- **Info**: Responses taking 500ms-1s
- **Warning**: Responses taking >1s
- **Error**: Performance system errors

## Data Collection

- **Rolling Window**: Last 100 requests per endpoint (memory efficient)
- **Thread Safe**: Concurrent request handling
- **Automatic Cleanup**: Prevents memory bloat
- **Real-time**: Immediate statistics availability

## Benefits

1. **Proactive Issue Detection**: Identify slow endpoints before users complain
2. **Performance Optimization Guidance**: Data-driven optimization decisions  
3. **Regression Prevention**: Monitor performance changes over time
4. **User Experience Improvement**: Focus optimization efforts on high-impact areas

## Integration

The performance monitoring system integrates with:

- **Database Optimization** (#67): Coordinate query optimizations
- **Frontend Performance** (#69): API improvements enhance user experience
- **Logging System**: Performance data in application logs
- **Health Monitoring**: Performance health checks

## Next Steps

1. **Expand Coverage**: Add monitoring to more API endpoints
2. **Performance Alerts**: Implement alerting for degraded performance
3. **Historical Analysis**: Store long-term performance trends
4. **Optimization Recommendations**: Automated performance improvement suggestions

## Critical Analysis

This implementation addresses the core issues with issue #68:

- ✅ **Provides Baseline Data**: Real performance measurements vs assumptions
- ✅ **Focused Approach**: Start with critical endpoints, expand systematically  
- ✅ **Evidence-Based Targets**: Use real data to set realistic performance goals
- ✅ **Root Cause Analysis**: Identify actual bottlenecks vs perceived issues

The system provides the foundation for data-driven API optimization rather than premature optimization based on assumptions.