#!/usr/bin/env python3
"""
Universal Web Scraper
Downloads and extracts content from websites.
"""

import os
import sys
import json
import time
import hashlib
from urllib.parse import urljoin, urlparse
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup


class Scraper:
    def __init__(self, base_url, job_id, max_pages=50, output_dir="/tmp/scraper-output"):
        self.base_url = base_url
        self.job_id = job_id
        self.max_pages = max_pages
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.domain = urlparse(base_url).netloc
        self.visited = set()
        self.queue = [base_url]
        self.pages = []
        self.images = 0
        self.code_blocks = 0
        self.total_size = 0
        
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        })

    def log(self, msg, level="info"):
        timestamp = datetime.now().isoformat()
        log_entry = {"timestamp": timestamp, "level": level, "message": msg}
        print(json.dumps(log_entry), flush=True)

    def is_same_domain(self, url):
        parsed = urlparse(url)
        return parsed.netloc == self.domain or parsed.netloc == ""

    def normalize_url(self, url, base):
        if not url or url.startswith(("javascript:", "mailto:", "tel:", "#", "data:")):
            return None
        absolute = urljoin(base, url)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            return None
        # Remove fragment and normalize
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def save_progress(self):
        progress = {
            "job_id": self.job_id,
            "url": self.base_url,
            "pages_scraped": len(self.pages),
            "images": self.images,
            "code_blocks": self.code_blocks,
            "total_size_bytes": self.total_size,
            "queue_size": len(self.queue),
            "updated_at": datetime.now().isoformat()
        }
        with open(self.output_dir / "progress.json", "w") as f:
            json.dump(progress, f, indent=2)
        return progress

    def scrape_page(self, url):
        try:
            self.log(f"Scraping: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            content_size = len(response.content)
            self.total_size += content_size
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Get title
            title = ""
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            
            # Remove unwanted elements
            for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            
            # Get main content
            content = soup.get_text(separator="\n", strip=True)
            
            # Count images
            images = soup.find_all("img")
            self.images += len(images)
            
            # Count code blocks
            code_blocks = soup.find_all(["pre", "code"])
            self.code_blocks += len(code_blocks)
            
            # Extract links for crawling
            for a in soup.find_all("a", href=True):
                link = self.normalize_url(a["href"], url)
                if link and self.is_same_domain(link):
                    if link not in self.visited and link not in self.queue:
                        self.queue.append(link)
            
            # Save page content
            page_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            page_file = self.output_dir / f"page_{page_hash}.json"
            page_data = {
                "url": url,
                "title": title,
                "content": content[:50000],  # Limit content size
                "content_length": len(content),
                "images_count": len(images),
                "code_blocks_count": len(code_blocks),
                "scraped_at": datetime.now().isoformat()
            }
            with open(page_file, "w") as f:
                json.dump(page_data, f, indent=2)
            
            return {
                "url": url,
                "title": title,
                "content_length": len(content),
                "images": len(images),
                "code_blocks": len(code_blocks)
            }
            
        except requests.exceptions.RequestException as e:
            self.log(f"Error scraping {url}: {str(e)}", "error")
            return None
        except Exception as e:
            self.log(f"Unexpected error scraping {url}: {str(e)}", "error")
            return None

    def run(self):
        self.log(f"Starting scrape of {self.base_url}")
        self.log(f"Max pages: {self.max_pages}")
        
        start_time = time.time()
        
        while self.queue and len(self.pages) < self.max_pages:
            url = self.queue.pop(0)
            
            if url in self.visited:
                continue
            
            self.visited.add(url)
            
            page = self.scrape_page(url)
            if page:
                self.pages.append(page)
                progress = self.save_progress()
                self.log(f"Progress: {len(self.pages)}/{self.max_pages} pages, {self.images} images, {self.code_blocks} code blocks")
            
            # Be polite - wait between requests
            time.sleep(1)
        
        elapsed = time.time() - start_time
        
        # Final results
        results = {
            "job_id": self.job_id,
            "url": self.base_url,
            "status": "completed",
            "pages_scraped": len(self.pages),
            "images": self.images,
            "code_blocks": self.code_blocks,
            "total_size_bytes": self.total_size,
            "total_size_mb": round(self.total_size / (1024 * 1024), 2),
            "elapsed_seconds": round(elapsed, 2),
            "completed_at": datetime.now().isoformat()
        }
        
        with open(self.output_dir / "results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        self.log(f"Scraping completed: {len(self.pages)} pages in {elapsed:.1f}s")
        
        # Print final results as JSON for parsing
        print("---RESULTS---")
        print(json.dumps(results, indent=2))
        
        return results


def main():
    # Get configuration from environment
    target_url = os.environ.get("TARGET_URL")
    job_id = os.environ.get("JOB_ID", "unknown")
    max_pages = int(os.environ.get("MAX_PAGES", "10"))
    output_dir = os.environ.get("OUTPUT_DIR", "/tmp/scraper-output")
    
    if not target_url:
        print(json.dumps({"status": "error", "message": "TARGET_URL environment variable is required"}))
        sys.exit(1)
    
    scraper = Scraper(
        base_url=target_url,
        job_id=job_id,
        max_pages=max_pages,
        output_dir=output_dir
    )
    
    results = scraper.run()
    sys.exit(0 if results["status"] == "completed" else 1)


if __name__ == "__main__":
    main()
