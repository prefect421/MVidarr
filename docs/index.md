---
layout: home
title: Home
---

{: .text-center }
![MVidarr Logo](https://raw.githubusercontent.com/prefect421/mvidarr/main/frontend/src/Content/Images/mvidarr-logo.png){: width="150" height="150"}

# MVidarr
{: .text-center }

**A comprehensive music video management and discovery platform** that helps you organize, discover, and stream your music video collection with intelligent artist management and advanced search capabilities.
{: .text-center }

{: .text-center }
[![Version](https://img.shields.io/badge/version-v0.9.5-blue.svg)](https://github.com/prefect421/mvidarr/releases/tag/v0.9.5){: target="_blank"}
[![Stars](https://img.shields.io/github/stars/prefect421/mvidarr.svg)](https://github.com/prefect421/mvidarr){: target="_blank"}
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/prefect421/mvidarr/blob/main/LICENSE){: target="_blank"}
[![Docker](https://img.shields.io/badge/docker-ghcr.io-2496ED.svg)](https://ghcr.io/prefect421/mvidarr:v0.9.5){: target="_blank"}

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

{: .text-center }
📥 **[Installation Guide]({% link _tabs/installation.md %})**  
🎉 **[Download v0.9.5](https://github.com/prefect421/mvidarr/releases/tag/v0.9.5)**  
🐳 **[Docker Image](https://ghcr.io/prefect421/mvidarr:v0.9.5)**

### 🐳 Docker Deployment (Recommended)

```bash
# Quick start with Docker Compose
git clone https://github.com/prefect421/mvidarr.git
cd mvidarr && git checkout v0.9.5
docker-compose up -d

# Or use production image directly
docker pull ghcr.io/prefect421/mvidarr:v0.9.5
```

**🌐 Access your application:**
- **URL**: `http://localhost:5001`
- **Default Login**: `admin` / `admin` ⚠️ *Change immediately*
- **API Docs**: `http://localhost:5001/api/docs`

## 🏗️ Architecture

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">
  <div style="border: 1px solid #e1e4e8; border-radius: 6px; padding: 16px;">
    <h3>🐍 Backend</h3>
    <p>Flask (Python 3.12+) with modular service architecture, RESTful APIs, and comprehensive error handling</p>
  </div>
  <div style="border: 1px solid #e1e4e8; border-radius: 6px; padding: 16px;">
    <h3>🗄️ Database</h3>
    <p>MariaDB 11.4+ with automatic initialization, optimized queries, and intelligent indexing</p>
  </div>
  <div style="border: 1px solid #e1e4e8; border-radius: 6px; padding: 16px;">
    <h3>🎨 Frontend</h3>
    <p>Modern responsive design with advanced JavaScript, theme system, and mobile optimization</p>
  </div>
  <div style="border: 1px solid #e1e4e8; border-radius: 6px; padding: 16px;">
    <h3>🔒 Security</h3>
    <p>Enterprise-grade security with role-based access, automated vulnerability scanning, and audit logging</p>
  </div>
</div>

## 🤝 Community & Support

<div align="center" style="margin: 20px 0;">
  <a href="https://github.com/prefect421/mvidarr/issues" target="_blank" style="background: #6f42c1; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; margin: 0 10px; display: inline-block;">
    🐛 Report Issues
  </a>
  <a href="https://github.com/prefect421/mvidarr/discussions" target="_blank" style="background: #0969da; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; margin: 0 10px; display: inline-block;">
    💬 Discussions
  </a>
  <a href="{% link _tabs/documentation.md %}" style="background: #1f883d; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; margin: 0 10px; display: inline-block;">
    📚 Documentation
  </a>
</div>

---

<div align="center" style="margin: 20px 0; padding: 20px; background: #f6f8fa; border-radius: 6px;">
  <h3>🚀 MVidarr v0.9.5</h3>
  <p><strong>UI/UX Excellence & Documentation Complete</strong></p>
  <p>Built with ❤️ for music video enthusiasts</p>
  <small>Licensed under the <a href="https://github.com/prefect421/mvidarr/blob/main/LICENSE" target="_blank">MIT License</a></small>
</div>