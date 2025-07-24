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

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **MariaDB 10.5+** (recommended) or SQLite (for development)
- **FFmpeg** (for video processing)

### Installation

#### Option 1: Automated Installation (Recommended)

**Linux/macOS:**
```bash
chmod +x scripts/install.sh
./scripts/install.sh
```

**Windows:**
```cmd
scripts\install.bat
```

#### Option 2: Manual Installation

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/mvidarr.git
cd mvidarr
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Initialize the database:**
```bash
python scripts/setup_database.sh
```

4. **Start the application:**
```bash
python app.py
```

5. **Access MVidarr:**
   - Open your browser to `http://localhost:5000`
   - Create your admin account on first run

### Docker Deployment

For production deployments, see our [Docker Quick Start Guide](DOCKER-QUICKSTART.md).

## 📚 Documentation

- **[Installation Guide](INSTALLATION_GUIDE.md)** - Comprehensive setup instructions
- **[Quick Start](QUICKSTART.md)** - Get running in 5 minutes
- **[Docker Guide](DOCKER-QUICKSTART.md)** - Container deployment
- **[User Guide](docs/USER-GUIDE.md)** - Feature documentation
- **[API Documentation](docs/api/)** - REST API reference

## 🏗️ Architecture

MVidarr is built with:

- **Backend**: Flask (Python 3.8+)
- **Database**: MariaDB/MySQL or SQLite
- **Frontend**: Modern HTML5/CSS3/JavaScript
- **Media Processing**: FFmpeg, yt-dlp
- **Authentication**: JWT with optional 2FA
- **Security**: bcrypt, CSRF protection, rate limiting

## 🔧 Configuration

Configuration is managed through:
- Database settings (preferred for production)
- Environment variables
- Configuration files in `src/config/`

Key environment variables:
```bash
MVIDARR_SECRET_KEY=your-secret-key
DATABASE_URL=mysql://user:pass@host/db
YOUTUBE_API_KEY=your-youtube-api-key
```

## 🛡️ Security

MVidarr includes enterprise-grade security features:

- **Multi-user authentication** with role-based access
- **Two-factor authentication** (TOTP)
- **Password policies** and strength requirements
- **Session management** with secure cookies
- **Audit logging** for all user actions
- **Rate limiting** and CSRF protection
- **SQL injection prevention** with parameterized queries

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

**MVidarr v0.9** - Built with ❤️ for music video enthusiasts