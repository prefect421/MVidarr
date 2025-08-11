/**
 * Service Worker for MVidarr
 * Provides caching for better performance and offline functionality
 */

const CACHE_NAME = 'mvidarr-v1.0.0';
const STATIC_CACHE_NAME = 'mvidarr-static-v1.0.0';
const API_CACHE_NAME = 'mvidarr-api-v1.0.0';

// Resources to cache immediately
const STATIC_RESOURCES = [
    '/',
    '/static/js/core.js',
    '/static/js/universal-search.js',
    '/static/js/header.js',
    '/static/js/toast.js',
    '/static/main.js',
    '/css/main.css',
    '/css/themes.css',
    '/static/MVidarr.png',
    '/static/favicon.ico',
    'https://code.iconify.design/iconify-icon/3.0.0/iconify-icon.min.js'
];

// API endpoints to cache (with short TTL)
const API_CACHE_PATTERNS = [
    '/api/health/version',
    '/api/themes/current',
    '/auth/check'
];

// Install event - cache static resources
self.addEventListener('install', event => {
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE_NAME)
                .then(cache => cache.addAll(STATIC_RESOURCES)),
            caches.open(API_CACHE_NAME)
        ])
        .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName.startsWith('mvidarr-') && 
                        cacheName !== CACHE_NAME && 
                        cacheName !== STATIC_CACHE_NAME && 
                        cacheName !== API_CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Handle different types of requests
    if (isStaticResource(url.pathname)) {
        event.respondWith(handleStaticResource(request));
    } else if (isAPIRequest(url.pathname)) {
        event.respondWith(handleAPIRequest(request));
    } else if (isPageRequest(request)) {
        event.respondWith(handlePageRequest(request));
    } else {
        event.respondWith(handleOtherRequest(request));
    }
});

// Check if it's a static resource
function isStaticResource(pathname) {
    return pathname.startsWith('/static/') || 
           pathname.startsWith('/css/') ||
           pathname.endsWith('.js') ||
           pathname.endsWith('.css') ||
           pathname.endsWith('.png') ||
           pathname.endsWith('.jpg') ||
           pathname.endsWith('.ico') ||
           pathname.includes('iconify');
}

// Check if it's an API request
function isAPIRequest(pathname) {
    return pathname.startsWith('/api/') || 
           pathname.startsWith('/auth/') ||
           API_CACHE_PATTERNS.some(pattern => pathname.includes(pattern));
}

// Check if it's a page request
function isPageRequest(request) {
    return request.headers.get('accept').includes('text/html');
}

// Handle static resources (cache first)
async function handleStaticResource(request) {
    try {
        const cache = await caches.open(STATIC_CACHE_NAME);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Error handling static resource:', error);
        return new Response('Resource unavailable', { status: 503 });
    }
}

// Handle API requests (network first, cache as fallback)
async function handleAPIRequest(request) {
    try {
        // Try network first
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful responses for 5 minutes
            const cache = await caches.open(API_CACHE_NAME);
            const responseWithTimestamp = new Response(networkResponse.body, {
                status: networkResponse.status,
                statusText: networkResponse.statusText,
                headers: {
                    ...Object.fromEntries(networkResponse.headers),
                    'sw-cached': Date.now().toString()
                }
            });
            
            cache.put(request, responseWithTimestamp.clone());
            return networkResponse;
        }
        
        throw new Error('Network response not ok');
    } catch (error) {
        // Fall back to cache
        const cache = await caches.open(API_CACHE_NAME);
        const cachedResponse = await cache.match(request);
        
        if (cachedResponse) {
            const cacheTime = parseInt(cachedResponse.headers.get('sw-cached') || '0');
            const now = Date.now();
            const fiveMinutes = 5 * 60 * 1000;
            
            // Return cached response if less than 5 minutes old
            if (now - cacheTime < fiveMinutes) {
                return cachedResponse;
            }
        }
        
        return new Response('Service unavailable', { status: 503 });
    }
}

// Handle page requests (network first, cache as fallback)
async function handlePageRequest(request) {
    try {
        const networkResponse = await fetch(request);
        return networkResponse;
    } catch (error) {
        // Return a basic offline page
        return new Response(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>MVidarr - Offline</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        text-align: center;
                        padding: 2rem;
                        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                        color: white;
                        min-height: 100vh;
                        margin: 0;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                    }
                    h1 { margin-bottom: 1rem; }
                    p { margin-bottom: 2rem; opacity: 0.8; }
                    button {
                        background: #3b82f6;
                        color: white;
                        border: none;
                        padding: 0.75rem 1.5rem;
                        border-radius: 0.5rem;
                        cursor: pointer;
                        font-size: 1rem;
                    }
                </style>
            </head>
            <body>
                <h1>MVidarr is Offline</h1>
                <p>You're currently offline. Please check your connection and try again.</p>
                <button onclick="location.reload()">Retry</button>
            </body>
            </html>
        `, {
            headers: { 'Content-Type': 'text/html' }
        });
    }
}

// Handle other requests (pass through)
async function handleOtherRequest(request) {
    try {
        return await fetch(request);
    } catch (error) {
        return new Response('Request failed', { status: 503 });
    }
}

// Background sync for analytics data
self.addEventListener('sync', event => {
    if (event.tag === 'performance-metrics') {
        event.waitUntil(syncPerformanceMetrics());
    }
});

async function syncPerformanceMetrics() {
    // Sync any cached performance metrics when back online
    try {
        const cache = await caches.open('performance-metrics');
        const requests = await cache.keys();
        
        for (const request of requests) {
            const response = await cache.match(request);
            const data = await response.json();
            
            // Send to analytics endpoint
            await fetch('/api/performance/metrics', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            // Remove from cache after successful sync
            await cache.delete(request);
        }
    } catch (error) {
        console.error('Error syncing performance metrics:', error);
    }
}

// Message handling for cache management
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    } else if (event.data && event.data.type === 'CLEAR_CACHE') {
        clearAllCaches();
    }
});

async function clearAllCaches() {
    const cacheNames = await caches.keys();
    await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
    );
}