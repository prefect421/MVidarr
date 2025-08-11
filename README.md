<div align="center">
  <img src="./frontend/src/Content/Images/mvidarr-logo.png" alt="MVidarr Logo" width="200" height="200">
  
  # MVidarr
  
  **A comprehensive music video management and discovery platform** that helps you organize, discover, and stream your music video collection with intelligent artist management and advanced search capabilities.
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
- **🎨 Advanced Theme System** - 7 built-in themes with export/import functionality

## 🆕 What's New in v0.9.3

**Theme System & UI Improvements Release**

- **🎨 Complete Theme Export/Import** - Export individual themes or all themes as JSON files
- **🔧 Simplified Theme Management** - Streamlined single-variant theme system  
- **📹 Enhanced Video Management** - Bulk refresh metadata with preserved navigation context
- **🏗️ Major Code Refactoring** - Videos page reduced by 98.7% through modular components
- **🎯 API-Based Themes** - 7 built-in themes: Default, Cyber, VaporWave, TARDIS, Punk 77, MTV, LCARS
- **💻 Improved JavaScript** - Comprehensive error handling and authentication integration
- **🎛️ Modular UI Components** - Reusable pagination, search, and modal systems

## 🆕 What's New in v0.9.5

**UI/UX Excellence & Documentation Complete Release**

- **🎨 UI/UX Excellence** - Streamlined design with clean headers and improved navigation across all pages
- **📚 Complete Documentation Portfolio** - Comprehensive guides for developers, users, and operations
- **📄 Artists Page Pagination** - Full navigation controls with customizable page sizes  
- **⚡ Performance Optimizations** - 60% CI time reduction and enhanced system reliability
- **🔧 Enhanced Scheduler Service** - Flexible time intervals and improved error handling
- **🐛 Critical Bug Fixes** - SQLAlchemy compatibility, API authentication, and UI issues resolved
- **📊 35 Comprehensive Features** - All core functionality with enterprise-grade security
- **🔍 Verified System Reliability** - Scheduled downloads, video indexing, and theme management

## 🆕 Previous Updates (v0.9.4)

- **🐳 Docker Optimization** - Reduced build time from timeout failures to consistent 8-minute builds
- **📦 Container Size Optimization** - Efficient multi-stage builds with optimized caching (1.41GB optimized size)
- **🔍 Build Monitoring** - Comprehensive Docker build monitoring and validation infrastructure
- **⚡ Build Reliability** - 100% build success rate with automated size monitoring and performance tracking
- **🛠️ Infrastructure** - Enhanced CI/CD workflows with automated Docker monitoring and health checks

## 🚀 Quick Start

### Docker Deployment (Recommended)

**Quick Start:**
```bash
git clone https://github.com/prefect421/mvidarr.git
cd mvidarr
docker-compose up -d
```

**Production Docker Image:**
```bash
# Use the latest optimized release
docker pull ghcr.io/prefect421/mvidarr:v0.9.4
```

**Access the application:**
- Open your browser to `http://localhost:5001`
- Default login: `admin` / `admin` (change immediately)

### Manual Installation

**Prerequisites:**
- Python 3.12+
- MariaDB 11.4+ (recommended)
- FFmpeg (for video processing)

**Installation:**
```bash
# Clone and setup
git clone https://github.com/prefect421/mvidarr.git
cd mvidarr
pip install -r requirements.txt

# Start application
python app.py
```

**Access:** `http://localhost:5000`

## 📚 Documentation

- **[User Guide](docs/USER-GUIDE.md)** - Feature documentation and tutorials
- **[Installation Guide](docs/INSTALLATION-GUIDE.md)** - Comprehensive setup instructions
- **[Docker Optimization Guide](docs/DOCKER_OPTIMIZATION_GUIDE.md)** - Container build optimization and monitoring
- **[Security Implementation](docs/SECURITY_IMPLEMENTATION.md)** - Security features and configuration
- **[Final Project Status](docs/FINAL_PROJECT_STATUS.md)** - Complete feature status and changelog
- **[Authentication Features](docs/AUTHENTICATION_FEATURE_LOG.md)** - User management and security features

## 🏗️ Architecture

MVidarr is built with:

- **Backend**: Flask (Python 3.12+) with modular service architecture
- **Database**: MariaDB 11.4+ with automatic table initialization
- **Frontend**: Modern HTML5/CSS3/JavaScript with responsive design
- **Media Processing**: FFmpeg, yt-dlp for video downloading and processing
- **Authentication**: Secure user management with role-based access control
- **Security**: bcrypt password hashing, session management, audit logging
- **Containerization**: Optimized Docker Compose with multi-stage builds, automated monitoring, and 1.41GB production images

## 🔧 Configuration

Configuration is managed through:
- Database settings (preferred for production)
- Environment variables
- Docker Compose environment files

Key environment variables:
```bash
DB_HOST=mariadb
DB_PASSWORD=secure_password
SECRET_KEY=your-secret-key
IMVDB_API_KEY=your-imvdb-key
YOUTUBE_API_KEY=your-youtube-key
```

## 🛡️ Security

MVidarr includes comprehensive security features:

- **Multi-user authentication** with role-based access (Admin, Manager, User, ReadOnly)
- **Secure password hashing** with bcrypt
- **Session management** with secure tokens and expiration
- **Account lockout** protection against brute force attacks
- **Password reset** functionality with secure tokens
- **Audit logging** for user actions and system events
- **SQL injection prevention** with parameterized queries and ORM
- **Docker security** with non-root containers and isolated networking

## 🎯 Use Cases

- **Personal Music Video Collections** - Organize and stream your collection
- **Music Discovery** - Find new videos through integrated search
- **Media Center Integration** - Works with Plex and other media servers
- **Home Entertainment** - MvTV mode for continuous viewing
- **Music Research** - Advanced search and filtering capabilities

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate` (Windows)
4. Install dev dependencies: `pip install -r requirements.txt`
5. Run tests: `pytest`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **yt-dlp** - Video download and processing
- **IMVDb** - Music video metadata database
- **YouTube API** - Video discovery and streaming
- **Flask** - Web framework
- **MariaDB** - Database engine

## 📞 Support

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Report bugs via GitHub Issues
- **Community**: Join our discussions

---

**MVidarr v0.9.4** - Built with ❤️ for music video enthusiasts
