/**
 * Frontend Performance Monitor
 * Tracks Core Web Vitals and other performance metrics
 */

class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.observers = [];
        this.init();
    }
    
    init() {
        // Wait for page to load before starting measurements
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.startMonitoring());
        } else {
            this.startMonitoring();
        }
    }
    
    startMonitoring() {
        this.measureCoreWebVitals();
        this.measureCustomMetrics();
        this.setupPerformanceObserver();
        this.measureResourceTiming();
        
        // Send metrics after page is fully loaded
        window.addEventListener('load', () => {
            setTimeout(() => this.sendMetrics(), 2000);
        });
    }
    
    measureCoreWebVitals() {
        // Largest Contentful Paint (LCP)
        this.measureLCP();
        
        // First Input Delay (FID)
        this.measureFID();
        
        // Cumulative Layout Shift (CLS)
        this.measureCLS();
        
        // First Contentful Paint (FCP)
        this.measureFCP();
    }
    
    measureLCP() {
        if (!('PerformanceObserver' in window)) return;
        
        try {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.metrics.lcp = Math.round(lastEntry.startTime);
            });
            
            observer.observe({ type: 'largest-contentful-paint', buffered: true });
            this.observers.push(observer);
        } catch (error) {
            console.warn('LCP measurement failed:', error);
        }
    }
    
    measureFID() {
        if (!('PerformanceObserver' in window)) return;
        
        try {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (entry.name === 'first-input') {
                        this.metrics.fid = Math.round(entry.processingStart - entry.startTime);
                    }
                });
            });
            
            observer.observe({ type: 'first-input', buffered: true });
            this.observers.push(observer);
        } catch (error) {
            console.warn('FID measurement failed:', error);
        }
    }
    
    measureCLS() {
        if (!('PerformanceObserver' in window)) return;
        
        try {
            let clsValue = 0;
            let sessionValue = 0;
            let sessionEntries = [];
            
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                
                entries.forEach(entry => {
                    if (!entry.hadRecentInput) {
                        const firstSessionEntry = sessionEntries[0];
                        const lastSessionEntry = sessionEntries[sessionEntries.length - 1];
                        
                        if (sessionValue &&
                            entry.startTime - lastSessionEntry.startTime < 1000 &&
                            entry.startTime - firstSessionEntry.startTime < 5000) {
                            sessionValue += entry.value;
                            sessionEntries.push(entry);
                        } else {
                            sessionValue = entry.value;
                            sessionEntries = [entry];
                        }
                        
                        if (sessionValue > clsValue) {
                            clsValue = sessionValue;
                        }
                    }
                });
                
                this.metrics.cls = Math.round(clsValue * 10000) / 10000;
            });
            
            observer.observe({ type: 'layout-shift', buffered: true });
            this.observers.push(observer);
        } catch (error) {
            console.warn('CLS measurement failed:', error);
        }
    }
    
    measureFCP() {
        if (!('PerformanceObserver' in window)) return;
        
        try {
            const observer = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (entry.name === 'first-contentful-paint') {
                        this.metrics.fcp = Math.round(entry.startTime);
                    }
                });
            });
            
            observer.observe({ type: 'paint', buffered: true });
            this.observers.push(observer);
        } catch (error) {
            console.warn('FCP measurement failed:', error);
        }
    }
    
    measureCustomMetrics() {
        // Time to Interactive approximation
        this.measureTTI();
        
        // Page load times
        this.measureLoadTimes();
        
        // JavaScript bundle size
        this.measureBundleSize();
        
        // Memory usage (if available)
        this.measureMemoryUsage();
    }
    
    measureTTI() {
        window.addEventListener('load', () => {
            // Simple TTI approximation - when long tasks stop
            let lastLongTaskTime = 0;
            
            if ('PerformanceObserver' in window) {
                try {
                    const observer = new PerformanceObserver((list) => {
                        const entries = list.getEntries();
                        entries.forEach(entry => {
                            if (entry.duration >= 50) {
                                lastLongTaskTime = entry.startTime + entry.duration;
                            }
                        });
                    });
                    
                    observer.observe({ type: 'longtask', buffered: true });
                    this.observers.push(observer);
                    
                    // Estimate TTI after 5 seconds of no long tasks
                    setTimeout(() => {
                        const now = performance.now();
                        this.metrics.tti = Math.round(lastLongTaskTime || now);
                    }, 5000);
                } catch (error) {
                    console.warn('TTI measurement failed:', error);
                }
            }
        });
    }
    
    measureLoadTimes() {
        window.addEventListener('load', () => {
            const navigation = performance.getEntriesByType('navigation')[0];
            if (navigation) {
                this.metrics.domContentLoaded = Math.round(navigation.domContentLoadedEventEnd - navigation.navigationStart);
                this.metrics.loadComplete = Math.round(navigation.loadEventEnd - navigation.navigationStart);
                this.metrics.dnsLookup = Math.round(navigation.domainLookupEnd - navigation.domainLookupStart);
                this.metrics.tcpConnect = Math.round(navigation.connectEnd - navigation.connectStart);
                this.metrics.serverResponse = Math.round(navigation.responseEnd - navigation.requestStart);
            }
        });
    }
    
    measureBundleSize() {
        const resources = performance.getEntriesByType('resource');
        let totalJSSize = 0;
        let totalCSSSize = 0;
        
        resources.forEach(resource => {
            if (resource.name.endsWith('.js')) {
                totalJSSize += resource.transferSize || 0;
            } else if (resource.name.endsWith('.css')) {
                totalCSSSize += resource.transferSize || 0;
            }
        });
        
        this.metrics.jsBundleSize = totalJSSize;
        this.metrics.cssBundleSize = totalCSSSize;
    }
    
    measureMemoryUsage() {
        if ('memory' in performance) {
            this.metrics.memoryUsage = {
                used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024 * 100) / 100,
                total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024 * 100) / 100,
                limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024 * 100) / 100
            };
        }
    }
    
    measureResourceTiming() {
        window.addEventListener('load', () => {
            const resources = performance.getEntriesByType('resource');
            const slowResources = resources
                .filter(resource => resource.duration > 1000)
                .map(resource => ({
                    name: resource.name,
                    duration: Math.round(resource.duration),
                    size: resource.transferSize
                }));
            
            if (slowResources.length > 0) {
                this.metrics.slowResources = slowResources;
            }
        });
    }
    
    setupPerformanceObserver() {
        if (!('PerformanceObserver' in window)) return;
        
        // Monitor long tasks
        try {
            const longTaskObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const longTasks = entries.filter(entry => entry.duration >= 50);
                
                if (longTasks.length > 0) {
                    this.metrics.longTaskCount = (this.metrics.longTaskCount || 0) + longTasks.length;
                    this.metrics.totalBlockingTime = (this.metrics.totalBlockingTime || 0) + 
                        longTasks.reduce((sum, task) => sum + Math.max(0, task.duration - 50), 0);
                }
            });
            
            longTaskObserver.observe({ type: 'longtask' });
            this.observers.push(longTaskObserver);
        } catch (error) {
            console.warn('Long task observer failed:', error);
        }
    }
    
    async sendMetrics() {
        const pageInfo = {
            url: window.location.href,
            userAgent: navigator.userAgent,
            timestamp: Date.now(),
            viewport: {
                width: window.innerWidth,
                height: window.innerHeight
            },
            connection: this.getConnectionInfo()
        };
        
        const allMetrics = {
            ...this.metrics,
            ...pageInfo
        };
        
        // Send to API endpoint
        try {
            await fetch('/api/performance/frontend-metrics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(allMetrics)
            });
            
            console.log('Performance metrics sent:', allMetrics);
        } catch (error) {
            console.warn('Failed to send performance metrics:', error);
            
            // Store in IndexedDB or localStorage for later sync
            this.storeMetricsLocally(allMetrics);
        }
    }
    
    getConnectionInfo() {
        if ('connection' in navigator) {
            const conn = navigator.connection;
            return {
                effectiveType: conn.effectiveType,
                downlink: conn.downlink,
                rtt: conn.rtt,
                saveData: conn.saveData
            };
        }
        return null;
    }
    
    storeMetricsLocally(metrics) {
        try {
            const stored = localStorage.getItem('pendingMetrics') || '[]';
            const pendingMetrics = JSON.parse(stored);
            pendingMetrics.push(metrics);
            
            // Keep only last 10 entries
            if (pendingMetrics.length > 10) {
                pendingMetrics.shift();
            }
            
            localStorage.setItem('pendingMetrics', JSON.stringify(pendingMetrics));
        } catch (error) {
            console.warn('Failed to store metrics locally:', error);
        }
    }
    
    // Public methods
    getMetrics() {
        return { ...this.metrics };
    }
    
    getRecommendations() {
        const recommendations = [];
        
        if (this.metrics.lcp > 2500) {
            recommendations.push('LCP is slow. Consider optimizing images and reducing server response times.');
        }
        
        if (this.metrics.fid > 100) {
            recommendations.push('FID is high. Consider reducing JavaScript execution time.');
        }
        
        if (this.metrics.cls > 0.1) {
            recommendations.push('CLS is high. Add size attributes to images and avoid inserting content above existing content.');
        }
        
        if (this.metrics.loadComplete > 3000) {
            recommendations.push('Page load time is slow. Consider code splitting and lazy loading.');
        }
        
        if (this.metrics.jsBundleSize > 500000) {
            recommendations.push('JavaScript bundle is large. Consider code splitting and tree shaking.');
        }
        
        return recommendations;
    }
    
    cleanup() {
        this.observers.forEach(observer => {
            try {
                observer.disconnect();
            } catch (error) {
                console.warn('Error disconnecting observer:', error);
            }
        });
    }
}

// Initialize performance monitoring
const performanceMonitor = new PerformanceMonitor();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    performanceMonitor.cleanup();
});

// Export for global access
window.performanceMonitor = performanceMonitor;