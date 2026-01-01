import httpx
from bs4 import BeautifulSoup
import structlog
import asyncio

logger = structlog.get_logger(__name__)

async def scrape_url(url: str, timeout: float = 30.0) -> str:
    """Scrape text content from a URL and convert to markdown-like text."""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text

        soup = BeautifulSoup(html, 'html.parser')

        # Docusaurus specific: target the main article or content area
        main_content = soup.find('article') or soup.find('main') or soup.find('body')

        if not main_content:
            return ""

        # Remove nav, footer, sidebar to get clean content
        for element in main_content.find_all(['nav', 'footer', 'header', 'aside', 'script', 'style']):
            element.decompose()

        # Get text while preserving some structure
        text = main_content.get_text(separator=' ', strip=True)
        return text
    except Exception as e:
        logger.error("scrape_error", url=url, error=str(e))
        return ""

async def scrape_batch(urls: list[str], batch_size: int = 5) -> dict[str, str]:
    """Scrape a list of URLs in batches."""
    results = {}
    for i in range(0, len(urls), batch_size):
        batch = urls[i:i+batch_size]
        tasks = [scrape_url(url) for url in batch]
        batch_results = await asyncio.gather(*tasks)

        for url, content in zip(batch, batch_results):
            if content:
                results[url] = content

        # Small delay between batches to be polite
        await asyncio.sleep(1)

    return results
