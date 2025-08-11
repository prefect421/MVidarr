# MVidarr Performance Optimization Guide

## Overview

This guide provides comprehensive strategies for optimizing MVidarr performance across database operations, frontend rendering, API responses, and system resources. It includes specific configuration recommendations, monitoring techniques, and troubleshooting procedures.

## 🎯 Performance Targets

### Response Time Goals
- **Main page load**: < 2 seconds
- **API endpoints**: < 500ms (search < 1s)
- **Video listing**: < 1 second for 1000+ videos
- **Search operations**: < 1 second
- **Download initialization**: < 5 seconds

### Resource Usage Guidelines
- **Memory usage**: < 1GB for typical libraries (5000+ videos)
- **CPU usage**: < 20% during normal operation
- **Database response**: < 100ms for common queries
- **Disk I/O**: < 100MB/s during active downloads

## 🗄️ Database Performance Optimization

### Connection Pool Configuration

#### Optimal Pool Settings
```python
# For small deployments (< 1000 videos)
DB_POOL_SIZE = 5
DB_MAX_OVERFLOW = 10
DB_POOL_TIMEOUT = 30

# For medium deployments (1000-10000 videos)  
DB_POOL_SIZE = 10
DB_MAX_OVERFLOW = 20
DB_POOL_TIMEOUT = 30

# For large deployments (10000+ videos)
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 40
DB_POOL_TIMEOUT = 60
```

#### Connection Pool Monitoring
```python
# Check pool status
from src.database.connection import engine
pool = engine.pool

print(f"Pool size: {pool.size()}")
print(f"Checked out: {pool.checkedout()}")
print(f"Overflow: {pool.overflow()}")
print(f"Invalid: {pool.invalid()}")
```

### Database Query Optimization

#### Index Strategy
```sql
-- Primary indexes (automatically created)
CREATE INDEX IF NOT EXISTS idx_artists_name ON artists(name);
CREATE INDEX IF NOT EXISTS idx_videos_artist_id ON videos(artist_id);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);

-- Performance indexes for common queries
CREATE INDEX IF NOT EXISTS idx_videos_title ON videos(title);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at);
CREATE INDEX IF NOT EXISTS idx_videos_youtube_id ON videos(youtube_id);
CREATE INDEX IF NOT EXISTS idx_videos_imvdb_id ON videos(imvdb_id);

-- Composite indexes for complex queries
CREATE INDEX IF NOT EXISTS idx_videos_artist_status ON videos(artist_id, status);
CREATE INDEX IF NOT EXISTS idx_videos_status_created ON videos(status, created_at);
```

#### Query Optimization Techniques

**Efficient Pagination:**
```python
# Bad: OFFSET can be slow for large datasets
videos = session.query(Video).offset(1000).limit(50).all()

# Better: Use cursor-based pagination
last_id = request.args.get('last_id', 0)
videos = session.query(Video).filter(Video.id > last_id).limit(50).all()
```

**Optimized Filtering:**
```python
# Bad: Loading all records then filtering in Python
artists = session.query(Artist).all()
filtered = [a for a in artists if 'rock' in a.name.lower()]

# Good: Database-level filtering
artists = session.query(Artist).filter(
    Artist.name.ilike('%rock%')
).all()
```

**Eager Loading Relationships:**
```python
# Bad: N+1 query problem
artists = session.query(Artist).all()
for artist in artists:
    videos = artist.videos  # Separate query for each artist

# Good: Eager loading
artists = session.query(Artist).options(
    joinedload(Artist.videos)
).all()
```

### Database Maintenance

#### Regular Maintenance Tasks
```sql
-- SQLite optimization
PRAGMA optimize;
VACUUM;
REINDEX;

-- MySQL/MariaDB optimization  
OPTIMIZE TABLE artists, videos, downloads, settings;
ANALYZE TABLE artists, videos, downloads, settings;
```

#### Automated Maintenance Script
```python
# scripts/db_maintenance.py
import schedule
import time
from src.database.connection import get_db

def optimize_database():
    """Run database optimization tasks."""
    with get_db() as session:
        # SQLite
        if session.bind.dialect.name == 'sqlite':
            session.execute('PRAGMA optimize')
            session.execute('VACUUM')
        
        # MySQL/MariaDB
        elif session.bind.dialect.name == 'mysql':
            tables = ['artists', 'videos', 'downloads', 'settings']
            for table in tables:
                session.execute(f'OPTIMIZE TABLE {table}')
                session.execute(f'ANALYZE TABLE {table}')

# Schedule weekly optimization
schedule.every().sunday.at("02:00").do(optimize_database)
```

## 🖥️ Frontend Performance Optimization

### JavaScript Optimization

#### Virtualization for Large Lists
```javascript
// Implement virtual scrolling for large video lists
class VirtualizedVideoList {
    constructor(container, items, itemHeight = 100) {
        this.container = container;
        this.items = items;
        this.itemHeight = itemHeight;
        this.visibleStart = 0;
        this.visibleEnd = 0;
        this.scrollTop = 0;
        
        this.render();
        this.setupScrollListener();
    }
    
    calculateVisibleRange() {
        const containerHeight = this.container.clientHeight;
        const scrollTop = this.container.scrollTop;
        
        this.visibleStart = Math.floor(scrollTop / this.itemHeight);
        this.visibleEnd = Math.min(
            this.visibleStart + Math.ceil(containerHeight / this.itemHeight) + 1,
            this.items.length
        );
    }
    
    render() {
        this.calculateVisibleRange();
        
        // Only render visible items
        const visibleItems = this.items.slice(this.visibleStart, this.visibleEnd);
        
        // Update DOM with only visible items
        this.updateDOM(visibleItems);
    }
}
```

#### Efficient DOM Manipulation
```javascript
// Bad: Multiple DOM updates
for (let video of videos) {
    const element = document.createElement('div');
    element.innerHTML = videoTemplate(video);
    container.appendChild(element);
}

// Good: Batch DOM updates
const fragment = document.createDocumentFragment();
for (let video of videos) {
    const element = document.createElement('div');
    element.innerHTML = videoTemplate(video);
    fragment.appendChild(element);
}
container.appendChild(fragment);
```

#### API Request Optimization
```javascript
// Implement request debouncing for search
class SearchManager {
    constructor(searchInput, searchCallback, delay = 300) {
        this.searchInput = searchInput;
        this.searchCallback = searchCallback;
        this.delay = delay;
        this.timeoutId = null;
        
        this.setupSearch();
    }
    
    setupSearch() {
        this.searchInput.addEventListener('input', (event) => {
            clearTimeout(this.timeoutId);
            
            this.timeoutId = setTimeout(() => {
                this.searchCallback(event.target.value);
            }, this.delay);
        });
    }
}

// Request caching
class APICache {
    constructor(ttl = 300000) { // 5 minutes
        this.cache = new Map();
        this.ttl = ttl;
    }
    
    get(key) {
        const cached = this.cache.get(key);
        if (cached && (Date.now() - cached.timestamp < this.ttl)) {
            return cached.data;
        }
        return null;
    }
    
    set(key, data) {
        this.cache.set(key, {
            data: data,
            timestamp: Date.now()
        });
    }
}
```

### CSS and Asset Optimization

#### CSS Performance
```css
/* Use efficient selectors */
/* Bad: Overly specific selectors */
.container .video-list .video-item .video-title { }

/* Good: Simple, specific selectors */
.video-title { }

/* Optimize animations */
/* Bad: Animating layout properties */
.video-card {
    transition: width 0.3s, height 0.3s;
}

/* Good: Animating composite properties */
.video-card {
    transition: transform 0.3s, opacity 0.3s;
}

/* Use CSS containment for performance */
.video-list-item {
    contain: layout style paint;
}
```

#### Image Optimization
```python
# Thumbnail optimization service
class ThumbnailOptimizer:
    def __init__(self):
        self.sizes = {
            'small': (150, 100),
            'medium': (300, 200), 
            'large': (600, 400)
        }
    
    def optimize_thumbnail(self, image_path, output_dir):
        """Generate optimized thumbnails in multiple sizes."""
        from PIL import Image
        
        with Image.open(image_path) as img:
            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            for size_name, dimensions in self.sizes.items():
                # Resize with high-quality resampling
                resized = img.resize(dimensions, Image.Resampling.LANCZOS)
                
                # Optimize file size
                output_path = f"{output_dir}/{size_name}_{Path(image_path).name}"
                resized.save(output_path, 'JPEG', quality=85, optimize=True)
```

## ⚡ API Performance Optimization

### Response Time Optimization

#### Caching Strategy
```python
from functools import lru_cache
from flask_caching import Cache

# Application-level caching
cache = Cache(config={'CACHE_TYPE': 'simple'})

@cache.memoize(timeout=300)  # 5-minute cache
def get_artist_videos(artist_id):
    """Cache expensive artist video queries."""
    with get_db() as session:
        return session.query(Video).filter(
            Video.artist_id == artist_id
        ).all()

# Method-level caching
class VideoService:
    @lru_cache(maxsize=1000)
    def get_video_metadata(self, video_id):
        """Cache video metadata lookups."""
        # Expensive metadata lookup
        pass
```

#### Pagination and Filtering
```python
# Efficient pagination implementation
def get_paginated_videos(page=1, per_page=50, filters=None):
    """Optimized pagination with filtering."""
    with get_db() as session:
        query = session.query(Video)
        
        # Apply filters efficiently
        if filters:
            if filters.get('artist_id'):
                query = query.filter(Video.artist_id == filters['artist_id'])
            if filters.get('status'):
                query = query.filter(Video.status == filters['status'])
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(Video.title.ilike(search_term))
        
        # Count total results efficiently
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        videos = query.offset(offset).limit(per_page).all()
        
        return {
            'videos': videos,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page
        }
```

#### Asynchronous Processing
```python
import asyncio
import concurrent.futures

class AsyncVideoDiscovery:
    def __init__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    
    async def discover_videos_async(self, artist_ids):
        """Discover videos for multiple artists concurrently."""
        loop = asyncio.get_event_loop()
        
        # Create tasks for each artist
        tasks = []
        for artist_id in artist_ids:
            task = loop.run_in_executor(
                self.executor,
                self.discover_videos_for_artist,
                artist_id
            )
            tasks.append(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = []
        failed = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed.append({
                    'artist_id': artist_ids[i],
                    'error': str(result)
                })
            else:
                successful.extend(result)
        
        return {
            'discovered_videos': successful,
            'failed_artists': failed
        }
```

## 🔧 System Resource Optimization

### Memory Management

#### Memory Usage Monitoring
```python
import psutil
import gc
from src.utils.logger import get_logger

logger = get_logger("performance.memory")

class MemoryMonitor:
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = self.get_memory_usage()
    
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def check_memory_usage(self, operation_name=""):
        """Log memory usage and trigger cleanup if needed."""
        current_memory = self.get_memory_usage()
        memory_increase = current_memory - self.baseline_memory
        
        logger.info(f"Memory usage: {current_memory:.1f}MB "
                   f"(+{memory_increase:.1f}MB) - {operation_name}")
        
        # Trigger garbage collection if memory usage is high
        if current_memory > 1000:  # 1GB threshold
            logger.warning("High memory usage detected, running garbage collection")
            collected = gc.collect()
            logger.info(f"Garbage collection freed {collected} objects")
        
        return current_memory

# Usage in services
memory_monitor = MemoryMonitor()

def bulk_video_processing():
    memory_monitor.check_memory_usage("bulk_processing_start")
    
    # Process videos...
    
    memory_monitor.check_memory_usage("bulk_processing_complete")
```

#### Memory-Efficient Data Processing
```python
def process_large_dataset(query):
    """Process large datasets without loading everything into memory."""
    batch_size = 1000
    
    with get_db() as session:
        # Use yield_per for memory-efficient iteration
        for video in session.query(Video).yield_per(batch_size):
            # Process individual video
            process_video(video)
            
            # Periodically clear session to free memory
            if video.id % batch_size == 0:
                session.expunge_all()

def streaming_json_response(data_generator):
    """Stream JSON responses for large datasets."""
    def generate():
        yield '{"items": ['
        first = True
        for item in data_generator:
            if not first:
                yield ','
            yield json.dumps(item.to_dict())
            first = False
        yield ']}'
    
    return Response(
        generate(),
        content_type='application/json',
        headers={'Transfer-Encoding': 'chunked'}
    )
```

### CPU Optimization

#### Background Task Management
```python
import threading
import queue
from concurrent.futures import ThreadPoolExecutor

class TaskQueue:
    def __init__(self, max_workers=3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.pending_tasks = queue.Queue()
        self.active_tasks = {}
    
    def submit_task(self, task_func, *args, **kwargs):
        """Submit task for background execution."""
        future = self.executor.submit(task_func, *args, **kwargs)
        task_id = id(future)
        
        self.active_tasks[task_id] = {
            'future': future,
            'started_at': time.time(),
            'function': task_func.__name__
        }
        
        # Cleanup completed tasks
        future.add_done_callback(lambda f: self.active_tasks.pop(task_id, None))
        
        return future
    
    def get_task_status(self):
        """Get status of all active tasks."""
        status = []
        for task_id, task_info in self.active_tasks.items():
            status.append({
                'id': task_id,
                'function': task_info['function'],
                'running_time': time.time() - task_info['started_at'],
                'done': task_info['future'].done()
            })
        return status

# Global task queue
task_queue = TaskQueue(max_workers=3)

# Usage in API endpoints
@videos_bp.route('/<int:video_id>/download', methods=['POST'])
def download_video(video_id):
    # Submit download task to background queue
    future = task_queue.submit_task(download_video_task, video_id)
    
    return jsonify({
        'message': 'Download queued',
        'task_id': id(future)
    })
```

### Disk I/O Optimization

#### Efficient File Operations
```python
import shutil
from pathlib import Path

class FileManager:
    def __init__(self, temp_dir, final_dir):
        self.temp_dir = Path(temp_dir)
        self.final_dir = Path(final_dir)
        
        # Ensure directories exist
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.final_dir.mkdir(parents=True, exist_ok=True)
    
    def atomic_move(self, temp_file, final_file):
        """Atomically move file from temp to final location."""
        temp_path = self.temp_dir / temp_file
        final_path = self.final_dir / final_file
        
        # Ensure destination directory exists
        final_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Atomic move
        shutil.move(str(temp_path), str(final_path))
        
        return final_path
    
    def batch_file_operations(self, operations):
        """Perform multiple file operations efficiently."""
        for operation in operations:
            if operation['type'] == 'move':
                self.atomic_move(operation['source'], operation['dest'])
            elif operation['type'] == 'delete':
                Path(operation['path']).unlink(missing_ok=True)
```

## 📊 Performance Monitoring

### Built-in Performance Monitoring

#### API Performance Tracking
```python
from src.utils.performance_monitor import monitor_performance

@monitor_performance("api.videos.search")
def search_videos():
    """Search videos with performance monitoring."""
    # Implementation here
    pass

# Check performance statistics
def get_performance_stats():
    """Get comprehensive performance statistics."""
    from src.utils.performance_monitor import perf_stats
    
    stats = {}
    for endpoint, data in perf_stats.stats.items():
        stats[endpoint] = {
            'avg_response_time': data.avg_time,
            'min_response_time': data.min_time,
            'max_response_time': data.max_time,
            'request_count': data.count,
            'slow_requests': len([t for t in data.times if t > 1.0])
        }
    
    return stats
```

#### System Resource Monitoring
```python
class SystemMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.process = psutil.Process()
    
    def get_system_stats(self):
        """Get comprehensive system statistics."""
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory usage
        memory = psutil.virtual_memory()
        process_memory = self.process.memory_info()
        
        # Disk usage
        disk_usage = psutil.disk_usage('/')
        
        # Network I/O
        network = psutil.net_io_counters()
        
        return {
            'uptime': time.time() - self.start_time,
            'cpu': {
                'percent': cpu_percent,
                'count': cpu_count,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent,
                'process_rss': process_memory.rss,
                'process_vms': process_memory.vms
            },
            'disk': {
                'total': disk_usage.total,
                'used': disk_usage.used,
                'free': disk_usage.free,
                'percent': (disk_usage.used / disk_usage.total) * 100
            },
            'network': {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }
        }
```

### Performance Alerting
```python
class PerformanceAlerter:
    def __init__(self):
        self.thresholds = {
            'cpu_percent': 80,
            'memory_percent': 85,
            'disk_percent': 90,
            'response_time': 2.0
        }
        self.alert_history = {}
    
    def check_alerts(self, stats):
        """Check for performance issues and send alerts."""
        alerts = []
        
        # CPU usage alert
        if stats['cpu']['percent'] > self.thresholds['cpu_percent']:
            alerts.append({
                'type': 'high_cpu',
                'value': stats['cpu']['percent'],
                'threshold': self.thresholds['cpu_percent']
            })
        
        # Memory usage alert
        if stats['memory']['percent'] > self.thresholds['memory_percent']:
            alerts.append({
                'type': 'high_memory',
                'value': stats['memory']['percent'],
                'threshold': self.thresholds['memory_percent']
            })
        
        # Disk usage alert
        if stats['disk']['percent'] > self.thresholds['disk_percent']:
            alerts.append({
                'type': 'high_disk',
                'value': stats['disk']['percent'],
                'threshold': self.thresholds['disk_percent']
            })
        
        # Send alerts if any are triggered
        for alert in alerts:
            self.send_alert(alert)
    
    def send_alert(self, alert):
        """Send performance alert notification."""
        logger.warning(f"Performance alert: {alert['type']} - "
                      f"{alert['value']}% exceeds threshold of {alert['threshold']}%")
        
        # Implement email/webhook notifications here
```

## 🔍 Performance Testing

### Load Testing
```python
import requests
import concurrent.futures
import time

def load_test_endpoint(url, concurrent_requests=10, total_requests=100):
    """Load test an API endpoint."""
    results = []
    
    def make_request():
        start_time = time.time()
        try:
            response = requests.get(url)
            end_time = time.time()
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'success': response.status_code == 200
            }
        except Exception as e:
            return {
                'status_code': None,
                'response_time': None,
                'success': False,
                'error': str(e)
            }
    
    # Execute concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_requests) as executor:
        futures = [executor.submit(make_request) for _ in range(total_requests)]
        results = [future.result() for future in futures]
    
    # Analyze results
    successful_requests = [r for r in results if r['success']]
    response_times = [r['response_time'] for r in successful_requests]
    
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
        success_rate = len(successful_requests) / len(results) * 100
        
        print(f"Load Test Results:")
        print(f"Total Requests: {total_requests}")
        print(f"Successful Requests: {len(successful_requests)}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Average Response Time: {avg_response_time:.3f}s")
        print(f"Min Response Time: {min_response_time:.3f}s")
        print(f"Max Response Time: {max_response_time:.3f}s")
    
    return results
```

## 📈 Performance Optimization Checklist

### Database Optimization
- [ ] Connection pool properly configured
- [ ] Appropriate indexes created
- [ ] Queries optimized (no N+1 problems)
- [ ] Regular maintenance scheduled
- [ ] Database statistics up to date

### Frontend Optimization
- [ ] Virtualization implemented for large lists
- [ ] API requests debounced/cached
- [ ] Images optimized and responsive
- [ ] CSS and JavaScript minified
- [ ] Efficient DOM manipulation

### API Optimization
- [ ] Response caching implemented
- [ ] Pagination properly implemented
- [ ] Background tasks for heavy operations
- [ ] Appropriate rate limiting
- [ ] Performance monitoring active

### System Optimization
- [ ] Memory usage monitored
- [ ] CPU usage reasonable
- [ ] Disk I/O optimized
- [ ] Background task queue configured
- [ ] Resource limits set appropriately

### Monitoring
- [ ] Performance metrics collected
- [ ] Alerts configured for thresholds
- [ ] Regular performance reviews scheduled
- [ ] Load testing performed
- [ ] Performance regression tests in place

## 🔗 Related Documentation

- **System Monitoring**: `MONITORING.md`
- **Architecture Guide**: `ARCHITECTURE.md` 
- **Configuration Guide**: `CONFIGURATION_GUIDE.md`
- **Troubleshooting**: `TROUBLESHOOTING.md`

This performance optimization guide ensures MVidarr operates efficiently at scale while maintaining responsive user experience and optimal resource utilization.