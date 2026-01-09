#!/usr/bin/env python3
import os, sys, json, time, requests
from urllib.parse import urljoin, urlparse
from datetime import datetime
from bs4 import BeautifulSoup

class Scraper:
    def __init__(self, base_url, job_id, max_pages=10):
        self.base_url = base_url
        self.job_id = job_id
        self.max_pages = max_pages
        self.domain = urlparse(base_url).netloc
        self.visited = set()
        self.queue = [base_url]
        self.pages = []
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"})

    def scrape_page(self, url):
        try:
            print(json.dumps({"job_id": self.job_id, "message": f"Scraping: {url}"}), flush=True)
            response = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response.text, "html.parser")
            title = soup.title.string.strip() if soup.title else ""
            for tag in soup.find_all(["script", "style", "nav", "footer"]):
                tag.decompose()
            content = soup.get_text(separator="\n", strip=True)
            for a in soup.find_all("a", href=True):
                link = urljoin(url, a["href"])
                parsed = urlparse(link)
                if parsed.netloc == self.domain and link not in self.visited:
                    self.queue.append(link)
            return {"url": url, "title": title, "content": content[:50000]}
        except Exception as e:
            print(json.dumps({"job_id": self.job_id, "error": str(e)}), flush=True)
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
            time.sleep(1)
        return {
            "job_id": self.job_id,
            "status": "completed",
            "pages_count": len(self.pages),
            "pages": self.pages,
            "elapsed": round(time.time() - start, 2)
        }

def main():
    target_url = os.environ.get("TARGET_URL")
    job_id = os.environ.get("JOB_ID", "unknown")
    max_pages = int(os.environ.get("MAX_PAGES", "10"))
    callback_url = os.environ.get("CALLBACK_URL")
    
    if not target_url:
        print(json.dumps({"status": "error", "message": "TARGET_URL required"}))
        sys.exit(1)
    
    print(json.dumps({"job_id": job_id, "status": "starting", "target_url": target_url}), flush=True)
    
    scraper = Scraper(target_url, job_id, max_pages)
    results = scraper.run()
    
    # Se tiver callback URL, envia os resultados
    if callback_url:
        try:
            requests.post(callback_url, json=results, timeout=30)
        except Exception as e:
            print(json.dumps({"error": f"Callback failed: {e}"}), flush=True)
    
    print("---SCRAPER_RESULTS---")
    print(json.dumps(results))

if __name__ == "__main__":
    main()
