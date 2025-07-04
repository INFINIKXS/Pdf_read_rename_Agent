import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from src.services.llm_client import LLMClient
"""
scholar_agent.py
Implements the Scholar Agent for the Multi-Agent Research System.
- Reads search terms from Search_terms.md
- (Future) Performs Google Scholar search, selects relevant papers, downloads PDFs
"""
import os
from typing import List, Optional

class ScholarAgent:

    def download_pdfs(self, papers, dest_folder="downloaded_papers", verbose=True, max_attempts=3, query=None, all_papers=None, llm_client=None):
        """
        Download PDFs for the given list of (title, link, score) papers.
        If a download fails, use the next best PDF from all_papers (by LLM score) as a replacement.
        Args:
            papers: List of (title, link, score) tuples (top N selected).
            dest_folder: Where to save PDFs.
            verbose: Print status and errors.
            max_attempts: Max number of papers to download.
            query: The original search query (for LLM replacement).
            all_papers: All (title, link) tuples from the search (for replacement).
            llm_client: Optional, for LLM-based scoring.
        Returns:
            List of (title, link, score, status, filename or error) for each attempt.
        """
        import requests
        import os
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)
        results = []
        used_links = set(link for _, link, _ in papers)
        attempts = 0
        idx = 0
        while attempts < max_attempts and idx < len(papers):
            title, link, score = papers[idx]
            if link and link.lower().endswith('.pdf'):
                try:
                    filename = os.path.join(dest_folder, f"{attempts+1}_{self.sanitize_filename(title)}.pdf")
                    r = requests.get(link, timeout=20)
                    if r.status_code == 200 and r.headers.get('content-type', '').startswith('application/pdf'):
                        with open(filename, 'wb') as f:
                            f.write(r.content)
                        if verbose:
                            print(f"[PDF OK] Downloaded: {title}\n   {link}")
                        results.append((title, link, score, 'success', filename))
                        attempts += 1
                    else:
                        raise Exception(f"Not a PDF or bad status: {r.status_code}")
                except Exception as e:
                    if verbose:
                        print(f"[PDF FAIL] {title}\n   {link}\n   Error: {e}")
                    results.append((title, link, score, 'fail', str(e)))
                    # Try to replace with next best PDF from all_papers
                    if all_papers and query and llm_client:
                        replacement = self.find_next_pdf_replacement(query, all_papers, used_links, llm_client, verbose)
                        if replacement:
                            papers.append(replacement)
                            used_links.add(replacement[1])
            else:
                # Try landing page PDF detection before skipping
                pdf_url = None
                if link:
                    pdf_url = self.find_pdf_on_landing_page(link, verbose)
                if pdf_url:
                    # Try to download the found PDF
                    try:
                        filename = os.path.join(dest_folder, f"{attempts+1}_{self.sanitize_filename(title)}.pdf")
                        r = requests.get(pdf_url, timeout=20)
                        if r.status_code == 200 and r.headers.get('content-type', '').startswith('application/pdf'):
                            with open(filename, 'wb') as f:
                                f.write(r.content)
                            if verbose:
                                print(f"[PDF OK] Downloaded from landing page: {title}\n   {pdf_url}")
                            results.append((title, pdf_url, score, 'success', filename))
                            attempts += 1
                            idx += 1
                            continue
                        else:
                            raise Exception(f"Not a PDF or bad status: {r.status_code}")
                    except Exception as e:
                        if verbose:
                            print(f"[PDF FAIL] (landing page) {title}\n   {pdf_url}\n   Error: {e}")
                        results.append((title, pdf_url, score, 'fail', str(e)))
                if verbose:
                    print(f"[SKIP] Not a direct PDF: {title}\n   {link}")
                results.append((title, link, score, 'skip', 'Not a direct PDF link'))
                # Try to replace with next best PDF from all_papers
                if all_papers and query and llm_client:
                    replacement = self.find_next_pdf_replacement(query, all_papers, used_links, llm_client, verbose)
                    if replacement:
                        papers.append(replacement)
                        used_links.add(replacement[1])
            idx += 1
        return results

    import time

    def _llm_score_with_retry(self, query, title, llm_client, verbose, max_retries=5, min_interval=12.1):
        """
        Calls llm_client.generate_content(prompt) with retry and backoff to respect 5 requests/minute (12s interval).
        Builds the prompt from query and title.
        Returns a float score (0.0 if failed).
        """
        import time
        prompt = f"""
You are an expert research assistant. Given the following search query and a paper title, rate the relevance of the paper to the query on a scale from 0 (not relevant) to 1 (highly relevant). Only output a single number between 0 and 1.

Search Query: {query}
Paper Title: {title}
"""
        last_call = getattr(self, '_last_llm_call', 0)
        now = time.time()
        wait_time = max(0, min_interval - (now - last_call))
        if wait_time > 0:
            if verbose:
                print(f"[LLM] Waiting {wait_time:.1f}s to respect rate limit...")
            time.sleep(wait_time)
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                result = llm_client.generate_content(prompt).strip()
                self._last_llm_call = time.time()
                return float(result)
            except Exception as e:
                last_exception = e
                if verbose:
                    print(f"[LLM RETRY] Attempt {attempt} failed for '{title}': {e}")
                if attempt < max_retries:
                    time.sleep(min_interval)
        if verbose:
            print(f"[LLM ERROR] Could not score '{title}' after {max_retries} attempts: {last_exception}")
        return 0.0

    def find_next_pdf_replacement(self, query, all_papers, used_links, llm_client, verbose):
        """
        Find the next best PDF paper (not already used) using LLM scoring, with retry/backoff for rate limits.
        Returns (title, link, score) or None.
        """
        candidates = [(title, link) for (title, link) in all_papers if link and link.lower().endswith('.pdf') and link not in used_links]
        if not candidates:
            if verbose:
                print("[REPLACE] No more PDF candidates available.")
            return None
        scored = []
        for title, link in candidates:
            score = self._llm_score_with_retry(query, title, llm_client, verbose)
            scored.append((title, link, score))
        scored.sort(key=lambda x: x[2], reverse=True)
        if scored:
            best = scored[0]
            if verbose:
                print(f"[REPLACE] Using replacement PDF: {best[0]}\n   {best[1]}\n   Score: {best[2]}")
            return best
        return None

    @staticmethod
    def sanitize_filename(name: str) -> str:
        import re
        name = re.sub(r'[\\/:*?"<>|]', '', name)
        name = name.strip().replace(' ', '_')
        return name[:100]

    from typing import Optional

    def select_top_papers_llm(self, query: str, papers: list, llm_client: 'Optional[LLMClient]' = None, top_n: int = 3, verbose: bool = True) -> list:
        """
        Use LLM to score and select the top N most relevant papers based on title (and optionally link), with retry/backoff for rate limits.
        Args:
            query (str): The original search query.
            papers (list): List of (title, link) tuples.
            llm_client (Optional[LLMClient]): Optional, will create if not provided.
            top_n (int): Number of top papers to select.
            verbose (bool): Print LLM scores and errors.
        Returns:
            List of (title, link, score) tuples for the top N papers.
        """
        if llm_client is None:
            llm_client = LLMClient()
        scored = []
        for title, link in papers:
            score = self._llm_score_with_retry(query, title, llm_client, verbose)
            scored.append((title, link, score))
        # Sort by score descending and return top N
        scored.sort(key=lambda x: x[2], reverse=True)
        if verbose:
            print("\n[LLM] Top papers by relevance:")
            for i, (title, link, score) in enumerate(scored[:top_n], 1):
                print(f"{i}. {title}\n   {link}\n   Score: {score}")
        return scored[:top_n]
    def find_pdf_on_landing_page(self, url: str, verbose: bool = True) -> Optional[str]:
        """
        (MCP REMOVED) Stub: No Playwright MCP tool used. Always returns None.
        """
        if verbose:
            print(f"[Playwright MCP] (MCP REMOVED) Skipping landing page PDF extraction for: {url}")
        return None

    def scholar_search(self, query: str, verbose: bool = True, num_results: int = 20) -> list:
        """
        Perform a Google Scholar search for the given query using Selenium in headless mode.
        Returns a list of up to `num_results` (title, link) tuples for the top results.
        If blocked by CAPTCHA or fails, retries with Exa MCP web search as a fallback.
        """
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from webdriver_manager.chrome import ChromeDriverManager
        import random, time

        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
        ]
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument(f'user-agent={random.choice(user_agents)}')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')

        from selenium.webdriver.chrome.service import Service
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        results = []
        captcha_or_error = False
        try:
            driver.get('https://scholar.google.com/')
            time.sleep(random.uniform(2, 4))
            search_box = driver.find_element(By.NAME, 'q')
            search_box.clear()
            search_box.send_keys(query)
            time.sleep(random.uniform(1, 2))
            search_box.send_keys(Keys.RETURN)
            time.sleep(random.uniform(2, 4))
            if 'captcha' in driver.page_source.lower():
                if verbose:
                    print(f"[CAPTCHA detected] Google Scholar blocked the search for: {query}")
                captcha_or_error = True
            else:
                # Scrape top N result titles and links
                articles = driver.find_elements(By.CSS_SELECTOR, 'div.gs_r.gs_or.gs_scl')[:num_results]
                for art in articles:
                    try:
                        title_elem = art.find_element(By.CSS_SELECTOR, 'h3.gs_rt')
                        title = title_elem.text
                        link = None
                        a_tag = title_elem.find_elements(By.TAG_NAME, 'a')
                        if a_tag:
                            link = a_tag[0].get_attribute('href')
                            # If not a direct PDF, try landing page PDF detection
                            if link and not link.lower().endswith('.pdf'):
                                pdf_url = self.find_pdf_on_landing_page(link, verbose)
                                if pdf_url:
                                    link = pdf_url
                        results.append((title, link))
                    except Exception:
                        continue
                if verbose:
                    print(f"[OK] Search completed for: {query}")
                    for i, (title, link) in enumerate(results, 1):
                        print(f"{i}. {title}\n   {link}")
        except Exception as e:
            if verbose:
                print(f"[ERROR] Scholar search failed for '{query}': {e}")
            captcha_or_error = True
        finally:
            driver.quit()

        # Fallback to MCP removed: Only use Selenium results
        return results

    def __init__(self, search_terms_file: str = "Search_terms.md"):
        self.search_terms_file = search_terms_file

    def read_search_terms(self) -> List[str]:
        """
        Reads search terms from a markdown file, one per line.
        Only lines that look like real search queries (e.g., contain parentheses, AND/OR, or quote marks) are included.
        Ignores empty lines, comments, headings, and instructional text.
        Returns:
            List[str]: List of search terms.
        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.exists(self.search_terms_file):
            raise FileNotFoundError(f"Search terms file not found: {self.search_terms_file}")
        terms = []
        with open(self.search_terms_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines, comments, headings, and tips
                if not line or line.startswith("#"):
                    continue
                # Exclude lines that are all uppercase and short (likely section headers)
                if line.isupper() and len(line) < 40:
                    continue
                # Exclude lines that start with known instructional phrases or end with a colon
                if (
                    line.startswith("Example:") or
                    line.startswith("Pro-Tip:") or
                    line.startswith("Tips for") or
                    line.endswith(":")
                ):
                    continue
                # Exclude Boolean operator explanations
                if line.strip() in [
                    "AND: Narrows your search (all terms must be present).",
                    "OR: Broadens your search (any of the terms can be present)."
                ]:
                    continue
                # Heuristic: Only include lines that look like search queries
                if (
                    ("AND" in line or "OR" in line)
                    and ("(" in line or ")" in line)
                ) or (
                    '"' in line and ("AND" in line or "OR" in line)
                ):
                    terms.append(line)
        return terms

if __name__ == "__main__":
    agent = ScholarAgent()
    try:
        terms = agent.read_search_terms()
        print("Search terms loaded:", terms)
        if terms:
            print("Testing Scholar search for first query...")
            all_papers = agent.scholar_search(terms[0], num_results=20)
            print(f"\nTotal papers found: {len(all_papers)}")
            if all_papers:
                print("\nScoring and selecting top 3 papers with LLM...")
                llm_client = LLMClient()
                top_papers = agent.select_top_papers_llm(terms[0], all_papers, llm_client=llm_client, verbose=True)
                print("\nAttempting to download top 3 PDFs (with LLM-based replacement if needed)...")
                download_results = agent.download_pdfs(top_papers, all_papers=all_papers, query=terms[0], llm_client=llm_client, verbose=True)
                print("\nDownload summary:")
                for res in download_results:
                    print(res)
    except Exception as e:
        print("Error:", e)
