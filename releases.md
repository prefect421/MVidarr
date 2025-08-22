---
layout: page
title: Releases
permalink: /releases/
---

# Releases

Track MVidarr's development progress through our release history and upcoming milestones.

## 🚀 Current Release: v0.9.7

**Released**: August 22, 2025  
**Focus**: Enterprise Media Management & Production Readiness

### 🏆 Major Achievements
- **🎯 47 Comprehensive Solutions**: Complete feature matrix across all application areas
- **✅ Enterprise Quality**: 185+ comprehensive tests with 6000+ lines documentation
- **🚀 Production Ready**: Zero known vulnerabilities with automated security monitoring
- **💫 User Experience**: Modern interface with professional workflows requiring no technical expertise

### 🎮 Advanced Video Management
- **Professional Video Players**: Standard, MvTV, and cinematic modes with subtitle support
- **Advanced Search & Filtering**: Multi-criteria search with year range and performance optimization
- **Bulk Operations**: Enterprise-grade batch processing with real-time progress tracking
- **Intelligent Organization**: Automatic folder creation and cleanup systems

### 🎨 User Interface Excellence
- **Streamlined Workflows**: Intuitive user journeys eliminating all reported pain points
- **Theme System**: Consistent UI with MVIDARR logo and CSS variable compliance
- **Progress Indicators**: Professional feedback systems with error recovery
- **Responsive Design**: Modern interface with accessibility features

### 🔧 Developer Experience
- **Complete Testing Infrastructure**: Pytest suite covering all functionality categories
- **Comprehensive API Documentation**: OpenAPI specification with detailed examples
- **Architecture Documentation**: 700+ lines detailing system design patterns
- **CI/CD Pipeline**: Automated testing, security scanning, deployment automation

### 🛡️ Security & Performance
- **Enterprise Security**: Complete audit with 8 automated security workflows
- **Performance Optimization**: Sub-500ms response times maintained across all features
- **Zero Technical Debt**: Clean code with proper patterns for long-term maintenance
- **100% Backward Compatibility**: All existing functionality preserved

**Docker Image**: `ghcr.io/prefect421/mvidarr:v0.9.7`

---

## 🔄 Development Version: v0.9.8-dev

**Status**: In Active Development  
**Focus**: External Service Integrations & Advanced Features

### Planned Improvements
- Enhanced Spotify integration and music discovery capabilities
- Media server integration (Plex/Jellyfin/Emby) for centralized management
- Advanced notification system with Discord/Slack integration
- Third-party metadata providers integration for enriched content
- Cloud storage integration and comprehensive backup solutions

### Strategic Focus
Expanding MVidarr's ecosystem integration capabilities while maintaining the enterprise-grade quality and performance standards established in v0.9.7.

---

## 📅 Release Roadmap

### v0.9.8 - External Service Integrations
**Planned Release**: November 2025

- Enhanced Spotify integration and music discovery capabilities
- Media server integration (Plex/Jellyfin/Emby) for centralized management  
- Advanced notification system with Discord/Slack integration
- Third-party metadata providers integration for enriched content
- Cloud storage integration and comprehensive backup solutions

### v0.9.9 - Enterprise & Multi-User Features
**Planned Release**: August 2026

- Advanced user management and role-based access control
- Multi-tenant artist libraries and data isolation
- Comprehensive audit logging and activity tracking
- API rate limiting and resource quota management
- Enterprise authentication integration (LDAP/SSO/SAML)

### v1.0.0 - Production Readiness & Stability
**Planned Release**: November 2026 - **Public Release**

- Complete documentation overhaul and user guides
- Migration tools and database upgrade automation
- Advanced backup and disaster recovery system
- Production deployment automation and infrastructure
- Long-term maintenance tools and system optimization

---

## 📈 Previous Releases

### v0.9.4
**Released**: August 6, 2025  
**Focus**: Docker Optimization and Build Reliability

- **🐳 Docker Build Optimization**: Reduced build time from timeout failures to consistent 8m6s builds
- **📦 Container Size Reduction**: Optimized Docker image layers and dependencies (1.41GB production images)
- **⚡ Build Reliability**: Fixed timeout issues with build-essential package installation
- **🔍 Monitoring Infrastructure**: Added comprehensive Docker build monitoring and validation tools
- Multi-stage Docker builds with optimized caching strategies
- Production-ready container configurations and enhanced .dockerignore

### v0.9.3
**Released**: July 28, 2025  
**Focus**: Security Implementation

- Enterprise-grade security audit completion
- Comprehensive vulnerability remediation (17 issues fixed)
- Advanced security monitoring infrastructure
- Automated security scanning workflows
- Enhanced authentication and authorization systems

### v0.9.2  
**Released**: July 15, 2025  
**Focus**: Core Functionality Stabilization

- Advanced artist management system
- Comprehensive video discovery and organization
- Modern UI with theme system implementation
- Database-driven configuration management
- System health monitoring and diagnostics

### v0.9.1
**Released**: June 2025  
**Focus**: Foundation and Architecture

- Initial Flask application architecture
- Basic artist and video management
- Database schema and ORM implementation
- Authentication system foundation
- Docker containerization setup

---

## 🔄 Release Process

### Release Cycles
- **Major Releases** (x.y.0): Every 3-4 months with significant new features
- **Minor Releases** (x.y.z): Monthly with bug fixes and small improvements  
- **Security Releases**: As needed for critical security updates

### Quality Assurance
- **Automated Testing**: Comprehensive test suite with CI/CD integration
- **Security Scanning**: Multi-tool security validation on every release
- **Performance Testing**: Automated performance regression testing
- **Docker Validation**: Container build and size optimization verification

### Release Notes
Each release includes detailed notes covering:
- New features and improvements
- Security updates and fixes
- Performance enhancements
- Breaking changes and migration guides
- Known issues and workarounds

---

## 📋 Release Statistics

### Development Metrics
- **Total Releases**: 5 major releases
- **Issues Resolved**: 200+ across all releases
- **Security Fixes**: 17 vulnerabilities addressed (zero remaining)
- **Docker Optimization**: 100% build reliability achieved
- **Test Coverage**: 185+ comprehensive tests implemented

### Performance Improvements
- **Docker Build Time**: From timeout failures to 8m6s consistent builds
- **Container Size**: Optimized to 1.41GB production images  
- **Security Posture**: Zero known vulnerabilities maintained
- **API Response Times**: <500ms for typical operations (target)
- **Database Performance**: Optimized for 10,000+ video libraries

---

## 🎯 Version Support

### Current Support Status
- **v0.9.7**: ✅ Fully supported with security updates
- **v0.9.4**: ✅ Security updates only
- **v0.9.3**: ⚠️ End of life - upgrade recommended
- **v0.9.2**: ❌ End of life - upgrade required

### Support Policy
- **Latest Release**: Full feature support and security updates
- **Previous Release**: Security updates for 6 months
- **Older Releases**: End of life after 1 year

---

## 📦 Download & Deployment

### Docker Images
```bash
# Latest stable release
docker pull ghcr.io/prefect421/mvidarr:latest

# Specific version
docker pull ghcr.io/prefect421/mvidarr:v0.9.7

# Development build
docker pull ghcr.io/prefect421/mvidarr:dev
```

### Source Code
```bash
# Latest release
git clone --branch v0.9.7 https://github.com/prefect421/mvidarr.git

# Development version
git clone --branch dev https://github.com/prefect421/mvidarr.git
```

### Release Verification
All releases are:
- **Signed**: GPG signatures for source releases
- **Checksummed**: SHA256 checksums for all artifacts
- **Scanned**: Security scanned before publication
- **Tested**: Automated testing and validation

---

## 📢 Release Notifications

Stay updated on new releases:

- **GitHub Releases**: [Watch the repository]({{ site.github.repository_url }}) for notifications
- **Release RSS**: Subscribe to our [releases RSS feed]({{ site.github.repository_url }}/releases.atom)
- **GitHub Discussions**: Join [release discussions]({{ site.github.repository_url }}/discussions/categories/releases)
- **Security Alerts**: Subscribe to [security advisories]({{ site.github.repository_url }}/security/advisories)

---

**Looking for a specific version?** Check our complete [release history on GitHub]({{ site.github.repository_url }}/releases).