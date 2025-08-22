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

## 🆕 Latest Release (v0.9.7) - Enterprise Media Management

### 🏆 Major Achievements
- **🎯 47 Comprehensive Solutions** - Complete feature matrix across all application areas  
- **✅ Enterprise Quality** - 185+ comprehensive tests with 6000+ lines documentation
- **🚀 Production Ready** - Zero known vulnerabilities with automated security monitoring
- **💫 User Experience** - Modern interface with professional workflows requiring no technical expertise

### 🎮 Advanced Video Management
- **🔍 Advanced Search & Filtering** - Multi-criteria search with year range and performance optimization
- **⚡ Bulk Operations** - Enterprise-grade batch processing with real-time progress tracking
- **📺 Professional Video Players** - Standard, MvTV, and cinematic modes with subtitle support
- **📁 Intelligent Organization** - Automatic folder creation and cleanup systems

### 🎨 User Interface Excellence  
- **🎨 Streamlined Workflows** - Intuitive user journeys eliminating all reported pain points
- **🎭 Theme System** - Consistent UI with MVIDARR logo and CSS variable compliance
- **📊 Progress Indicators** - Professional feedback systems with error recovery
- **📱 Responsive Design** - Modern interface with accessibility features

## 🚀 Quick Start

### Docker Deployment (Recommended)

```bash
git clone https://github.com/prefect421/mvidarr.git
cd mvidarr
docker-compose up -d
```

**Production Docker Image:**
```bash
# Use the latest stable release
docker pull ghcr.io/prefect421/mvidarr:v0.9.7
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

**MVidarr v{{ site.data.version.current | default: "0.9.7" }}** - Built with ❤️ for music video enthusiasts