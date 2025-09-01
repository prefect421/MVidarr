# Metadata Enrichment Service Refactoring Plan

## Problem Statement

The current metadata enrichment service is making **synchronous blocking network calls inside async functions**, causing the process to hang indefinitely when external APIs are slow or unresponsive. This results in:

- Video cards stuck on "Enriching metadata..." state
- Failed lyrics and thumbnail downloads  
- Poor user experience with no feedback
- Potential resource exhaustion from hanging connections

## Root Cause Analysis

### Critical Issues Identified:

1. **Blocking Network Calls in Async Context**
   - All `_get_*_metadata()` functions use synchronous HTTP requests
   - Spotify, Last.fm, MusicBrainz, AllMusic, Wikipedia calls are blocking
   - No proper async HTTP session management

2. **Database Session Management**
   - Long-lived database sessions during network operations
   - Potential connection timeouts and deadlocks
   - Sessions kept open while making external API calls

3. **No Rate Limiting Between Services**
   - Rate limiting only exists for bulk operations
   - Individual enrichment calls hit all services simultaneously
   - No circuit breaker pattern for failing services

4. **Insufficient Error Handling**
   - Silent failures in external service calls
   - No graceful degradation when services are unavailable
   - Limited timeout controls

## Long-Term Refactoring Plan

### Phase 1: Core Infrastructure Changes (High Priority)

#### 1.1 Convert HTTP Clients to Async
- [x] **Refactor Spotify Service** (`src/services/spotify_service.py`) ✅ COMPLETED
  - ✅ Replace `requests` with `aiohttp` 
  - ✅ Make all methods async (`async def`)
  - ✅ Implement proper connection pooling
  - ✅ Add per-request timeouts (5-10 seconds)
  - ✅ File: `src/services/async_spotify_service.py`
  - ✅ Update metadata enrichment service to use async Spotify
  - ✅ Add circuit breaker and retry logic via async HTTP client

- [ ] **Refactor Last.fm Service** (`src/services/lastfm_service.py`)
  - Convert to async HTTP client
  - Add request timeouts and retry logic
  - Implement rate limiting (1 request/second)
  - File: `src/services/async_lastfm_service.py`

- [ ] **Refactor MusicBrainz Service** (`src/services/musicbrainz_service.py`)
  - Convert to async with proper MusicBrainz rate limits (1 request/second)
  - Add User-Agent headers as required by MusicBrainz
  - Implement exponential backoff for rate limit errors
  - File: `src/services/async_musicbrainz_service.py`

- [ ] **Refactor AllMusic Service** (`src/services/allmusic_service.py`)
  - Convert scraping logic to async
  - Add proper timeout handling for web scraping
  - Implement circuit breaker for repeated failures
  - File: `src/services/async_allmusic_service.py`

- [ ] **Refactor Wikipedia Service** (`src/services/wikipedia_service.py`)
  - Convert to async Wikipedia API calls
  - Add image download async functionality
  - Implement proper error handling for missing pages
  - File: `src/services/async_wikipedia_service.py`

#### 1.2 Create Async HTTP Session Manager
- [x] **HTTP Session Management** (`src/utils/async_http_client.py`) ✅ COMPLETED
  - ✅ Centralized `aiohttp.ClientSession` management
  - ✅ Connection pooling and timeout configuration
  - ✅ Automatic retry logic with exponential backoff
  - ✅ Request/response logging for debugging
  - ✅ Circuit breaker pattern implementation

```python
# Example structure:
class AsyncHttpClient:
    async def __init__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30, connect=10),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=10)
        )
    
    async def get_with_retry(self, url, max_retries=3, backoff_factor=1.0):
        # Implementation with exponential backoff
        pass
```

#### 1.3 Database Session Optimization
- [ ] **Async Database Operations** (`src/database/async_db.py`)
  - Create async database session manager
  - Implement context managers for proper session lifecycle
  - Add connection pooling for async operations
  - Separate database operations from network calls

### Phase 2: Service Integration Layer (Medium Priority)

#### 2.1 Service Coordination and Orchestration
- [ ] **Async Service Coordinator** (`src/services/async_enrichment_coordinator.py`)
  - Coordinate calls to multiple services concurrently
  - Implement service priority and fallback logic
  - Add comprehensive error aggregation
  - Service health monitoring and circuit breaking

- [ ] **Progress Tracking System** (`src/services/enrichment_progress.py`)
  - Real-time progress updates for frontend
  - WebSocket or Server-Sent Events for live updates
  - Track individual service completion status
  - Provide detailed error reporting per service

#### 2.2 Caching and Performance
- [ ] **Async Caching Layer** (`src/utils/async_cache.py`)
  - Redis-based async caching for external API responses
  - Cache metadata results to reduce API calls
  - Implement cache invalidation strategies
  - Add cache warming for popular artists

- [ ] **Request Deduplication** (`src/utils/request_deduplication.py`)
  - Prevent multiple simultaneous requests for same resource
  - Implement request coalescing for concurrent enrichment
  - Add request queuing and batching

### Phase 3: Enhanced Error Handling and Resilience (Medium Priority)

#### 3.1 Circuit Breaker and Fallback Patterns
- [ ] **Service Circuit Breaker** (`src/utils/circuit_breaker.py`)
  - Monitor service health and failure rates
  - Automatic service isolation when failing
  - Configurable failure thresholds and recovery timers
  - Fallback to cached data when services are down

- [ ] **Graceful Degradation** (`src/services/fallback_strategies.py`)
  - Define fallback strategies for each service
  - Partial enrichment when some services fail
  - Priority-based service execution
  - Local fallback data sources

#### 3.2 Comprehensive Error Handling
- [ ] **Error Classification and Recovery** (`src/utils/error_handling.py`)
  - Classify errors (temporary, permanent, rate-limited)
  - Implement appropriate retry strategies per error type
  - Add structured logging for debugging
  - User-friendly error messages

### Phase 4: Background Processing and Queuing (Low Priority)

#### 4.1 Task Queue Implementation
- [ ] **Async Task Queue** (`src/services/task_queue.py`)
  - Implement Celery or RQ for background processing
  - Move heavy enrichment tasks to background workers
  - Add job status tracking and progress updates
  - Priority queuing for different enrichment types

- [ ] **Batch Processing Optimization** (`src/services/batch_enrichment.py`)
  - Optimize bulk enrichment operations
  - Implement intelligent batching strategies
  - Add parallel processing for bulk operations
  - Resource usage optimization

#### 4.2 Monitoring and Observability
- [ ] **Metrics and Monitoring** (`src/utils/metrics.py`)
  - Service response time tracking
  - Error rate monitoring per service
  - Success rate metrics and alerting
  - Resource usage monitoring

- [ ] **Health Checks** (`src/api/health.py`)
  - Service availability endpoints
  - Dependency health monitoring
  - Automated service recovery procedures
  - Status dashboard for administrators

### Phase 5: Configuration and Deployment (Low Priority)

#### 5.1 Configuration Management
- [ ] **Service Configuration** (`src/config/enrichment_config.py`)
  - Centralized configuration for all services
  - Environment-specific settings
  - Runtime configuration updates
  - Service enable/disable flags

- [ ] **Rate Limiting Configuration** (`src/config/rate_limits.py`)
  - Per-service rate limiting configuration
  - Dynamic rate limit adjustment
  - User-based rate limiting
  - API quota management

#### 5.2 Testing and Validation
- [ ] **Async Testing Framework** (`tests/test_async_enrichment.py`)
  - Comprehensive async service testing
  - Mock external API responses
  - Performance benchmarking tests
  - Error scenario testing

- [ ] **Integration Testing** (`tests/integration/test_enrichment_flow.py`)
  - End-to-end enrichment workflow testing
  - Service failure simulation
  - Load testing for concurrent operations
  - Data consistency validation

## Implementation Strategy

### Approach 1: Incremental Migration (Recommended)
1. Implement async versions alongside existing sync services
2. Add feature flags to switch between sync/async modes
3. Gradual rollout with fallback to sync implementation
4. Monitor performance and stability before full migration

### Approach 2: Big Bang Migration (Higher Risk)
1. Refactor all services simultaneously
2. Extensive testing in development environment
3. Coordinated deployment with rollback plan
4. Higher risk but faster completion

## Estimated Timeline

### Phase 1 (Core Infrastructure): 2-3 weeks
- Most critical for fixing the hanging issue
- Directly addresses the blocking call problem
- Provides immediate user experience improvements

### Phase 2 (Service Integration): 1-2 weeks
- Enhances performance and user feedback
- Adds professional polish to the feature
- Improves system reliability

### Phase 3 (Error Handling): 1-2 weeks
- Increases system resilience
- Reduces support burden
- Improves production stability

### Phase 4 (Background Processing): 2-3 weeks
- Optimizes resource usage
- Scales for larger deployments
- Adds enterprise-level features

### Phase 5 (Configuration/Deployment): 1 week
- Improves maintainability
- Adds operational excellence
- Facilitates monitoring and debugging

**Total Estimated Time: 7-11 weeks**

## Success Metrics

### Performance Metrics
- [ ] Metadata enrichment completion time < 30 seconds (95th percentile)
- [ ] Zero indefinitely hanging operations
- [ ] > 95% success rate for enrichment operations
- [ ] < 5% timeout rate under normal conditions

### User Experience Metrics
- [ ] Real-time progress feedback during enrichment
- [ ] Clear error messages when services fail
- [ ] Graceful degradation with partial results
- [ ] Consistent UI behavior regardless of service status

### System Reliability Metrics
- [ ] > 99.5% service availability
- [ ] < 1% unhandled exceptions
- [ ] Automatic recovery from transient failures
- [ ] Comprehensive error logging and alerting

## Risk Assessment

### High Risk Items
- **Service API Changes**: External services may change their APIs
- **Rate Limiting**: May trigger rate limiting during migration testing
- **Data Consistency**: Ensure enrichment results remain consistent
- **Performance Regression**: Async conversion might initially be slower

### Mitigation Strategies
- Implement comprehensive testing with service mocks
- Gradual rollout with feature flags
- Extensive monitoring during migration
- Keep sync fallback available during transition

## Dependencies and Prerequisites

### External Dependencies
- ✅ `aiohttp==3.10.11` - Async HTTP client library (ADDED to requirements.txt)
- ✅ `asyncio` - Python async runtime (built-in)
- `redis` - For caching and request deduplication (optional - Phase 2)
- `celery` or `rq` - For background task processing (Phase 4)

### Internal Prerequisites
- Database migration to support async operations
- Configuration management updates
- Monitoring infrastructure setup
- Testing framework enhancements

## Conclusion

This refactoring plan addresses the core issue of blocking network calls while building a robust, scalable metadata enrichment system. The phased approach allows for incremental improvements while maintaining system stability.

**Immediate Priority**: Focus on Phase 1 to fix the hanging issue and provide immediate user experience improvements. This will resolve the "Enriching metadata..." stuck state and enable proper lyrics/thumbnail downloads.

The subsequent phases build upon this foundation to create an enterprise-grade enrichment system with proper error handling, monitoring, and scalability features.