---
layout: home
title: MVidarr - Music Video Management Platform
---

<div class="home-header">
  <img src="https://raw.githubusercontent.com/prefect421/mvidarr/main/frontend/src/Content/Images/mvidarr-logo.png" alt="MVidarr Logo" width="150" height="150">
  
  <h1>MVidarr</h1>
  
  <p class="tagline"><strong>A comprehensive music video management and discovery platform</strong> that helps you organize, discover, and stream your music video collection with intelligent artist management and advanced search capabilities.</p>
  
  <div class="badges">
    <a href="https://github.com/prefect421/mvidarr/releases/tag/v0.9.5" target="_blank">
      <img src="https://img.shields.io/badge/version-v0.9.5-blue.svg" alt="Version">
    </a>
    <a href="https://github.com/prefect421/mvidarr" target="_blank">
      <img src="https://img.shields.io/github/stars/prefect421/mvidarr.svg" alt="Stars">
    </a>
    <a href="https://github.com/prefect421/mvidarr/blob/main/LICENSE" target="_blank">
      <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
    </a>
    <a href="https://ghcr.io/prefect421/mvidarr:v0.9.5" target="_blank">
      <img src="https://img.shields.io/badge/docker-ghcr.io-2496ED.svg" alt="Docker">
    </a>
  </div>
</div>

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

<div class="quick-start">
  <a href="https://github.com/prefect421/mvidarr/releases/tag/v0.9.5" target="_blank">📥 Download v0.9.5</a>
  <a href="https://ghcr.io/prefect421/mvidarr:v0.9.5" target="_blank">🐳 Docker Image</a>
  <a href="#installation">📚 Installation Guide</a>
</div>

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

<div class="architecture-grid">
  <div class="arch-card">
    <h3>🐍 Backend</h3>
    <p>Flask (Python 3.12+) with modular service architecture, RESTful APIs, and comprehensive error handling</p>
  </div>
  <div class="arch-card">
    <h3>🗄️ Database</h3>
    <p>MariaDB 11.4+ with automatic initialization, optimized queries, and intelligent indexing</p>
  </div>
  <div class="arch-card">
    <h3>🎨 Frontend</h3>
    <p>Modern responsive design with advanced JavaScript, theme system, and mobile optimization</p>
  </div>
  <div class="arch-card">
    <h3>🔒 Security</h3>
    <p>Enterprise-grade security with role-based access, automated vulnerability scanning, and audit logging</p>
  </div>
</div>

## 🎯 About MVidarr

<div class="about-section">
  <p>MVidarr is a comprehensive music video management and discovery platform designed for music enthusiasts who want to organize, discover, and stream their music video collections with professional-grade tools and intelligent automation.</p>

  <h2>🌟 Project Vision</h2>
  <p>Our vision is to create the ultimate music video management solution that combines the discovery power of multiple sources with intelligent organization, advanced search capabilities, and a modern streaming experience.</p>

  <h2>🛡️ Enterprise Security Features</h2>
  <div class="architecture-grid">
    <div class="arch-card">
      <h3>🔐 Authentication</h3>
      <p>Role-based access control with Admin, Manager, User, and ReadOnly roles</p>
    </div>
    <div class="arch-card">
      <h3>🔒 Data Protection</h3>
      <p>bcrypt password hashing, secure session management, and SQL injection prevention</p>
    </div>
    <div class="arch-card">
      <h3>📊 Audit Logging</h3>
      <p>Comprehensive audit trails and account lockout protection</p>
    </div>
    <div class="arch-card">
      <h3>🛡️ Security Scanning</h3>
      <p>Automated vulnerability scanning with enterprise-grade security workflows</p>
    </div>
  </div>

  <h2>📈 Development Philosophy</h2>
  <ul>
    <li><strong>Security First</strong>: Every feature is designed with security in mind</li>
    <li><strong>User Experience</strong>: Intuitive interfaces that don't compromise on functionality</li>
    <li><strong>Performance</strong>: Optimized for speed and reliability with 60% CI time reduction</li>
    <li><strong>Maintainability</strong>: Clean, well-documented code architecture</li>
    <li><strong>Extensibility</strong>: Built to grow with your needs</li>
  </ul>

  <h2>🚀 Current Status: v0.9.5</h2>
  <p><strong>Latest Release</strong>: UI/UX Excellence & Documentation Complete</p>
  <ul>
    <li>✅ Complete Docker optimization with 8-minute reliable builds</li>
    <li>✅ Container size optimization (1.41GB production images)</li>
    <li>✅ Enterprise-grade security with 17 vulnerabilities resolved</li>
    <li>✅ 35+ comprehensive features with advanced automation</li>
    <li>✅ Professional documentation and GitHub Pages deployment</li>
  </ul>
</div>

## 🤝 Community & Support

<div class="community-section">
  <a href="https://github.com/prefect421/mvidarr/issues" target="_blank" style="background: #6f42c1; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; margin: 0 10px; display: inline-block;">
    🐛 Report Issues
  </a>
  <a href="https://github.com/prefect421/mvidarr/discussions" target="_blank" style="background: #0969da; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; margin: 0 10px; display: inline-block;">
    💬 Discussions
  </a>
  <a href="https://github.com/prefect421/mvidarr/tree/main/docs" target="_blank" style="background: #1f883d; color: white; padding: 10px 20px; border-radius: 6px; text-decoration: none; margin: 0 10px; display: inline-block;">
    📚 Documentation
  </a>
</div>

---

<div class="version-footer">
  <h3>🚀 MVidarr v0.9.5</h3>
  <p><strong>UI/UX Excellence & Documentation Complete</strong></p>
  <p>Built with ❤️ for music video enthusiasts</p>
  <small>Licensed under the <a href="https://github.com/prefect421/mvidarr/blob/main/LICENSE" target="_blank">MIT License</a></small>
</div>