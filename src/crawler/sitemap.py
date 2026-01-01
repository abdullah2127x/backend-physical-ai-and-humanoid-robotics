import xml.etree.ElementTree as ET
import httpx
import structlog

logger = structlog.get_logger(__name__)

async def fetch_sitemap_urls(url: str) -> list[str]:
    """Fetch and parse URLs from a sitemap.xml."""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            xml_content = response.text

        root = ET.fromstring(xml_content)
        namespace = ""
        if root.tag.startswith("{"):
            namespace = root.tag.split("}")[0] + "}"

        urls = []
        for url_elem in root.findall(f".//{namespace}url"):
            loc_elem = url_elem.find(f"{namespace}loc")
            if loc_elem is not None and loc_elem.text:
                urls.append(loc_elem.text.strip())

        # Handle sitemap indexes
        for sitemap_elem in root.findall(f".//{namespace}sitemap"):
            loc_elem = sitemap_elem.find(f"{namespace}loc")
            if loc_elem is not None and loc_elem.text:
                # Recursively fetch nested sitemaps
                nested_urls = await fetch_sitemap_urls(loc_elem.text.strip())
                urls.extend(nested_urls)

        # Filter for markdown-like documentation pages
        doc_urls = [
            url for url in urls
            if not any(ext in url.lower() for ext in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".css", ".js", ".pdf"])
        ]

        return sorted(list(set(doc_urls)))
    except Exception as e:
        logger.error("sitemap_fetch_error", url=url, error=str(e))
        return []
