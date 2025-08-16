---
layout: home
title: Home
---

<div class="home-header">
  <img src="https://raw.githubusercontent.com/prefect421/mvidarr/main/frontend/src/Content/Images/mvidarr-logo.png" alt="MVidarr Logo" width="150" height="150">
  
  <h1>MVidarr</h1>
  
  <p class="tagline"><strong>A comprehensive music video management and discovery platform</strong> that helps you organize, discover, and stream your music video collection with intelligent artist management and advanced search capabilities.</p>
  
  <div class="badges">
    <a href="https://github.com/prefect421/mvidarr/releases/tag/v0.9.6" target="_blank">
      <img src="https://img.shields.io/badge/version-v0.9.6-blue.svg" alt="Version">
    </a>
    <a href="https://github.com/prefect421/mvidarr" target="_blank">
      <img src="https://img.shields.io/github/stars/prefect421/mvidarr.svg" alt="Stars">
    </a>
    <a href="https://github.com/prefect421/mvidarr/blob/main/LICENSE" target="_blank">
      <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
    </a>
    <a href="https://ghcr.io/prefect421/mvidarr:v0.9.6" target="_blank">
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

## 🆕 Recent Updates (v0.9.6) - **LATEST STABLE RELEASE**

**Quality Assurance & Testing Infrastructure Release**

- **🧪 Enterprise Testing Infrastructure** - 185+ comprehensive tests across all testing categories
- **🎨 Enhanced Video Management** - Icon-based video actions with intuitive UI and advanced delete functionality
- **📊 Complete Test Coverage** - Unit, integration, API, functional, visual, and monitoring tests
- **🔍 Advanced Testing Intelligence** - Flaky test detection, performance baselines, and automated maintenance
- **📚 Documentation Excellence** - 6000+ lines of technical documentation with comprehensive guides
- **🛡️ Security Operations** - Zero known vulnerabilities with enterprise-grade automated monitoring
- **⚡ FFmpeg Integration** - Technical metadata extraction with video quality analysis
- **🎭 Playlist Enhancements** - Complete playlist functionality with MvTV integration
- **🔗 Enhanced Navigation** - Clickable artist names and improved user experience

## 🔄 Development Version (v0.9.7-dev)

**Performance & Integration Development**

- **🔧 Advanced Video Filtering** - Multi-criteria search system in development
- **⚡ Performance Optimization** - Database and frontend enhancements
- **📦 Bulk Operations** - Enhanced batch management and processing
- **🎨 Artist Discovery** - Multi-source metadata enrichment system

## 🚀 Quick Start

<div class="quick-start">
  <a href="https://github.com/prefect421/mvidarr/releases/tag/v0.9.6" target="_blank">📥 Download v0.9.6</a>
  <a href="https://ghcr.io/prefect421/mvidarr:v0.9.6" target="_blank">🐳 Docker Image</a>
  <a href="#installation">📚 Installation Guide</a>
</div>

### 🐳 Docker Deployment (Recommended)

```bash
# Quick start with Docker Compose
git clone https://github.com/prefect421/mvidarr.git
cd mvidarr && git checkout v0.9.6
docker-compose up -d

# Or use production image directly
docker pull ghcr.io/prefect421/mvidarr:v0.9.6
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

  <h2>🚀 Current Status: v0.9.6</h2>
  <p><strong>Latest Release</strong>: Quality Assurance & Testing Infrastructure</p>
  <ul>
    <li>✅ Enterprise Testing Infrastructure with 185+ comprehensive tests</li>
    <li>✅ Complete test lifecycle management and automated maintenance</li>
    <li>✅ Zero known vulnerabilities with automated security monitoring</li>
    <li>✅ 6000+ lines of comprehensive technical documentation</li>
    <li>✅ Enhanced video management with playlist functionality</li>
  </ul>
  
  <h2>🔄 Development Status: v0.9.7-dev</h2>
  <p><strong>Next Release</strong>: Performance & Integration (Target: February 2026)</p>
  <ul>
    <li>🔧 Advanced video filtering and search system</li>
    <li>⚡ Database and frontend performance optimization</li>
    <li>📦 Enhanced bulk operations and batch management</li>
    <li>🎨 Multi-source artist discovery and metadata enrichment</li>
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
  <h3>🚀 MVidarr v0.9.6</h3>
  <p><strong>Quality Assurance & Testing Infrastructure</strong></p>
  <p>Built with ❤️ for music video enthusiasts</p>
  <small>Licensed under the <a href="https://github.com/prefect421/mvidarr/blob/main/LICENSE" target="_blank">MIT License</a></small>
</div>
