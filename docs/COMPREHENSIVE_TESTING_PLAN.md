# MVidarr Enhanced - Comprehensive Testing Plan

**Date Created**: July 21, 2025  
**Last Updated**: July 22, 2025  
**Status**: Updated for Systemd Service Integration  
**Test Coverage**: Core Features + Authentication + UI + Service Management

---

## 🎯 Testing Overview

This comprehensive testing plan covers all aspects of MVidarr Enhanced including core functionality, authentication system, UI enhancements, and edge cases. The plan is designed to validate production readiness and identify any remaining issues before public release.

### **Testing Scope**
- ✅ All 11 completed feature requests
- ✅ Authentication and authorization system  
- ✅ Left sidebar navigation and UI improvements
- ✅ Artist pagination and user management
- ✅ Systemd service integration and management
- ✅ API endpoints and data integrity
- ✅ Security and performance validation
- ✅ Service auto-start and failure recovery

---

## 🧪 Test Execution Command

**Quick Test Run:**
```bash
# Execute comprehensive testing plan
python3 scripts/testing/run_comprehensive_tests.py

# Run specific test categories
python3 scripts/testing/run_comprehensive_tests.py --category=core
python3 scripts/testing/run_comprehensive_tests.py --category=auth
python3 scripts/testing/run_comprehensive_tests.py --category=ui
python3 scripts/testing/run_comprehensive_tests.py --category=api
python3 scripts/testing/run_comprehensive_tests.py --category=service
```

**Manual Testing Checklist:**
```bash
# Start application and run manual test checklist
python3 scripts/testing/manual_test_checklist.py
```

**Service Management Testing:**
```bash
# Test systemd service functionality
sudo ./scripts/install_service.sh install    # Install service
sudo systemctl status mvidarr               # Check status
./scripts/manage_service.sh status          # Test management script
sudo journalctl -u mvidarr -f               # Follow logs
```

---

## 📋 Test Categories

### **1. Core Functionality Tests**

#### **1.1 Artist Management**
- [ ] **Artist Search & Discovery**
  - [ ] Search artists with various criteria (name, genre, status)
  - [ ] IMVDb artist search returns 25+ results
  - [ ] Artist pagination works correctly (25, 50, 100, 200 per page)
  - [ ] Artist creation from IMVDb import
  - [ ] Artist metadata editing (all 4 tabs)
  - [ ] Artist thumbnail management (search, upload, crop)
  - [ ] Artist deletion with dependency analysis

- [ ] **Artist Video Discovery**
  - [ ] Discover videos for existing artists
  - [ ] Handle artists with special characters (311, TylerChildersVEVO)
  - [ ] Video metadata includes like_count and genre information
  - [ ] Duplicate video detection and merging

#### **1.2 Video Management**
- [ ] **Video Operations**
  - [ ] Video search with multi-criteria filters
  - [ ] Video pagination with smooth navigation
  - [ ] Video metadata editing including genre field
  - [ ] Video thumbnail management
  - [ ] Video streaming with range support
  - [ ] Video download queue management
  - [ ] Bulk video operations (download, delete, edit)

- [ ] **Video Organization**
  - [ ] Automatic file organization by artist
  - [ ] Filename cleanup and path correction
  - [ ] Recovery of orphaned video files
  - [ ] Duplicate detection and handling

#### **1.3 Download System**
- [ ] **Download Management**
  - [ ] Individual video downloads
  - [ ] Bulk download operations
  - [ ] Download queue visualization
  - [ ] Download progress tracking
  - [ ] Download All Wanted functionality (verify fix for "0 queued, 19 failed")
  - [ ] Caption/subtitle download when enabled
  - [ ] yt-dlp integration functionality

### **2. Authentication & Security Tests**

#### **2.1 User Authentication**
- [ ] **Login/Logout**
  - [ ] Simple login with admin credentials
  - [ ] Session persistence across browser restarts
  - [ ] Logout functionality clears session
  - [ ] Session timeout handling
  - [ ] Multiple concurrent sessions

- [ ] **User Management**
  - [ ] Admin user management interface at `/admin/users`
  - [ ] User creation with different roles
  - [ ] Role-based permission enforcement
  - [ ] User activation/deactivation
  - [ ] Session management for users

#### **2.2 Authorization & Permissions**
- [ ] **Role-Based Access Control**
  - [ ] READONLY user permissions
  - [ ] USER role capabilities
  - [ ] MANAGER role access
  - [ ] ADMIN full access
  - [ ] API endpoint protection
  - [ ] UI element visibility based on roles

#### **2.3 Two-Factor Authentication**
- [ ] **2FA Setup and Usage**
  - [ ] TOTP setup with QR code generation
  - [ ] 2FA verification process
  - [ ] Backup codes generation and usage
  - [ ] 2FA recovery procedures
  - [ ] Integration with existing auth system

### **3. User Interface Tests**

#### **3.1 Left Sidebar Navigation**
- [ ] **Sidebar Functionality**
  - [ ] Sidebar toggle on desktop and mobile
  - [ ] Fixed positioning during page scroll
  - [ ] Responsive behavior on different screen sizes
  - [ ] Mobile overlay functionality
  - [ ] Theme toggle integration

- [ ] **Navigation Items**
  - [ ] Dashboard link functionality
  - [ ] Artists page navigation
  - [ ] Videos page navigation
  - [ ] MvTV player access
  - [ ] Settings page access
  - [ ] User menu visibility for authenticated users

#### **3.2 User Interface Components**
- [ ] **Theme System**
  - [ ] Day/night mode toggle
  - [ ] Theme persistence across sessions
  - [ ] Bauhaus theme application
  - [ ] Multiple theme.park variants

- [ ] **Responsive Design**
  - [ ] Mobile device compatibility
  - [ ] Tablet layout optimization
  - [ ] Desktop full-screen usage
  - [ ] Print-friendly styling

#### **3.3 MvTV Continuous Player**
- [ ] **Player Functionality**
  - [ ] Continuous video playback
  - [ ] Playlist management
  - [ ] Artist dropdown with search
  - [ ] Cinematic mode with overlay controls
  - [ ] Keyboard shortcuts
  - [ ] Video quality selection

### **4. API & Data Integrity Tests**

#### **4.1 API Endpoint Testing**
- [ ] **Core APIs**
  - [ ] `/api/artists` - All CRUD operations
  - [ ] `/api/videos` - Search, filter, bulk operations
  - [ ] `/api/settings` - Database-driven configuration
  - [ ] `/api/health` - System diagnostics
  - [ ] `/api/users` - User management (admin only)

- [ ] **External Integrations**
  - [ ] IMVDb API connectivity and rate limiting
  - [ ] YouTube Data API integration
  - [ ] Wikipedia API for thumbnails
  - [ ] Error handling for API failures

#### **4.2 Database Operations**
- [ ] **Data Consistency**
  - [ ] Artist-video relationships
  - [ ] Genre data propagation
  - [ ] Settings synchronization
  - [ ] User session management
  - [ ] Audit log integrity

- [ ] **Performance**
  - [ ] Database query optimization
  - [ ] Large dataset handling (1000+ artists/videos)
  - [ ] Concurrent user operations
  - [ ] Memory usage during bulk operations

### **5. System & Performance Tests**

#### **5.1 System Health**
- [ ] **Health Monitoring**
  - [ ] `/api/health` endpoint comprehensive checks
  - [ ] Database connectivity validation
  - [ ] Service status monitoring
  - [ ] Log file accessibility
  - [ ] Disk space monitoring

#### **5.2 Performance Validation**
- [ ] **Response Times**
  - [ ] API endpoints < 200ms average
  - [ ] Search operations < 500ms
  - [ ] Bulk operations complete within reasonable time
  - [ ] Video streaming without buffering issues

#### **5.3 Error Handling**
- [ ] **Graceful Degradation**
  - [ ] Network connectivity issues
  - [ ] Database connection failures
  - [ ] External API unavailability
  - [ ] Invalid user input handling
  - [ ] File system permission errors

### **6. Service Management Tests**

#### **6.1 Systemd Service Operations**
- [ ] **Service Installation**
  - [ ] Install systemd service: `sudo ./scripts/install_service.sh install`
  - [ ] Verify service file created at `/etc/systemd/system/mvidarr.service`
  - [ ] Check service enabled for auto-start: `systemctl is-enabled mvidarr.service`
  - [ ] Verify virtual environment and dependencies setup
  - [ ] Test service uninstallation: `sudo ./scripts/install_service.sh uninstall`

- [ ] **Service Control Operations**
  - [ ] Start service: `sudo systemctl start mvidarr.service`
  - [ ] Stop service: `sudo systemctl stop mvidarr.service`
  - [ ] Restart service: `sudo systemctl restart mvidarr.service`
  - [ ] Check service status: `sudo systemctl status mvidarr.service`
  - [ ] Verify service health endpoint responds after start
  - [ ] Test graceful shutdown on service stop

#### **6.2 Service Management Scripts**
- [ ] **Management Script Integration**
  - [ ] `./scripts/manage_service.sh status` - Uses systemd when available
  - [ ] `./scripts/manage_service.sh start` - Prefers systemd service
  - [ ] `./scripts/manage_service.sh stop` - Proper systemd integration
  - [ ] `./scripts/manage_service.sh restart` - Enhanced restart with validation
  - [ ] `./scripts/manage_service.sh logs` - Shows systemd journal logs
  - [ ] `./scripts/manage_service.sh install-service` - Installs systemd service

- [ ] **Service Auto-Start Testing**
  - [ ] Verify service starts automatically on system boot
  - [ ] Test service restart on failure (simulate crash)
  - [ ] Check restart limits and backoff policies
  - [ ] Validate resource limits (memory, CPU, file descriptors)
  - [ ] Test service behavior during system shutdown

#### **6.3 Service Logging & Monitoring**
- [ ] **Log Management**
  - [ ] Verify logs written to systemd journal: `sudo journalctl -u mvidarr.service`
  - [ ] Test log rotation and retention
  - [ ] Check log accessibility with `./scripts/manage_service.sh logs`
  - [ ] Verify error logging during service failures
  - [ ] Test live log following: `sudo journalctl -u mvidarr.service -f`

- [ ] **Service Health Validation**
  - [ ] Application responds on http://localhost:5000 after service start
  - [ ] Health endpoint accessible: `/api/health`
  - [ ] Database connectivity through service
  - [ ] Service memory usage within limits
  - [ ] Service restart after configuration changes

#### **6.4 Production Environment Testing**
- [ ] **Environment Validation**
  - [ ] Service runs correctly with production settings
  - [ ] Virtual environment isolation working
  - [ ] File permissions properly configured
  - [ ] Network port binding successful (port 5000)
  - [ ] Service user permissions adequate

- [ ] **Failure Recovery**
  - [ ] Service restarts after application crashes
  - [ ] Recovery from database connection failures
  - [ ] Proper handling of port conflicts
  - [ ] Service behavior during system resource exhaustion
  - [ ] Log analysis for failure diagnosis

### **7. Security & Vulnerability Tests**

#### **7.1 Security Validation**
- [ ] **Authentication Security**
  - [ ] Password complexity enforcement
  - [ ] Account lockout protection
  - [ ] Session security (token generation, expiration)
  - [ ] CSRF protection validation
  - [ ] SQL injection prevention

#### **7.2 Access Control Testing**
- [ ] **Authorization Enforcement**
  - [ ] Verify all endpoints respect role permissions
  - [ ] Test privilege escalation prevention
  - [ ] Validate admin-only functionality protection
  - [ ] Check for information disclosure

---

## 🚀 Test Execution Workflow

### **Phase 1: Automated Tests (30 minutes)**
1. Run core functionality test suite
2. Execute API endpoint validation
3. Perform database integrity checks
4. Validate authentication workflows

### **Phase 2: Manual UI Testing (45 minutes)**
1. Test sidebar navigation on all devices
2. Verify user management interface
3. Validate MvTV player functionality
4. Check theme system operation

### **Phase 3: Integration Testing (30 minutes)**
1. Test external API integrations
2. Validate video download workflows
3. Check bulk operation performance
4. Verify cross-feature interactions

### **Phase 4: Service Management Testing (20 minutes)**
1. Test systemd service installation and setup
2. Validate service control operations
3. Check auto-start and failure recovery
4. Verify log integration and monitoring

### **Phase 5: Security & Performance (30 minutes)**
1. Execute security validation tests
2. Perform load testing scenarios
3. Check error handling robustness
4. Validate system health monitoring

---

## 📊 Test Results Documentation

### **Test Report Template**
- **Test Date**: 
- **Tester**: 
- **Environment**: 
- **Test Coverage**: 
- **Pass Rate**: 
- **Critical Issues**: 
- **Recommendations**: 

### **Issue Tracking**
- **Priority Levels**: Critical, High, Medium, Low
- **Categories**: Bug, Enhancement, Documentation
- **Status**: Open, In Progress, Resolved, Verified

---

## 🔧 Test Environment Setup

### **Prerequisites**
- Python 3.12+ with all dependencies installed
- MariaDB running with test database
- Network connectivity for external APIs
- Write access to data directories

### **Test Data Preparation**
- Sample artists with various metadata
- Test videos in different formats
- User accounts with different roles
- Test settings configurations

---

## 📝 Success Criteria

**Testing is considered successful when:**
- ✅ 95%+ pass rate on all automated tests
- ✅ All critical functionality works as expected
- ✅ No security vulnerabilities identified
- ✅ Performance meets specified benchmarks
- ✅ UI/UX functions properly across devices
- ✅ Authentication and authorization work correctly
- ✅ All new features integrate seamlessly

**Ready for Production when:**
- ✅ All critical and high-priority issues resolved
- ✅ Documentation updated and complete
- ✅ Docker containerization tested
- ✅ Deployment procedures validated