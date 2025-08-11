# MVidarr Testing Guide

## Overview

This comprehensive testing guide covers all aspects of MVidarr testing including unit tests, integration tests, API testing, security testing, and performance testing. The guide provides practical examples, best practices, and automated testing procedures.

## 🧪 Testing Framework Overview

### Testing Stack
- **Unit Testing**: pytest with fixtures and mocking
- **API Testing**: requests with automated endpoint validation
- **Database Testing**: SQLAlchemy test database with transactions
- **Security Testing**: bandit, safety, semgrep integration
- **Performance Testing**: Custom load testing and profiling tools
- **Browser Testing**: Selenium WebDriver for UI automation

### Test Environment Setup
```bash
# Install testing dependencies
pip install -r requirements-dev.txt

# Additional testing tools
pip install pytest-cov pytest-mock pytest-html
pip install selenium webdriver-manager
pip install locust  # For load testing
```

## 🏗️ Test Environment Configuration

### Test Database Setup
```python
# conftest.py - Pytest configuration
import pytest
from src.database.connection import get_test_db, init_test_database
from src.database.models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    engine = create_engine("sqlite:///test.db", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create test database session with transaction rollback."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def test_app():
    """Create test Flask application."""
    from app import create_app
    app = create_app()
    app.config.update({
        'TESTING': True,
        'DATABASE_URL': 'sqlite:///test.db',
        'SECRET_KEY': 'test-secret-key'
    })
    
    with app.test_client() as client:
        with app.app_context():
            yield client
```

### Environment Configuration
```python
# test_config.py
class TestConfig:
    TESTING = True
    DATABASE_URL = 'sqlite:///test.db'
    SECRET_KEY = 'test-secret-key-for-testing'
    WTF_CSRF_ENABLED = False
    
    # External API mocking
    IMVDB_API_KEY = 'test-imvdb-key'
    YOUTUBE_API_KEY = 'test-youtube-key'
    
    # Disable external services in tests
    ENABLE_EXTERNAL_APIS = False
    ENABLE_DOWNLOADS = False
    ENABLE_SCHEDULING = False
```

## 🔬 Unit Testing

### Model Testing
```python
# test_models.py
import pytest
from src.database.models import Artist, Video, User
from src.database.models import VideoStatus, UserRole

class TestArtistModel:
    def test_artist_creation(self, test_session):
        """Test basic artist creation."""
        artist = Artist(name="Test Artist")
        test_session.add(artist)
        test_session.commit()
        
        assert artist.id is not None
        assert artist.name == "Test Artist"
        assert artist.created_at is not None
        assert len(artist.videos) == 0

    def test_artist_name_uniqueness(self, test_session):
        """Test artist name uniqueness constraint."""
        artist1 = Artist(name="Unique Artist")
        artist2 = Artist(name="Unique Artist")
        
        test_session.add(artist1)
        test_session.commit()
        
        test_session.add(artist2)
        with pytest.raises(Exception):  # IntegrityError expected
            test_session.commit()

    def test_artist_video_relationship(self, test_session):
        """Test artist-video relationship."""
        artist = Artist(name="Test Artist")
        test_session.add(artist)
        test_session.commit()
        
        video = Video(
            title="Test Video",
            artist_id=artist.id,
            url="https://youtube.com/watch?v=test"
        )
        test_session.add(video)
        test_session.commit()
        
        assert len(artist.videos) == 1
        assert artist.videos[0].title == "Test Video"
        assert video.artist.name == "Test Artist"

class TestVideoModel:
    def test_video_creation(self, test_session):
        """Test basic video creation."""
        artist = Artist(name="Test Artist")
        test_session.add(artist)
        test_session.commit()
        
        video = Video(
            title="Test Video",
            artist_id=artist.id,
            url="https://youtube.com/watch?v=test",
            youtube_id="test123",
            status=VideoStatus.WANTED
        )
        test_session.add(video)
        test_session.commit()
        
        assert video.id is not None
        assert video.title == "Test Video"
        assert video.status == VideoStatus.WANTED
        assert video.youtube_id == "test123"

    def test_video_status_enum(self, test_session):
        """Test video status enumeration."""
        artist = Artist(name="Test Artist")
        test_session.add(artist)
        test_session.commit()
        
        for status in VideoStatus:
            video = Video(
                title=f"Test Video {status.value}",
                artist_id=artist.id,
                status=status
            )
            test_session.add(video)
        
        test_session.commit()
        
        videos = test_session.query(Video).all()
        assert len(videos) == len(VideoStatus)

class TestUserModel:
    def test_user_creation(self, test_session):
        """Test user creation with password hashing."""
        from werkzeug.security import check_password_hash
        
        user = User(username="testuser", role=UserRole.USER)
        user.set_password("securepassword123")
        
        test_session.add(user)
        test_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.role == UserRole.USER
        assert user.is_active is True
        assert check_password_hash(user.password_hash, "securepassword123")

    def test_user_authentication(self, test_session):
        """Test user authentication methods."""
        user = User(username="testuser")
        user.set_password("correct_password")
        
        test_session.add(user)
        test_session.commit()
        
        assert user.check_password("correct_password") is True
        assert user.check_password("wrong_password") is False
        
        # Test account locking
        for _ in range(5):  # Assuming max 5 failed attempts
            user.record_failed_login()
        
        assert user.is_locked() is True
```

### Service Testing
```python
# test_services.py
import pytest
from unittest.mock import Mock, patch
from src.services.artist_service import ArtistService
from src.services.video_discovery_service import VideoDiscoveryService
from src.services.settings_service import SettingsService

class TestArtistService:
    def test_create_artist(self, test_session):
        """Test artist creation through service."""
        service = ArtistService()
        
        artist_id = service.create_artist("Test Artist")
        
        artist = test_session.query(Artist).get(artist_id)
        assert artist.name == "Test Artist"
        assert artist.folder_path is not None

    def test_get_artist_by_name(self, test_session):
        """Test artist retrieval by name."""
        service = ArtistService()
        
        # Create test artist
        artist_id = service.create_artist("Search Artist")
        
        # Test retrieval
        found_artist = service.get_artist_by_name("Search Artist")
        assert found_artist.id == artist_id
        assert found_artist.name == "Search Artist"

    def test_update_artist(self, test_session):
        """Test artist information update."""
        service = ArtistService()
        
        # Create artist
        artist_id = service.create_artist("Original Name")
        
        # Update artist
        updates = {
            'bio': 'Updated bio information',
            'thumbnail_url': 'https://example.com/thumb.jpg'
        }
        service.update_artist(artist_id, updates)
        
        # Verify updates
        artist = service.get_artist(artist_id)
        assert artist.bio == 'Updated bio information'
        assert artist.thumbnail_url == 'https://example.com/thumb.jpg'

class TestVideoDiscoveryService:
    @patch('src.services.imvdb_service.IMVDBService.search_artist_videos')
    @patch('src.services.youtube_service.YouTubeService.search_videos')
    def test_discover_videos_for_artist(self, mock_youtube, mock_imvdb, test_session):
        """Test video discovery with mocked external services."""
        service = VideoDiscoveryService()
        
        # Create test artist
        artist = Artist(name="Test Artist")
        test_session.add(artist)
        test_session.commit()
        
        # Mock external service responses
        mock_imvdb.return_value = [
            {
                'title': 'Song One',
                'imvdb_id': 123,
                'url': 'https://imvdb.com/video/123'
            }
        ]
        
        mock_youtube.return_value = [
            {
                'title': 'Song Two',
                'youtube_id': 'abc123',
                'url': 'https://youtube.com/watch?v=abc123'
            }
        ]
        
        # Test discovery
        discovered = service.discover_videos_for_artist(artist.id)
        
        assert len(discovered) == 2
        assert any(v['title'] == 'Song One' for v in discovered)
        assert any(v['title'] == 'Song Two' for v in discovered)
        
        # Verify external services were called
        mock_imvdb.assert_called_once_with("Test Artist")
        mock_youtube.assert_called_once()

class TestSettingsService:
    def test_settings_caching(self, test_session):
        """Test settings service caching behavior."""
        service = SettingsService()
        
        # Set a setting
        service.set('test_key', 'test_value')
        
        # Retrieve setting (should use cache)
        value1 = service.get('test_key')
        value2 = service.get('test_key')
        
        assert value1 == 'test_value'
        assert value2 == 'test_value'
        
        # Clear cache and verify reload
        service.reload_cache()
        value3 = service.get('test_key')
        assert value3 == 'test_value'
```

## 🌐 API Testing

### RESTful Endpoint Testing
```python
# test_api.py
import json
import pytest
from flask import url_for

class TestArtistsAPI:
    def test_list_artists_empty(self, test_app):
        """Test listing artists when none exist."""
        response = test_app.get('/api/artists')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['artists'] == []
        assert data['total'] == 0

    def test_create_artist(self, test_app):
        """Test artist creation via API."""
        artist_data = {'name': 'API Test Artist'}
        
        response = test_app.post('/api/artists', 
                               data=json.dumps(artist_data),
                               content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'API Test Artist'
        assert 'id' in data

    def test_get_artist(self, test_app):
        """Test retrieving specific artist."""
        # Create artist first
        artist_data = {'name': 'Specific Artist'}
        create_response = test_app.post('/api/artists',
                                      data=json.dumps(artist_data),
                                      content_type='application/json')
        artist_id = json.loads(create_response.data)['id']
        
        # Retrieve artist
        response = test_app.get(f'/api/artists/{artist_id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Specific Artist'
        assert data['id'] == artist_id

    def test_artist_not_found(self, test_app):
        """Test retrieving non-existent artist."""
        response = test_app.get('/api/artists/99999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data

class TestVideosAPI:
    def test_list_videos(self, test_app):
        """Test video listing with pagination."""
        response = test_app.get('/api/videos?page=1&per_page=50')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'videos' in data
        assert 'total' in data
        assert 'page' in data

    def test_video_filtering(self, test_app):
        """Test video filtering by status."""
        response = test_app.get('/api/videos?status=WANTED')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify all returned videos have WANTED status
        for video in data['videos']:
            assert video['status'] == 'WANTED'

    def test_video_search(self, test_app):
        """Test video search functionality."""
        search_term = "test song"
        response = test_app.get(f'/api/videos?search={search_term}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify search results contain search term
        for video in data['videos']:
            assert (search_term.lower() in video['title'].lower() or 
                   search_term.lower() in video['artist_name'].lower())

class TestBulkOperations:
    def test_bulk_video_status_update(self, test_app):
        """Test bulk video status update."""
        # First, create some test videos
        # This would typically be done in a fixture
        
        bulk_data = {
            'video_ids': [1, 2, 3],
            'status': 'WANTED'
        }
        
        response = test_app.put('/api/videos/bulk/status',
                              data=json.dumps(bulk_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['updated_count'] >= 0  # May be 0 if no videos exist

    def test_bulk_download_queue(self, test_app):
        """Test bulk download queueing."""
        bulk_data = {
            'video_ids': [1, 2, 3]
        }
        
        response = test_app.post('/api/videos/bulk/download',
                               data=json.dumps(bulk_data),
                               content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'queued_count' in data

class TestAuthentication:
    def test_login_required_endpoints(self, test_app):
        """Test endpoints that require authentication."""
        # This test assumes authentication is enabled
        protected_endpoints = [
            '/api/artists',
            '/api/videos',
            '/api/settings/test_key'
        ]
        
        for endpoint in protected_endpoints:
            response = test_app.get(endpoint)
            # Response should be 401 if auth is required, 200 if not
            assert response.status_code in [200, 401]

    def test_role_based_access(self, test_app):
        """Test role-based access control."""
        # Admin-only endpoints
        admin_endpoints = [
            '/api/users',
            '/api/system/restart'
        ]
        
        for endpoint in admin_endpoints:
            response = test_app.get(endpoint)
            # Should require authentication and proper role
            assert response.status_code in [401, 403, 404]  # 404 if endpoint doesn't exist
```

### API Performance Testing
```python
# test_api_performance.py
import time
import pytest
import concurrent.futures
from statistics import mean, median

class TestAPIPerformance:
    def test_artist_list_performance(self, test_app):
        """Test artist listing performance."""
        start_time = time.time()
        response = test_app.get('/api/artists')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 1.0  # Should respond within 1 second

    def test_video_search_performance(self, test_app):
        """Test video search performance."""
        start_time = time.time()
        response = test_app.get('/api/videos?search=test&page=1&per_page=50')
        end_time = time.time()
        
        assert response.status_code == 200
        assert (end_time - start_time) < 2.0  # Search should complete within 2 seconds

    def test_concurrent_api_requests(self, test_app):
        """Test API performance under concurrent load."""
        def make_request():
            start = time.time()
            response = test_app.get('/api/artists')
            end = time.time()
            return {
                'status_code': response.status_code,
                'response_time': end - start
            }
        
        # Test with 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
        
        # All requests should succeed
        assert all(r['status_code'] == 200 for r in results)
        
        # Check response time statistics
        response_times = [r['response_time'] for r in results]
        avg_time = mean(response_times)
        median_time = median(response_times)
        
        assert avg_time < 1.0  # Average should be under 1 second
        assert median_time < 0.5  # Median should be under 0.5 seconds
```

## 🖥️ Frontend Testing

### Browser Automation Testing
```python
# test_frontend.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

@pytest.fixture
def browser():
    """Create browser instance for testing."""
    options = Options()
    options.add_argument('--headless')  # Run in headless mode for CI
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    yield driver
    driver.quit()

class TestUserInterface:
    def test_main_page_loads(self, browser, test_app):
        """Test main page loading."""
        browser.get('http://localhost:5000')
        
        assert "MVidarr" in browser.title
        
        # Check for main navigation elements
        nav_elements = browser.find_elements(By.CSS_SELECTOR, ".navbar a")
        nav_text = [el.text for el in nav_elements]
        
        expected_nav = ["Artists", "Videos", "Downloads", "Settings"]
        for item in expected_nav:
            assert any(item in text for text in nav_text)

    def test_artist_page_functionality(self, browser, test_app):
        """Test artist page functionality."""
        browser.get('http://localhost:5000/artists')
        
        # Test search functionality
        search_box = browser.find_element(By.CSS_SELECTOR, "input[type='search']")
        search_box.send_keys("test artist")
        search_box.submit()
        
        # Wait for results
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".artist-list"))
        )

    def test_add_artist_modal(self, browser, test_app):
        """Test add artist modal functionality."""
        browser.get('http://localhost:5000/artists')
        
        # Open add artist modal
        add_button = browser.find_element(By.CSS_SELECTOR, ".add-artist-btn")
        add_button.click()
        
        # Wait for modal to appear
        modal = WebDriverWait(browser, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal"))
        )
        
        # Fill in artist name
        name_input = modal.find_element(By.CSS_SELECTOR, "input[name='artist_name']")
        name_input.send_keys("Test UI Artist")
        
        # Submit form
        submit_button = modal.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for success message
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".toast-success"))
        )

class TestVideoManagement:
    def test_video_list_display(self, browser, test_app):
        """Test video list display and functionality."""
        browser.get('http://localhost:5000/videos')
        
        # Check for video list elements
        video_list = browser.find_element(By.CSS_SELECTOR, ".video-list")
        assert video_list is not None
        
        # Test filtering
        status_filter = browser.find_element(By.CSS_SELECTOR, "select[name='status']")
        status_filter.click()
        
        wanted_option = browser.find_element(By.CSS_SELECTOR, "option[value='WANTED']")
        wanted_option.click()
        
        # Wait for filtered results
        WebDriverWait(browser, 10).until(
            EC.staleness_of(video_list)
        )

    def test_bulk_operations(self, browser, test_app):
        """Test bulk video operations."""
        browser.get('http://localhost:5000/videos')
        
        # Select multiple videos
        checkboxes = browser.find_elements(By.CSS_SELECTOR, "input[type='checkbox'][name='video_ids']")
        
        if checkboxes:
            # Select first few videos
            for checkbox in checkboxes[:3]:
                checkbox.click()
            
            # Open bulk actions
            bulk_actions = browser.find_element(By.CSS_SELECTOR, ".bulk-actions select")
            bulk_actions.click()
            
            # Select an action
            download_option = browser.find_element(By.CSS_SELECTOR, "option[value='download']")
            download_option.click()
            
            # Execute bulk action
            execute_button = browser.find_element(By.CSS_SELECTOR, ".bulk-execute-btn")
            execute_button.click()
```

### JavaScript Unit Testing
```javascript
// static/js/tests/test_main.js
describe('MVidarr JavaScript Functions', function() {
    describe('APIClient', function() {
        it('should make successful API requests', function() {
            // Mock fetch
            global.fetch = jest.fn().mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ success: true })
            });
            
            return APIClient.request('/test').then(data => {
                expect(data.success).toBe(true);
                expect(fetch).toHaveBeenCalledWith('/api/test', {
                    headers: { 'Content-Type': 'application/json' }
                });
            });
        });
        
        it('should handle API errors', function() {
            global.fetch = jest.fn().mockResolvedValue({
                ok: false,
                status: 500
            });
            
            return APIClient.request('/test').catch(error => {
                expect(error.message).toContain('API request failed: 500');
            });
        });
    });
    
    describe('SettingsManager', function() {
        beforeEach(function() {
            global.fetch = jest.fn();
        });
        
        it('should get settings values', function() {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ value: 'test_value' })
            });
            
            return SettingsManager.get('test_key').then(value => {
                expect(value).toBe('test_value');
                expect(fetch).toHaveBeenCalledWith('/api/settings/test_key');
            });
        });
        
        it('should set settings values', function() {
            global.fetch.mockResolvedValue({
                ok: true,
                json: () => Promise.resolve({ success: true })
            });
            
            const eventSpy = jest.spyOn(document, 'dispatchEvent');
            
            return SettingsManager.set('test_key', 'new_value').then(() => {
                expect(fetch).toHaveBeenCalledWith('/api/settings/test_key', {
                    method: 'PUT',
                    body: JSON.stringify({ value: 'new_value' }),
                    headers: { 'Content-Type': 'application/json' }
                });
                expect(eventSpy).toHaveBeenCalledWith(
                    expect.objectContaining({
                        type: 'settingsChanged',
                        detail: { key: 'test_key', value: 'new_value' }
                    })
                );
            });
        });
    });
});
```

## 🛡️ Security Testing

### Automated Security Testing
```python
# test_security.py
import pytest
from flask import session
import json

class TestAuthentication:
    def test_password_hashing(self, test_app):
        """Test password hashing security."""
        from werkzeug.security import check_password_hash
        from src.database.models import User
        
        user = User(username="test_user")
        user.set_password("secure_password_123")
        
        # Password should be hashed
        assert user.password_hash != "secure_password_123"
        
        # Verify hashing works
        assert check_password_hash(user.password_hash, "secure_password_123")
        assert not check_password_hash(user.password_hash, "wrong_password")

    def test_session_security(self, test_app):
        """Test session security measures."""
        with test_app.session_transaction() as sess:
            sess['user_id'] = 1
            sess['authenticated'] = True
        
        # Test session data is properly secured
        response = test_app.get('/api/settings/test_key')
        assert response.status_code in [200, 401]  # Depends on auth config

    def test_csrf_protection(self, test_app):
        """Test CSRF protection on forms."""
        # This test would check CSRF token validation
        response = test_app.post('/api/artists',
                               data=json.dumps({'name': 'CSRF Test'}),
                               content_type='application/json')
        
        # Should handle CSRF appropriately
        assert response.status_code in [200, 201, 403, 422]

class TestInputValidation:
    def test_sql_injection_prevention(self, test_app):
        """Test SQL injection prevention."""
        malicious_input = "'; DROP TABLE artists; --"
        
        response = test_app.get(f'/api/artists?search={malicious_input}')
        
        # Should not cause server error
        assert response.status_code in [200, 400]

    def test_xss_prevention(self, test_app):
        """Test XSS prevention in API responses."""
        xss_payload = "<script>alert('xss')</script>"
        
        response = test_app.post('/api/artists',
                               data=json.dumps({'name': xss_payload}),
                               content_type='application/json')
        
        if response.status_code == 201:
            data = json.loads(response.data)
            # XSS payload should be escaped or sanitized
            assert '<script>' not in data.get('name', '')

    def test_file_upload_security(self, test_app):
        """Test file upload security measures."""
        # Test malicious file upload
        malicious_file = {
            'thumbnail': (
                io.BytesIO(b'<?php echo "malicious code"; ?>'),
                'malicious.php'
            )
        }
        
        response = test_app.post('/api/artists/1/thumbnail',
                               data=malicious_file,
                               content_type='multipart/form-data')
        
        # Should reject malicious files
        assert response.status_code in [400, 413, 415]

class TestAPISecurityHeaders:
    def test_security_headers_present(self, test_app):
        """Test presence of security headers."""
        response = test_app.get('/api/artists')
        
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection'
        ]
        
        for header in expected_headers:
            assert header in response.headers

    def test_content_type_validation(self, test_app):
        """Test content type validation."""
        # Send request with incorrect content type
        response = test_app.post('/api/artists',
                               data='{"name": "test"}',
                               content_type='text/plain')
        
        # Should reject or handle gracefully
        assert response.status_code in [400, 415]
```

## 🏋️ Performance Testing

### Load Testing with Locust
```python
# locustfile.py
from locust import HttpUser, task, between
import json
import random

class MVidarrUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Called when user starts."""
        # Perform login if authentication is required
        pass
    
    @task(3)
    def view_artists(self):
        """View artists list."""
        self.client.get("/api/artists")
    
    @task(5)
    def view_videos(self):
        """View videos list."""
        page = random.randint(1, 10)
        self.client.get(f"/api/videos?page={page}&per_page=50")
    
    @task(2)
    def search_videos(self):
        """Search for videos."""
        search_terms = ["rock", "pop", "metal", "jazz", "blues"]
        term = random.choice(search_terms)
        self.client.get(f"/api/videos?search={term}")
    
    @task(1)
    def view_artist_details(self):
        """View specific artist."""
        artist_id = random.randint(1, 100)
        self.client.get(f"/api/artists/{artist_id}")
    
    @task(1)
    def add_artist(self):
        """Add new artist."""
        artist_name = f"Load Test Artist {random.randint(1, 10000)}"
        self.client.post("/api/artists",
                        json={"name": artist_name},
                        headers={"Content-Type": "application/json"})

class AdminUser(HttpUser):
    weight = 1  # Only 10% of users are admins
    wait_time = between(5, 15)
    
    @task
    def admin_operations(self):
        """Admin-specific operations."""
        self.client.get("/api/system/status")
        self.client.get("/api/users")

# Run with: locust -f locustfile.py --host=http://localhost:5000
```

### Database Performance Testing
```python
# test_database_performance.py
import time
import pytest
from src.database.models import Artist, Video
from sqlalchemy import func

class TestDatabasePerformance:
    def test_bulk_insert_performance(self, test_session):
        """Test bulk insert performance."""
        start_time = time.time()
        
        # Insert 1000 artists
        artists = [Artist(name=f"Bulk Artist {i}") for i in range(1000)]
        test_session.add_all(artists)
        test_session.commit()
        
        end_time = time.time()
        insert_time = end_time - start_time
        
        assert insert_time < 5.0  # Should complete within 5 seconds
        assert test_session.query(Artist).count() == 1000

    def test_query_performance(self, test_session):
        """Test query performance with large dataset."""
        # Create test data
        artists = [Artist(name=f"Query Artist {i}") for i in range(100)]
        test_session.add_all(artists)
        test_session.commit()
        
        # Add videos for each artist
        for artist in artists:
            videos = [Video(
                title=f"Video {j}",
                artist_id=artist.id,
                url=f"https://example.com/video{j}"
            ) for j in range(50)]
            test_session.add_all(videos)
        test_session.commit()
        
        # Test query performance
        start_time = time.time()
        
        result = test_session.query(Artist).join(Video).filter(
            Artist.name.like('%Query Artist%')
        ).all()
        
        end_time = time.time()
        query_time = end_time - start_time
        
        assert query_time < 1.0  # Should complete within 1 second
        assert len(result) > 0

    def test_pagination_performance(self, test_session):
        """Test pagination performance."""
        # Create large dataset
        videos = [Video(
            title=f"Pagination Video {i}",
            artist_id=1,  # Assuming artist exists
            url=f"https://example.com/video{i}"
        ) for i in range(5000)]
        test_session.add_all(videos)
        test_session.commit()
        
        # Test different pagination approaches
        page_size = 50
        
        # Offset-based pagination
        start_time = time.time()
        offset_results = test_session.query(Video).offset(1000).limit(page_size).all()
        offset_time = time.time() - start_time
        
        # Cursor-based pagination
        start_time = time.time()
        cursor_results = test_session.query(Video).filter(
            Video.id > 1000
        ).limit(page_size).all()
        cursor_time = time.time() - start_time
        
        # Cursor-based should be faster for large offsets
        assert cursor_time < offset_time
        assert len(offset_results) == page_size
        assert len(cursor_results) == page_size
```

## 📊 Test Coverage and Reporting

### Coverage Configuration
```ini
# .coveragerc
[run]
source = src
omit = 
    */tests/*
    */test_*
    */conftest.py
    */__init__.py
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:

[html]
directory = htmlcov
```

### Running Tests with Coverage
```bash
# Run all tests with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# Run specific test categories
pytest tests/test_models.py -v
pytest tests/test_api.py -v
pytest tests/test_services.py -v

# Run with parallel execution
pytest -n auto  # Requires pytest-xdist

# Generate HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Continuous Integration Testing
```yaml
# .github/workflows/testing.yml
name: Comprehensive Testing

on:
  push:
    branches: [ dev, main ]
  pull_request:
    branches: [ dev, main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ --cov=src --cov-report=xml
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
    
    - name: Run security tests
      run: |
        bandit -r src/
        safety check --requirement requirements.txt
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true

  frontend-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: npm install
    
    - name: Run JavaScript tests
      run: npm test
    
    - name: Run browser tests
      run: |
        # Install Chrome for Selenium
        sudo apt-get install -y google-chrome-stable
        pytest tests/frontend/ --headless

  performance-tests:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements-dev.txt
        pip install locust
    
    - name: Run performance tests
      run: |
        pytest tests/performance/ -v
    
    - name: Run load tests
      run: |
        # Start application in background
        python app.py &
        sleep 10
        
        # Run locust load test
        locust -f locustfile.py --headless -u 10 -r 2 -t 60s --host=http://localhost:5000
```

## 📋 Testing Checklist

### Pre-commit Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Code coverage above 80%
- [ ] Security scans clean
- [ ] Performance tests within limits

### Pre-release Testing
- [ ] Full test suite passes
- [ ] Browser compatibility tested
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] Documentation updated

### Manual Testing Areas
- [ ] User authentication flows
- [ ] File upload/download functionality
- [ ] External API integrations
- [ ] Error handling and recovery
- [ ] Mobile responsiveness
- [ ] Accessibility compliance

## 🔗 Testing Resources

### Documentation Links
- **API Testing**: `API_DOCUMENTATION.md`
- **Security Testing**: `SECURITY_AUDIT.md`
- **Performance Testing**: `PERFORMANCE_OPTIMIZATION.md`
- **User Testing**: `USER_WORKFLOWS.md`

### External Tools
- **pytest**: https://pytest.org/
- **Selenium**: https://selenium.dev/
- **Locust**: https://locust.io/
- **Coverage.py**: https://coverage.readthedocs.io/

This comprehensive testing guide ensures MVidarr maintains high quality, security, and performance standards through systematic testing procedures.