# TODO: Phase 1 - Async Foundation (Weeks 1-14)
## Complete FastAPI Migration - Phase 1 Task List

**Timeline**: 12-14 weeks (Q1-Q2 2026)  
**Focus**: Blocking I/O optimization and async foundation  
**Goal**: 70% of blocking operations resolved, async database layer complete

---

## 📅 **WEEK 1-3: DATABASE LAYER ASYNC MIGRATION**
**GitHub Issue**: #122 - Database Layer Async Migration

### **Week 1: Database Connection Setup**
- [ ] **Install async database drivers**
  - [ ] Add `aiomysql>=0.2.0` to requirements-fastapi.txt
  - [ ] Remove `pymysql` dependency for FastAPI routes
  - [ ] Update connection strings from `mysql+pymysql://` to `mysql+aiomysql://`
  
- [ ] **Create async engine and session factory**
  - [ ] Create `src/database/async_connection.py`
  - [ ] Implement `AsyncEngine` configuration with proper pool settings
  - [ ] Setup `async_sessionmaker` with session lifecycle management
  - [ ] Add async database dependency injection for FastAPI

- [ ] **Test basic async database connection**
  - [ ] Create test script to verify async connection works
  - [ ] Test connection pool under load
  - [ ] Verify proper session cleanup

### **Week 2: Model Migration** 
- [ ] **Update SQLAlchemy models for async compatibility**
  - [ ] Review all models in `src/database/models.py` for async compatibility
  - [ ] Update relationship loading patterns for async queries
  - [ ] Test model instantiation and basic operations with async sessions
  
- [ ] **Create async base service class**
  - [ ] Create `src/services/async_base_service.py`
  - [ ] Implement common async database operation patterns
  - [ ] Add async context manager support
  - [ ] Create async repository pattern base class

### **Week 3: Service Layer Migration**
- [ ] **Convert core services to async (Priority order)**
  - [ ] `src/services/video_service.py` → async patterns (CRITICAL)
  - [ ] `src/services/artist_service.py` → async patterns  
  - [ ] `src/services/playlist_service.py` → async patterns
  - [ ] `src/services/settings_service.py` → async patterns
  
- [ ] **Update all database queries**
  - [ ] Replace `session.query()` with `session.execute(select())`
  - [ ] Update all `.all()`, `.first()`, `.get()` to async equivalents
  - [ ] Add proper async session management with `async with`
  - [ ] Implement async transaction handling

- [ ] **Create async migration testing**
  - [ ] Create comprehensive test suite for async database operations
  - [ ] Performance comparison tests (sync vs async)
  - [ ] Concurrent operation stress testing

**Week 1-3 Completion Criteria:**
- ✅ All database operations use async patterns
- ✅ Zero SQLAlchemy session binding errors  
- ✅ Performance improvement in database throughput measurable
- ✅ All existing functionality preserved with async equivalents

---

## 📅 **WEEK 4-6: HTTP CLIENT MIGRATION (Quick Wins)**
**Goal**: Replace 60+ blocking HTTP requests - 70% blocking I/O resolved

### **Week 4: External API Client Setup**
- [ ] **Create async HTTP client infrastructure**
  - [ ] Create `src/services/async_http_client.py` 
  - [ ] Implement singleton `httpx.AsyncClient` with connection pooling
  - [ ] Add timeout configuration and retry logic
  - [ ] Implement rate limiting for external APIs

- [ ] **Spotify API migration** (Priority 1 - Most used)
  - [ ] `src/api/metadata_enrichment.py` → Replace requests with httpx
  - [ ] Update all `requests.get(spotify_api_url)` calls
  - [ ] Test Spotify authentication with async client
  - [ ] Verify metadata enrichment works with async API calls

### **Week 5: Music Database APIs**
- [ ] **MusicBrainz API migration**
  - [ ] `src/api/musicbrainz.py` → async client implementation
  - [ ] Replace blocking requests with async httpx calls
  - [ ] Test artist metadata lookup performance
  
- [ ] **Last.fm API migration**  
  - [ ] Update Last.fm integration with async client
  - [ ] Test scrobbling and metadata features
  
- [ ] **IMVDB API migration**
  - [ ] `src/api/videos.py` → async IMVDB calls
  - [ ] Update video metadata enrichment

### **Week 6: System and Health Check APIs**
- [ ] **Internal API calls migration**
  - [ ] `src/api/health.py` → async health check calls
  - [ ] `src/api/admin_interface.py` → async system monitoring
  - [ ] `src/utils/performance_testing.py` → async testing calls

- [ ] **Error handling and monitoring**
  - [ ] Implement async-compatible error handling
  - [ ] Add proper logging for async HTTP operations
  - [ ] Create monitoring for external API response times

**Week 4-6 Completion Criteria:**
- ✅ All external HTTP requests use async httpx client
- ✅ 60+ requests.get/post calls eliminated  
- ✅ API response times improved with concurrent requests
- ✅ No external API timeout errors under normal load

---

## 📅 **WEEK 7-9: AUTHENTICATION SYSTEM MIGRATION**
**GitHub Issue**: #121 - FastAPI Authentication System Migration

### **Week 7: JWT Token System**
- [ ] **JWT infrastructure setup**
  - [ ] Install dependencies: `python-jose[cryptography]`, `passlib[bcrypt]`
  - [ ] Create `src/auth/jwt_handler.py` with token generation/validation
  - [ ] Implement JWT access & refresh token management
  - [ ] Create secure token storage strategy (HttpOnly cookies)

- [ ] **User authentication model updates**
  - [ ] Add JWT-related fields to User model (refresh_token, token_expires)
  - [ ] Create database migration for auth system changes
  - [ ] Implement password hashing with bcrypt

### **Week 8: FastAPI Authentication Endpoints**
- [ ] **Create authentication router**
  - [ ] Create `src/api/fastapi/auth.py` with authentication endpoints
  - [ ] Implement `POST /auth/login` - JWT token generation
  - [ ] Implement `POST /auth/refresh` - Access token refresh
  - [ ] Implement `POST /auth/logout` - Token revocation
  - [ ] Implement `GET /auth/me` - Current user profile

- [ ] **Authentication dependencies**
  - [ ] Create FastAPI dependency injection for auth
  - [ ] Implement `get_current_user()` dependency
  - [ ] Create role-based access control dependencies
  - [ ] Add route protection decorators

### **Week 9: Security and Integration**
- [ ] **Security enhancements**
  - [ ] Implement rate limiting for login attempts
  - [ ] Add security headers (CORS, HSTS, CSP)
  - [ ] Create API key support for integrations
  - [ ] Implement audit logging for authentication events

- [ ] **Migration compatibility**
  - [ ] Create dual authentication support (Flask sessions + JWT)
  - [ ] Session-to-JWT conversion utility
  - [ ] Backward compatibility layer for existing clients
  - [ ] Testing suite for authentication flows

**Week 7-9 Completion Criteria:**
- ✅ JWT authentication system fully operational
- ✅ All FastAPI routes protected with JWT dependencies
- ✅ Zero security regressions verified
- ✅ Backward compatibility maintained during migration

---

## 📅 **WEEK 10-12: SYSTEM COMMANDS OPTIMIZATION**
**Goal**: Optimize 20+ subprocess calls with thread pools

### **Week 10: Thread Pool Infrastructure**
- [ ] **Create async subprocess wrapper**
  - [ ] Create `src/utils/async_subprocess.py`
  - [ ] Implement `ThreadPoolExecutor` wrapper for subprocess calls
  - [ ] Add timeout and error handling for system commands
  - [ ] Create logging for subprocess operations

- [ ] **Health check system commands**
  - [ ] `src/api/health.py` → thread pool subprocess calls
  - [ ] System service status checks (systemctl, netstat)
  - [ ] Resource monitoring commands (df, free, ps)

### **Week 11: Admin and Management Commands**
- [ ] **Administrative subprocess calls**
  - [ ] `src/api/admin_interface.py` → async subprocess wrappers
  - [ ] Service restart commands → thread pool execution
  - [ ] System maintenance scripts → background execution
  - [ ] Log file operations → async file I/O

- [ ] **Settings and configuration commands**
  - [ ] `src/api/settings.py` → async system command calls
  - [ ] Configuration file updates → async file operations
  - [ ] Service reload operations → non-blocking execution

### **Week 12: Testing and Optimization**
- [ ] **Performance testing**
  - [ ] Load testing of async subprocess operations
  - [ ] Concurrent system command execution testing
  - [ ] Resource usage monitoring under load

- [ ] **Error handling and monitoring**
  - [ ] Implement proper async subprocess error handling
  - [ ] Add monitoring for system command performance
  - [ ] Create alerts for system command failures

**Week 10-12 Completion Criteria:**
- ✅ All system commands execute via thread pools
- ✅ Zero blocking subprocess calls in request handlers
- ✅ System commands can execute concurrently
- ✅ Proper error handling and monitoring in place

---

## 📅 **WEEK 13-14: CORE API MIGRATION FOUNDATION**
**GitHub Issue**: #120 - FastAPI Complete API Migration - Phase 2

### **Week 13: API Infrastructure Setup**
- [ ] **Pydantic models foundation**
  - [ ] Create `src/models/pydantic/` directory structure
  - [ ] Implement base Pydantic models for common entities
  - [ ] Create request/response models for core endpoints
  - [ ] Add validation rules and error handling

- [ ] **Error handling system**
  - [ ] Create `src/api/fastapi/exceptions.py`
  - [ ] Implement structured exception handlers
  - [ ] Create consistent error response format
  - [ ] Add HTTP status code management

### **Week 14: Core Endpoint Migration**
- [ ] **Settings API migration (lowest risk)**
  - [ ] Migrate `src/api/settings.py` core endpoints to FastAPI
  - [ ] Implement Pydantic validation for settings
  - [ ] Test settings CRUD operations with async database
  
- [ ] **Basic video API endpoints**
  - [ ] Migrate simple video listing endpoints
  - [ ] Implement video search with async database
  - [ ] Test video metadata retrieval performance

- [ ] **Testing and validation**
  - [ ] Create comprehensive test suite for migrated endpoints
  - [ ] Performance benchmarking vs Flask equivalents
  - [ ] Verify API contracts maintained

**Week 13-14 Completion Criteria:**
- ✅ Core API infrastructure established with Pydantic
- ✅ First FastAPI endpoints operational and tested
- ✅ Error handling system functional
- ✅ Performance improvements measurable vs Flask

---

## 🎯 **PHASE 1 SUCCESS METRICS**

### **Blocking I/O Resolution**
- ✅ **Database operations**: 100% async (0 blocking SQLAlchemy calls)
- ✅ **HTTP requests**: 60+ requests → httpx async (0 blocking requests)  
- ✅ **System commands**: 20+ subprocess → thread pools (0 blocking subprocess)
- ✅ **Overall blocking I/O**: 70% resolved (target achieved)

### **Performance Improvements**
- ✅ **Database throughput**: 3x improvement measured
- ✅ **External API concurrency**: 10x concurrent requests capability
- ✅ **System command response**: Non-blocking execution verified
- ✅ **Foundation for 25x concurrent capacity**: Infrastructure ready

### **Technical Quality**
- ✅ **Type safety**: 80% of new code type-annotated with Pydantic
- ✅ **Test coverage**: 80% of async functionality tested  
- ✅ **Zero regressions**: All existing functionality preserved
- ✅ **Documentation**: All new async patterns documented

### **Migration Readiness**
- ✅ **FastAPI infrastructure**: Core systems operational
- ✅ **Dual operation**: Flask and FastAPI running in parallel
- ✅ **Service configuration**: Updated for hybrid operation
- ✅ **Phase 2 ready**: Media processing migration can begin

---

## 🚨 **CRITICAL DEPENDENCIES & BLOCKERS**

### **Infrastructure Requirements**
- **Memory**: Monitor 3.8GB RAM usage with dual Flask/FastAPI
- **Database**: aiomysql driver must be stable under async load
- **Testing**: Comprehensive async test suite prevents regressions

### **Development Process**
- **Weekly progress tracking**: Each week's completion criteria must be met
- **Performance validation**: Measure improvements at each step
- **Documentation**: Update CLAUDE.md with async patterns learned
- **GitHub synchronization**: Update issues with progress weekly

**This Phase 1 todo list provides granular, week-by-week tasks to maintain synchronization across development sessions and ensure systematic async foundation implementation.**