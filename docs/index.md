---
layout: home
title: Home
---

# MVidarr

**A comprehensive music video management and discovery platform** that helps you organize, discover, and stream your music video collection with intelligent artist management and advanced search capabilities.

## ✨ Key Features

- **🎯 Advanced Artist Management** - Multi-criteria search and bulk operations
- **🔍 Comprehensive Video Discovery** - Dual-source integration (IMVDb + YouTube)  
- **🖼️ Advanced Thumbnail Management** - Multi-source search and cropping
- **📁 Intelligent Organization** - Automatic folder creation and cleanup
- **🔎 Advanced Search System** - Real-time suggestions and filtering
- **⚡ Bulk Operations** - Multi-select editing and batch processing
- **📺 Video Streaming** - Built-in player with transcoding support
- **💚 System Health Monitoring** - Comprehensive diagnostics
- **⚙️ Database-Driven Settings** - Complete configuration management
- **📥 Download Management** - Queue visualization and progress tracking
- **🎨 Modern UI** - Left sidebar navigation with theme system
- **📺 MvTV Continuous Player** - Cinematic mode for uninterrupted viewing
- **🎭 Genre Management** - Automatic genre tagging and filtering
- **🔐 User Authentication** - Role-based access control with security features
- **🌙 Dark/Light Themes** - Multiple theme options with automatic switching

## 🆕 Recent Updates (v0.9.5) - **LATEST STABLE RELEASE**

- **🎨 UI/UX Excellence** - Streamlined design with clean headers and improved navigation
- **📚 Complete Documentation** - Comprehensive guides for developers, users, and operations
- **📄 Artists Page Pagination** - Full navigation controls with customizable page sizes
- **⚡ Performance Optimizations** - 60% CI time reduction and enhanced system reliability
- **🔧 Enhanced Scheduler** - Flexible time intervals and improved error handling
- **🐛 Critical Bug Fixes** - SQLAlchemy compatibility, API authentication, and UI issues resolved
- **🤖 Fixed Release Automation** - Resolved GitHub Actions workflow issues for reliable deployments
- **📦 Automated Asset Generation** - Source code and installation packages now auto-generated
- **📦 Container Size Optimization** - Efficient multi-stage builds with optimized caching (1.41GB optimized size)
- **🔍 Build Monitoring** - Comprehensive Docker build monitoring and validation infrastructure
- **⚡ Build Reliability** - 100% build success rate with automated size monitoring and performance tracking
- **🛠️ Infrastructure** - Enhanced CI/CD workflows with automated Docker monitoring and health checks

## 🚀 Quick Start

### Docker Deployment (Recommended)

```bash
git clone https://github.com/prefect421/mvidarr.git
cd mvidarr
docker-compose up -d
```

**Production Docker Image:**
```bash
# Use the latest stable release (v0.9.5)
docker pull ghcr.io/prefect421/mvidarr:v0.9.5

# Or use the latest tag
docker pull ghcr.io/prefect421/mvidarr:latest
```

**Access the application:**
- Open your browser to `http://localhost:5001`
- Default login: `admin` / `admin` (change immediately)

## 🏗️ Architecture

MVidarr is built with:

- **Backend**: Flask (Python 3.12+) with modular service architecture
- **Database**: MariaDB 11.4+ with automatic table initialization
- **Frontend**: Modern HTML5/CSS3/JavaScript with responsive design
- **Media Processing**: FFmpeg, yt-dlp for video downloading and processing
- **Authentication**: Secure user management with role-based access control
- **Security**: bcrypt password hashing, session management, audit logging
- **Containerization**: Optimized Docker Compose with multi-stage builds, automated monitoring, and 1.41GB production images

## 📄 License

This project is licensed under the MIT License - see the [LICENSE]({{ site.github.repository_url }}/blob/main/LICENSE) file for details.

---

**MVidarr v{{ site.data.version.current | default: "0.9.4" }}** - Built with ❤️ for music video enthusiasts