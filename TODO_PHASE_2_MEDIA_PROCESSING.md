# TODO: Phase 2 - Media Processing Optimization (Weeks 15-26)
## Complete FastAPI Migration - Phase 2 Task List

**Timeline**: 10-12 weeks (Q2-Q3 2026)  
**Focus**: Eliminate longest blocking operations (yt-dlp, FFmpeg, image processing)  
**Goal**: Zero blocking operations in media processing, background job system operational

---

## 📅 **WEEK 15-18: BACKGROUND JOB QUEUE IMPLEMENTATION**
**Priority**: CRITICAL - Eliminates 30-300 second blocking operations  
**Target**: yt-dlp downloads, bulk operations, long-running tasks

### **Week 15: Celery + Redis Infrastructure**
- [ ] **Install and configure Redis**
  - [ ] Add Redis container to docker-compose.yml
  - [ ] Configure Redis for job queue persistence
  - [ ] Set up Redis connection pooling and memory limits
  - [ ] Test Redis connectivity and performance

- [ ] **Install and configure Celery**
  - [ ] Add `celery[redis]>=5.3.4` to requirements-fastapi.txt
  - [ ] Create `src/background/celery_app.py` with Redis broker
  - [ ] Configure Celery worker settings (concurrency, prefetch)
  - [ ] Set up Celery result backend for job tracking

- [ ] **Docker infrastructure updates**
  - [ ] Add celery-worker service to docker-compose.yml
  - [ ] Add celery-beat service for scheduled tasks
  - [ ] Configure health checks for Celery services
  - [ ] Test complete Docker stack startup

### **Week 16: yt-dlp Background Tasks**
- [ ] **Convert yt-dlp downloads to Celery tasks**
  - [ ] Create `src/background/tasks/video_download.py`
  - [ ] Move `YtDlpService.download_video()` to Celery task
  - [ ] Implement progress tracking via job status updates
  - [ ] Add error handling and retry logic for failed downloads

- [ ] **Update video download API endpoints**
  - [ ] Modify `/api/videos/download` to queue job instead of blocking
  - [ ] Return job ID immediately for client tracking
  - [ ] Create `/api/jobs/{job_id}/progress` for progress monitoring
  - [ ] Test non-blocking video download initiation

- [ ] **Job progress integration**
  - [ ] Implement job progress updates in Celery tasks
  - [ ] Create database job status tracking
  - [ ] Integrate with existing job dashboard UI
  - [ ] Test real-time progress updates

### **Week 17: Bulk Operations Background Tasks**
- [ ] **Convert bulk metadata enrichment**
  - [ ] Create `src/background/tasks/metadata_enrichment.py`
  - [ ] Move bulk artist enrichment to Celery tasks
  - [ ] Implement batch processing with progress tracking
  - [ ] Add proper error handling for API failures

- [ ] **Convert bulk video operations**
  - [ ] Create background tasks for bulk video deletion
  - [ ] Implement bulk video quality analysis
  - [ ] Create bulk playlist sync operations
  - [ ] Test batch operation performance and error handling

### **Week 18: Job Monitoring and Management**
- [ ] **Celery monitoring setup**
  - [ ] Install and configure Flower for job monitoring
  - [ ] Create job management dashboard integration
  - [ ] Implement job cancellation capabilities
  - [ ] Add job retry and failure recovery

- [ ] **Performance optimization**
  - [ ] Tune Celery worker concurrency settings
  - [ ] Optimize Redis memory usage for job storage
  - [ ] Implement job queue prioritization
  - [ ] Load test background job system

**Week 15-18 Completion Criteria:**
- ✅ All yt-dlp downloads execute in background (non-blocking)
- ✅ Bulk operations process via job queue
- ✅ Job progress tracking operational via WebSocket
- ✅ Zero timeout errors for video download requests

---

## 📅 **WEEK 19-21: FFMPEG STREAMING OPTIMIZATION**
**Priority**: HIGH - Continuous blocking operations for video streaming

### **Week 19: Async Subprocess for FFmpeg**
- [ ] **Convert FFmpeg streaming to async subprocess**
  - [ ] Update `src/services/ffmpeg_streaming_service.py`
  - [ ] Replace `subprocess.Popen` with `asyncio.create_subprocess_exec`
  - [ ] Implement async generator for video streaming
  - [ ] Add proper resource cleanup and process management

- [ ] **Streaming response optimization**
  - [ ] Create async streaming response for FastAPI
  - [ ] Implement proper chunk handling for video streams
  - [ ] Add stream error handling and recovery
  - [ ] Test streaming performance and resource usage

### **Week 20: Concurrent Stream Management**
- [ ] **Multiple concurrent streams support**
  - [ ] Implement stream session management
  - [ ] Add resource limits for concurrent streams
  - [ ] Create stream cleanup on client disconnect
  - [ ] Test multiple concurrent video streams

- [ ] **Stream quality and format handling**
  - [ ] Implement dynamic quality selection
  - [ ] Add format conversion on-the-fly
  - [ ] Create stream caching for popular content
  - [ ] Optimize stream startup time

### **Week 21: VLC and Alternative Streaming**
- [ ] **Update VLC streaming service**
  - [ ] Convert `src/services/vlc_streaming_service.py` to async
  - [ ] Implement VLC process management with async
  - [ ] Add VLC streaming error handling
  - [ ] Test VLC vs FFmpeg streaming performance

- [ ] **Streaming infrastructure optimization**
  - [ ] Implement stream load balancing
  - [ ] Add stream health monitoring
  - [ ] Create stream analytics and logging
  - [ ] Performance benchmarking of streaming solutions

**Week 19-21 Completion Criteria:**
- ✅ All video streaming uses async subprocess (non-blocking)
- ✅ Support for concurrent video streams verified
- ✅ Stream resource management operational
- ✅ Streaming performance improved vs synchronous version

---

## 📅 **WEEK 22-24: IMAGE PROCESSING THREAD POOLS**
**Priority**: MEDIUM - 1-5 second blocking operations for thumbnails/images

### **Week 22: PIL/OpenCV Thread Pool Implementation**
- [ ] **Create image processing service wrapper**
  - [ ] Create `src/services/async_image_processing.py`
  - [ ] Implement ThreadPoolExecutor for PIL operations
  - [ ] Add ProcessPoolExecutor for CPU-intensive operations
  - [ ] Create unified async interface for image operations

- [ ] **Thumbnail generation optimization**
  - [ ] Update thumbnail generation to use thread pools
  - [ ] Implement batch thumbnail processing
  - [ ] Add thumbnail caching and optimization
  - [ ] Test concurrent thumbnail generation performance

### **Week 23: Video Analysis Processing**
- [ ] **Video quality analysis optimization**
  - [ ] Convert video quality analysis to thread pools
  - [ ] Implement FFprobe operations in background
  - [ ] Add video metadata extraction to thread pools
  - [ ] Create video analysis result caching

- [ ] **Image manipulation operations**
  - [ ] Convert artist image processing to async
  - [ ] Implement image resizing and optimization
  - [ ] Add image format conversion operations
  - [ ] Test image processing under concurrent load

### **Week 24: Batch Processing and Optimization**
- [ ] **Batch image processing implementation**
  - [ ] Create ProcessPoolExecutor for batch operations
  - [ ] Implement bulk thumbnail regeneration
  - [ ] Add batch image optimization tasks
  - [ ] Create progress tracking for batch operations

- [ ] **Performance optimization and monitoring**
  - [ ] Optimize thread pool sizing for system resources
  - [ ] Add image processing performance monitoring
  - [ ] Implement image processing error handling
  - [ ] Load test image processing under various scenarios

**Week 22-24 Completion Criteria:**
- ✅ All image processing uses thread/process pools (non-blocking)
- ✅ Batch image operations process efficiently
- ✅ Image processing performance optimized for available CPU
- ✅ Proper error handling and monitoring in place

---

## 📅 **WEEK 25-26: WEBSOCKET SYSTEM MIGRATION**
**Priority**: CRITICAL - Real-time job progress and system updates

### **Week 25: FastAPI WebSocket Implementation**
- [ ] **Create FastAPI WebSocket infrastructure**
  - [ ] Create `src/api/fastapi/websockets.py`
  - [ ] Implement WebSocket connection management
  - [ ] Create WebSocket authentication and authorization
  - [ ] Add WebSocket error handling and reconnection

- [ ] **Job progress WebSocket integration**
  - [ ] Connect Celery job progress to WebSocket broadcasts
  - [ ] Implement real-time job status updates
  - [ ] Create job completion notifications
  - [ ] Test WebSocket performance under load

### **Week 26: Client-Side WebSocket Migration**
- [ ] **Update JavaScript WebSocket clients**
  - [ ] Modify `frontend/static/js/background-jobs.js`
  - [ ] Update WebSocket connection logic for FastAPI
  - [ ] Implement WebSocket reconnection handling
  - [ ] Update job progress display components

- [ ] **WebSocket system testing**
  - [ ] Test real-time job progress updates
  - [ ] Verify WebSocket connection stability
  - [ ] Load test WebSocket with multiple concurrent connections
  - [ ] Integration testing with background job system

- [ ] **Migration completion and cleanup**
  - [ ] Remove Flask-SocketIO dependencies
  - [ ] Clean up old WebSocket implementation
  - [ ] Update documentation for new WebSocket system
  - [ ] Performance comparison: Flask-SocketIO vs FastAPI WebSockets

**Week 25-26 Completion Criteria:**
- ✅ FastAPI WebSocket system fully operational
- ✅ Real-time job progress updates working
- ✅ WebSocket performance equal or better than Flask-SocketIO
- ✅ Client-side WebSocket integration complete

---

## 🎯 **PHASE 2 SUCCESS METRICS**

### **Blocking Operations Elimination**
- ✅ **Video Downloads**: 100% background processed (0 blocking downloads)
- ✅ **Video Streaming**: 100% async subprocess (0 blocking streams)
- ✅ **Image Processing**: 100% thread/process pools (0 blocking operations)
- ✅ **Overall**: Longest blocking operations eliminated

### **Performance Improvements**
- ✅ **Download Responsiveness**: Immediate response (background processing)
- ✅ **Streaming Concurrent Capacity**: 10x concurrent streams capability
- ✅ **Image Processing Throughput**: 5x improvement with thread pools
- ✅ **System Responsiveness**: Zero timeout errors under media processing load

### **Infrastructure Reliability**
- ✅ **Background Job System**: 99%+ reliability with retry logic
- ✅ **WebSocket Connectivity**: Stable real-time updates
- ✅ **Resource Management**: Proper cleanup and resource limits
- ✅ **Error Handling**: Comprehensive error recovery

### **User Experience**
- ✅ **Real-time Progress**: Job progress updates via WebSocket
- ✅ **Non-blocking Interface**: UI responsive during media operations
- ✅ **Concurrent Operations**: Multiple media operations simultaneous
- ✅ **Error Feedback**: Clear error messages and recovery options

---

## 🚨 **CRITICAL DEPENDENCIES & INFRASTRUCTURE**

### **Infrastructure Requirements**
- **Redis**: Must be operational and properly configured
- **Celery Workers**: Must scale with available CPU cores
- **Docker Resources**: Memory limits adjusted for worker processes
- **WebSocket Connections**: Connection limits configured appropriately

### **Performance Monitoring**
- **Job Queue Health**: Monitor Redis memory usage and job processing rates
- **Worker Performance**: Track worker CPU usage and job completion times
- **WebSocket Connections**: Monitor concurrent connection counts
- **Stream Resource Usage**: Monitor FFmpeg process resource consumption

### **Migration Dependencies**
- **Phase 1 Complete**: Async foundation must be operational
- **Database Async**: All database operations must be async
- **HTTP Clients**: All external API calls must be async
- **Testing Infrastructure**: Comprehensive testing of background operations

**Phase 2 represents the most critical performance improvements, eliminating the longest blocking operations and establishing the infrastructure for true async scalability.**