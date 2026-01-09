#!/usr/bin/env python3
"""
Advanced Web Scraper with Anti-Detection
- Real browser fingerprint (Playwright with stealth)
- Cookies and storage enabled
- Real User-Agent rotation
- Anti-bot detection bypass
- Intelligent content extraction
"""

import os
import sys
import json
import time
import random
import asyncio
from urllib.parse import urljoin, urlparse
from datetime import datetime

# Try to use Playwright for real browser, fallback to requests
try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    import requests
    from bs4 import BeautifulSoup

# Real User-Agents from actual browsers
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
]

# Stealth JavaScript to inject
STEALTH_JS = """
// Override webdriver detection
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

// Override plugins
Object.defineProperty(navigator, 'plugins', {
    get: () => [
        { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
        { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
        { name: 'Native Client', filename: 'internal-nacl-plugin' }
    ]
});

// Override languages
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en', 'pt-BR'] });

// Override platform
Object.defineProperty(navigator, 'platform', { get: () => 'Win32' });

// Override hardwareConcurrency
Object.defineProperty(navigator, 'hardwareConcurrency', { get: () => 8 });

// Override deviceMemory
Object.defineProperty(navigator, 'deviceMemory', { get: () => 8 });

// Override permissions
const originalQuery = window.navigator.permissions.query;
window.navigator.permissions.query = (parameters) => (
    parameters.name === 'notifications' ?
        Promise.resolve({ state: Notification.permission }) :
        originalQuery(parameters)
);

// Override chrome runtime
window.chrome = { runtime: {} };

// Canvas fingerprint randomization
const originalGetContext = HTMLCanvasElement.prototype.getContext;
HTMLCanvasElement.prototype.getContext = function(type, attributes) {
    const context = originalGetContext.call(this, type, attributes);
    if (type === '2d' && context) {
        const originalFillText = context.fillText;
        context.fillText = function(...args) {
            // Add tiny random noise to text rendering
            args[1] += Math.random() * 0.1 - 0.05;
            args[2] += Math.random() * 0.1 - 0.05;
            return originalFillText.apply(this, args);
        };
    }
    return context;
};

// WebGL fingerprint randomization
const getParameterProxyHandler = {
    apply: function(target, thisArg, args) {
        const param = args[0];
        const result = target.apply(thisArg, args);
        // Add noise to certain parameters
        if (param === 37445) return 'Intel Inc.';
        if (param === 37446) return 'Intel Iris OpenGL Engine';
        return result;
    }
};

// AudioContext fingerprint
const originalAudioContext = window.AudioContext || window.webkitAudioContext;
if (originalAudioContext) {
    window.AudioContext = window.webkitAudioContext = function(...args) {
        const context = new originalAudioContext(...args);
        const originalCreateOscillator = context.createOscillator;
        context.createOscillator = function() {
            const oscillator = originalCreateOscillator.call(this);
            oscillator.frequency.value += Math.random() * 0.1;
            return oscillator;
        };
        return context;
    };
}

console.log('[Stealth] Anti-detection measures applied');
"""


class PlaywrightScraper:
    """Advanced scraper using Playwright with stealth mode"""
    
    def __init__(self, config):
        self.config = config
        self.base_url = config.get('target_url')
        self.job_id = config.get('job_id', 'unknown')
        self.extraction_mode = config.get('extraction_mode', 'single')  # single or full
        self.max_pages = config.get('max_pages', 10) if self.extraction_mode == 'full' else 1
        self.content_types = config.get('content_types', {
            'text': True, 'images': True, 'code': True, 'links': False,
            'json': True, 'tables': True, 'media': True, 'files': False
        })
        self.domain = urlparse(self.base_url).netloc
        self.visited = set()
        self.queue = [self.base_url]
        self.pages = []
        self.browser = None
        self.context = None
        
    def log(self, message, level='info'):
        """Log message in JSON format"""
        print(json.dumps({
            "job_id": self.job_id,
            "level": level,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }), flush=True)
        
    async def setup_browser(self):
        """Setup browser with anti-detection"""
        self.playwright = await async_playwright().start()
        
        # Launch browser with stealth settings
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-size=1920,1080',
                '--start-maximized',
            ]
        )
        
        # Create context with real browser settings
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=random.choice(USER_AGENTS),
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},
            permissions=['geolocation'],
            color_scheme='light',
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
            device_scale_factor=1,
            # Enable cookies and storage
            accept_downloads=True,
            ignore_https_errors=True,
        )
        
        # Add stealth script to all pages
        await self.context.add_init_script(STEALTH_JS)
        
        self.log("Browser initialized with stealth mode")
        
    async def extract_content(self, page, url):
        """Extract content based on configuration"""
        result = {
            'url': url,
            'title': await page.title(),
            'extracted_at': datetime.now().isoformat(),
        }
        
        # Extract text content
        if self.content_types.get('text', True):
            text_content = await page.evaluate('''() => {
                const clone = document.body.cloneNode(true);
                ['script', 'style', 'nav', 'footer', 'header', 'aside'].forEach(tag => {
                    clone.querySelectorAll(tag).forEach(el => el.remove());
                });
                return clone.innerText;
            }''')
            result['text'] = text_content[:100000]
            result['text_length'] = len(text_content)
            
        # Extract images
        if self.content_types.get('images', True):
            images = await page.evaluate('''() => {
                return Array.from(document.images).map(img => ({
                    src: img.src,
                    alt: img.alt,
                    width: img.naturalWidth,
                    height: img.naturalHeight
                })).filter(img => img.src && img.width > 50);
            }''')
            result['images'] = images[:100]
            result['images_count'] = len(images)
            
        # Extract code blocks
        if self.content_types.get('code', True):
            code_blocks = await page.evaluate('''() => {
                const blocks = [];
                document.querySelectorAll('pre, code, .highlight, .code-block').forEach(el => {
                    const text = el.innerText.trim();
                    if (text.length > 10) {
                        blocks.push({
                            tag: el.tagName.toLowerCase(),
                            language: el.className || 'unknown',
                            content: text.slice(0, 5000)
                        });
                    }
                });
                return blocks;
            }''')
            result['code_blocks'] = code_blocks[:50]
            result['code_count'] = len(code_blocks)
            
        # Extract links
        if self.content_types.get('links', False):
            links = await page.evaluate('''() => {
                return Array.from(document.links).map(a => ({
                    href: a.href,
                    text: a.innerText.trim().slice(0, 100)
                })).filter(l => l.href.startsWith('http'));
            }''')
            result['links'] = links[:500]
            result['links_count'] = len(links)
            
        # Extract JSON-LD and structured data
        if self.content_types.get('json', True):
            json_data = await page.evaluate('''() => {
                const data = [];
                document.querySelectorAll('script[type="application/ld+json"]').forEach(el => {
                    try {
                        data.push(JSON.parse(el.textContent));
                    } catch(e) {}
                });
                return data;
            }''')
            result['json_ld'] = json_data
            result['json_count'] = len(json_data)
            
        # Extract tables
        if self.content_types.get('tables', True):
            tables = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('table')).map(table => {
                    const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim());
                    const rows = Array.from(table.querySelectorAll('tr')).map(tr => 
                        Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim())
                    ).filter(row => row.length > 0);
                    return { headers, rows: rows.slice(0, 100) };
                });
            }''')
            result['tables'] = tables[:20]
            result['tables_count'] = len(tables)
            
        # Extract media (video/audio)
        if self.content_types.get('media', True):
            media = await page.evaluate('''() => {
                const items = [];
                document.querySelectorAll('video, audio, iframe[src*="youtube"], iframe[src*="vimeo"]').forEach(el => {
                    items.push({
                        type: el.tagName.toLowerCase(),
                        src: el.src || el.querySelector('source')?.src || el.getAttribute('src'),
                        poster: el.poster
                    });
                });
                return items;
            }''')
            result['media'] = media[:50]
            result['media_count'] = len(media)
            
        # Extract downloadable files
        if self.content_types.get('files', False):
            files = await page.evaluate('''() => {
                const extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.rar', '.csv'];
                return Array.from(document.links)
                    .filter(a => extensions.some(ext => a.href.toLowerCase().endsWith(ext)))
                    .map(a => ({ href: a.href, text: a.innerText.trim() }));
            }''')
            result['files'] = files[:100]
            result['files_count'] = len(files)
            
        return result
        
    async def scrape_page(self, url):
        """Scrape a single page with anti-detection"""
        try:
            self.log(f"Scraping: {url}")
            
            page = await self.context.new_page()
            
            # Random delay to simulate human behavior
            await asyncio.sleep(random.uniform(1, 3))
            
            # Navigate with realistic timeout
            await page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Random scroll to simulate reading
            await page.evaluate('''() => {
                window.scrollTo(0, Math.random() * 500);
            }''')
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Extract content
            result = await self.extract_content(page, url)
            
            # Get links for crawling if in full mode
            if self.extraction_mode == 'full':
                links = await page.evaluate('''(domain) => {
                    return Array.from(document.links)
                        .map(a => a.href)
                        .filter(href => {
                            try {
                                const url = new URL(href);
                                return url.hostname === domain;
                            } catch { return false; }
                        });
                }''', self.domain)
                
                for link in links:
                    if link not in self.visited and link not in self.queue:
                        self.queue.append(link)
            
            await page.close()
            return result
            
        except Exception as e:
            self.log(f"Error scraping {url}: {str(e)}", 'error')
            return None
            
    async def run(self):
        """Run the scraper"""
        start_time = time.time()
        
        try:
            await self.setup_browser()
            
            while self.queue and len(self.pages) < self.max_pages:
                url = self.queue.pop(0)
                
                if url in self.visited:
                    continue
                    
                self.visited.add(url)
                result = await self.scrape_page(url)
                
                if result:
                    self.pages.append(result)
                    
                # Anti-detection delay
                if len(self.pages) < self.max_pages and self.queue:
                    delay = random.uniform(2, 5)
                    self.log(f"Waiting {delay:.1f}s before next page...")
                    await asyncio.sleep(delay)
                    
        finally:
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
                
        elapsed = round(time.time() - start_time, 2)
        
        return {
            'job_id': self.job_id,
            'status': 'completed',
            'extraction_mode': self.extraction_mode,
            'pages_count': len(self.pages),
            'pages': self.pages,
            'elapsed': elapsed,
            'config': {
                'content_types': self.content_types,
                'max_pages': self.max_pages
            }
        }


class RequestsScraper:
    """Fallback scraper using requests (when Playwright not available)"""
    
    def __init__(self, config):
        self.config = config
        self.base_url = config.get('target_url')
        self.job_id = config.get('job_id', 'unknown')
        self.extraction_mode = config.get('extraction_mode', 'single')
        self.max_pages = config.get('max_pages', 10) if self.extraction_mode == 'full' else 1
        self.domain = urlparse(self.base_url).netloc
        self.visited = set()
        self.queue = [self.base_url]
        self.pages = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def log(self, message, level='info'):
        print(json.dumps({
            "job_id": self.job_id,
            "level": level,
            "message": message
        }), flush=True)
        
    def scrape_page(self, url):
        try:
            self.log(f"Scraping: {url}")
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title = soup.title.string.strip() if soup.title else ''
            
            # Remove unwanted elements
            for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
                tag.decompose()
                
            content = soup.get_text(separator='\n', strip=True)
            
            # Get links for crawling
            if self.extraction_mode == 'full':
                for a in soup.find_all('a', href=True):
                    link = urljoin(url, a['href'])
                    parsed = urlparse(link)
                    if parsed.netloc == self.domain and link not in self.visited:
                        self.queue.append(link)
                        
            return {
                'url': url,
                'title': title,
                'text': content[:100000],
                'text_length': len(content)
            }
            
        except Exception as e:
            self.log(f"Error: {str(e)}", 'error')
            return None
            
    def run(self):
        start = time.time()
        
        while self.queue and len(self.pages) < self.max_pages:
            url = self.queue.pop(0)
            if url in self.visited:
                continue
            self.visited.add(url)
            
            page = self.scrape_page(url)
            if page:
                self.pages.append(page)
                
            time.sleep(random.uniform(1, 3))
            
        return {
            'job_id': self.job_id,
            'status': 'completed',
            'extraction_mode': self.extraction_mode,
            'pages_count': len(self.pages),
            'pages': self.pages,
            'elapsed': round(time.time() - start, 2)
        }


def main():
    # Get configuration from environment
    config = {
        'target_url': os.environ.get('TARGET_URL'),
        'job_id': os.environ.get('JOB_ID', 'unknown'),
        'extraction_mode': os.environ.get('EXTRACTION_MODE', 'single'),
        'max_pages': int(os.environ.get('MAX_PAGES', '10')),
        'callback_url': os.environ.get('CALLBACK_URL'),
    }
    
    # Parse content types from JSON
    content_types_str = os.environ.get('CONTENT_TYPES', '{}')
    try:
        config['content_types'] = json.loads(content_types_str)
    except:
        config['content_types'] = {
            'text': True, 'images': True, 'code': True, 'links': False,
            'json': True, 'tables': True, 'media': True, 'files': False
        }
    
    if not config['target_url']:
        print(json.dumps({"status": "error", "message": "TARGET_URL required"}))
        sys.exit(1)
        
    print(json.dumps({
        "job_id": config['job_id'],
        "status": "starting",
        "target_url": config['target_url'],
        "extraction_mode": config['extraction_mode'],
        "has_playwright": HAS_PLAYWRIGHT
    }), flush=True)
    
    # Use Playwright if available, otherwise fallback to requests
    if HAS_PLAYWRIGHT:
        scraper = PlaywrightScraper(config)
        results = asyncio.run(scraper.run())
    else:
        scraper = RequestsScraper(config)
        results = scraper.run()
    
    # Send results to callback if configured
    if config['callback_url']:
        try:
            import requests as req
            req.post(config['callback_url'], json=results, timeout=30)
        except Exception as e:
            print(json.dumps({"error": f"Callback failed: {e}"}), flush=True)
    
    # Output results marker for log parsing
    print("---SCRAPER_RESULTS---")
    print(json.dumps(results))


if __name__ == "__main__":
    main()
