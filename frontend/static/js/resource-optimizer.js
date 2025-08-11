/**
 * Resource Optimizer - Handles efficient loading of assets
 * Improves Core Web Vitals and reduces loading times
 */

class ResourceOptimizer {
    constructor() {
        this.loadedResources = new Set();
        this.observer = null;
        this.init();
    }
    
    init() {
        this.setupIntersectionObserver();
        this.optimizeImages();
        this.preloadCriticalResources();
        this.setupServiceWorker();
    }
    
    // Lazy load images and videos
    setupIntersectionObserver() {
        if (!('IntersectionObserver' in window)) {
            // Fallback for older browsers
            this.loadAllImages();
            return;
        }
        
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.loadResource(entry.target);
                    this.observer.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '50px 0px', // Load 50px before entering viewport
            threshold: 0.1
        });
        
        // Observe all lazy-loadable elements
        this.observeLazyElements();
    }
    
    observeLazyElements() {
        const lazyImages = document.querySelectorAll('img[data-src], video[data-src]');
        lazyImages.forEach(img => this.observer.observe(img));
    }
    
    loadResource(element) {
        if (element.dataset.src) {
            element.src = element.dataset.src;
            element.removeAttribute('data-src');
            
            // Add loaded class for CSS transitions
            element.addEventListener('load', () => {
                element.classList.add('loaded');
            });
            
            // Handle errors gracefully
            element.addEventListener('error', () => {
                element.classList.add('error');
                // Set fallback image if available
                if (element.dataset.fallback) {
                    element.src = element.dataset.fallback;
                }
            });
        }
    }
    
    loadAllImages() {
        const lazyImages = document.querySelectorAll('img[data-src], video[data-src]');
        lazyImages.forEach(img => this.loadResource(img));
    }
    
    // Optimize existing images
    optimizeImages() {
        const images = document.querySelectorAll('img');
        images.forEach(img => {
            // Add loading="lazy" for native lazy loading support
            if (!img.loading) {
                img.loading = 'lazy';
            }
            
            // Decode images asynchronously
            if ('decode' in img) {
                img.decode().catch(() => {
                    // Handle decode errors silently
                });
            }
        });
    }
    
    // Preload critical resources
    preloadCriticalResources() {
        const criticalResources = [
            '/static/js/core.js',
            '/static/js/universal-search.js',
            '/css/themes.css'
        ];
        
        criticalResources.forEach(resource => {
            if (!this.loadedResources.has(resource)) {
                this.preloadResource(resource);
                this.loadedResources.add(resource);
            }
        });
    }
    
    preloadResource(href, as = 'script') {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.href = href;
        link.as = as;
        
        // Add to head
        document.head.appendChild(link);
    }
    
    // Dynamic import for non-critical modules
    async loadModule(modulePath) {
        try {
            const module = await import(modulePath);
            return module;
        } catch (error) {
            console.error(`Failed to load module: ${modulePath}`, error);
            return null;
        }
    }
    
    // Setup service worker for caching
    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/static/sw.js')
                    .then(registration => {
                        console.log('SW registered: ', registration);
                    })
                    .catch(registrationError => {
                        console.log('SW registration failed: ', registrationError);
                    });
            });
        }
    }
    
    // Measure performance
    measurePerformance() {
        if ('performance' in window) {
            window.addEventListener('load', () => {
                setTimeout(() => {
                    const perfData = performance.getEntriesByType('navigation')[0];
                    
                    const metrics = {
                        'DNS Lookup': perfData.domainLookupEnd - perfData.domainLookupStart,
                        'TCP Connection': perfData.connectEnd - perfData.connectStart,
                        'Request': perfData.responseStart - perfData.requestStart,
                        'Response': perfData.responseEnd - perfData.responseStart,
                        'DOM Processing': perfData.domComplete - perfData.domLoading,
                        'Total Load Time': perfData.loadEventEnd - perfData.navigationStart
                    };
                    
                    // Send metrics to analytics if available
                    if (typeof sendPerformanceMetrics === 'function') {
                        sendPerformanceMetrics(metrics);
                    }
                    
                    console.log('Performance Metrics:', metrics);
                }, 1000);
            });
        }
    }
    
    // Resource hints
    addResourceHints() {
        const hints = [
            { rel: 'dns-prefetch', href: '//code.iconify.design' },
            { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
            { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: true }
        ];
        
        hints.forEach(hint => {
            const link = document.createElement('link');
            Object.assign(link, hint);
            document.head.appendChild(link);
        });
    }
    
    // Cleanup on page unload
    cleanup() {
        if (this.observer) {
            this.observer.disconnect();
        }
    }
}

// Initialize resource optimizer
const resourceOptimizer = new ResourceOptimizer();

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    resourceOptimizer.cleanup();
});

// Export for use in other modules
window.resourceOptimizer = resourceOptimizer;