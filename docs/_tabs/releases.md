---
# the default layout is 'page'
icon: fas fa-rocket
order: 5
---

# Releases

Track MVidarr's development progress through our release history and upcoming milestones.

## 🚀 Current Release: v0.9.5

**Released**: August 11, 2025  
**Focus**: UI/UX Excellence & Documentation Complete

### Major Improvements
- **🎨 Streamlined UI Design**: Clean, professional headers and improved navigation across all pages
- **📚 Complete Documentation Portfolio**: Comprehensive guides for developers, users, and operations
- **📄 Artists Page Pagination**: Full navigation controls with customizable page sizes
- **⚡ Performance Optimizations**: 60% CI time reduction and enhanced system reliability
- **🔧 Enhanced Scheduler Service**: Flexible time intervals and improved error handling

### Key Features
- 35 comprehensive features including all core functionality
- Complete dual-source video discovery (IMVDb + YouTube)
- Professional thumbnail management with multi-source search
- Advanced artist management with bulk operations
- Enterprise-grade security with automated vulnerability scanning
- Multi-user authentication with role-based access control
- MvTV continuous player with cinematic mode
- Enhanced Docker-native scheduler service

### Technical Enhancements
- Fixed Video Indexing Database Statistics with SQLAlchemy compatibility
- Resolved Themes API Authentication for seamless settings management
- Verified Scheduled Download System functionality for YouTube videos
- Complete Duplicate Video Merge functionality with enhanced UI
- Docker build optimization with consistent 8-minute build times
- Container size optimization to 1.41GB production images
- **Fixed GitHub Actions Release Automation**: Resolved tar archive and permissions issues
- **Modernized CI/CD Pipeline**: Updated to use GitHub CLI with proper workflow permissions
- **Reliable Release Asset Generation**: Automated source code and installation package creation

### Download v0.9.5
- **[GitHub Release](https://github.com/prefect421/mvidarr/releases/tag/v0.9.5)** - Source code and installation packages
- **[Docker Image](https://ghcr.io/prefect421/mvidarr:v0.9.5)** - Production-ready container
- **[Documentation](https://prefect421.github.io/mvidarr)** - Complete user and developer guides

## 📋 Previous Release: v0.9.4

**Released**: August 6, 2025  
**Focus**: Docker Optimization and Build Reliability

### Major Improvements
- **🐳 Docker Build Optimization**: Reduced build time from timeout failures to consistent 8m6s builds
- **📦 Container Size Reduction**: Optimized Docker image layers and dependencies (1.41GB production images)
- **⚡ Build Reliability**: Fixed timeout issues with build-essential package installation
- **🔍 Monitoring Infrastructure**: Added comprehensive Docker build monitoring and validation tools

### Key Features
- Multi-stage Docker builds with optimized caching
- Automated Docker size monitoring and validation
- Enhanced .dockerignore for build context optimization
- Production-ready container configurations
- Build performance monitoring and analysis tools

### Technical Enhancements
- Fixed Docker build timeout issues by replacing build-essential with gcc+g++
- Implemented --timeout=1000 for pip installations of heavy packages
- Added comprehensive Docker monitoring workflows
- Created build context analysis and optimization tools
- Enhanced container layer caching strategies

## 🗓️ Release History

### v0.9.3 - Theme System & UI Improvements
**Released**: August 4, 2025

- **🎨 Complete Theme Export/Import**: Export individual themes or all themes as JSON files
- **🔧 Simplified Theme Management**: Streamlined single-variant theme system
- **📹 Enhanced Video Management**: Bulk refresh metadata with preserved navigation context
- **🏗️ Major Code Refactoring**: Videos page reduced by 98.7% through modular components
- **🎯 API-Based Themes**: 7 built-in themes with real-time switching

### v0.9.2 - Performance & Security
**Released**: July 28, 2025

- **🛡️ Comprehensive Security Audit**: Fixed 17 vulnerabilities (1 Critical, 2 High, 12 Medium, 2 Low)
- **🔒 Enhanced Authentication**: Multi-user support with role-based access control
- **⚡ Performance Optimizations**: Database query optimization and intelligent caching
- **🔍 Advanced Search**: Real-time suggestions and fuzzy matching capabilities
- **📊 System Health Monitoring**: Comprehensive diagnostics and reporting

### v0.9.1 - Core Functionality
**Released**: July 15, 2025

- **🎯 Advanced Artist Management**: Multi-criteria search and bulk operations
- **🔍 Video Discovery Integration**: Dual-source support (IMVDb + YouTube)
- **📺 MvTV Player**: Continuous playback with cinematic mode
- **📥 Download Management**: Queue system with progress tracking
- **🖼️ Thumbnail Management**: Multi-source search and optimization

### v0.9.0 - Initial Release
**Released**: June 30, 2025

- **🏗️ Core Architecture**: Flask-based backend with modern frontend
- **🐳 Docker Support**: Containerized deployment with Docker Compose
- **📊 Database Integration**: MySQL/MariaDB with SQLAlchemy ORM
- **🔐 Basic Authentication**: User management and session handling
- **📱 Responsive UI**: Mobile-friendly interface design

## 🔮 Upcoming Releases

### v0.9.6 - Advanced Testing & Mobile Optimization
**Planned**: Q4 2025

#### Planned Features
- **🧪 Advanced Testing Framework**: Comprehensive test coverage and automation
- **📱 Enhanced Mobile Design**: Improved responsive layouts and touch interactions
- **⚡ Video Quality Management**: Automatic quality detection and optimization
- **🔌 Extended API Functionality**: Additional endpoints for third-party integrations
- **📊 Performance Dashboard**: Real-time monitoring and metrics visualization

#### Technical Improvements
- **🔧 Plugin System**: Support for custom extensions and integrations
- **📈 Analytics Engine**: Advanced reporting and usage statistics
- **☁️ Cloud Integration**: Support for cloud storage providers
- **🎨 Advanced Theming**: Enhanced customization capabilities
- **🔍 Search Improvements**: AI-powered search suggestions and recommendations

### v1.0.0 - Stable Release
**Target**: Q1 2026

#### Goals
- **🎯 Production Ready**: Enterprise-grade stability and performance
- **📚 Complete Documentation**: Comprehensive guides and API documentation
- **🔒 Security Certification**: Professional security audit and certification
- **🌐 Multi-language Support**: Internationalization and localization
- **🤝 Community Features**: Plugin marketplace and community contributions

## 📊 Release Statistics

### Development Metrics
- **Total Releases**: 6 major versions
- **Features Implemented**: 35+ comprehensive capabilities
- **Security Fixes**: 17 vulnerabilities resolved
- **Performance Improvements**: 60% CI time reduction
- **Docker Optimizations**: 8-minute consistent build times

### Community Engagement
- **GitHub Stars**: Growing community interest
- **Issues Resolved**: Active issue tracking and resolution
- **Documentation Pages**: 25+ comprehensive guides
- **Test Coverage**: Expanding automated test suite

## 🔗 Release Resources

### Download Options
- **[GitHub Releases](https://github.com/prefect421/mvidarr/releases)** - All versions with release notes
- **[Docker Hub](https://ghcr.io/prefect421/mvidarr)** - Container images for all versions
- **[Source Code](https://github.com/prefect421/mvidarr)** - Latest development code

### Documentation
- **[Installation Guide]({% link _tabs/installation.md %})** - Setup instructions for all versions
- **[Migration Guides](https://github.com/prefect421/mvidarr/tree/main/docs/migrations)** - Upgrade procedures
- **[Breaking Changes](https://github.com/prefect421/mvidarr/blob/main/BREAKING_CHANGES.md)** - Compatibility information

### Support
- **[GitHub Issues](https://github.com/prefect421/mvidarr/issues)** - Bug reports and feature requests
- **[Discussions](https://github.com/prefect421/mvidarr/discussions)** - Community Q&A and feedback
- **[Project Board](https://github.com/users/prefect421/projects/1)** - Development roadmap and progress

---

## 📅 Release Schedule

MVidarr follows a regular release schedule:

- **Major Releases** (x.0.0): Quarterly, with significant new features
- **Minor Releases** (x.y.0): Monthly, with feature additions and improvements  
- **Patch Releases** (x.y.z): As needed, for bug fixes and security updates
- **Beta Releases**: Available for testing new features before official release

### Versioning Policy
- **Semantic Versioning**: Following semver.org standards
- **Backward Compatibility**: Maintained within minor version increments
- **Deprecation Notice**: 2 release cycles for deprecated features
- **LTS Support**: Long-term support for select stable versions

---

*Stay updated with the latest releases by watching our [GitHub repository](https://github.com/prefect421/mvidarr) and subscribing to release notifications.*