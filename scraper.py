import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re

def extract_website_data(url):
    if not url.startswith("http"):
        url = "https://" + url

    headers = {"User-Agent": "Mozilla/5.0 (compatible; UsabilityAnalyzer/1.0)"}
    response = requests.get(url, timeout=15, headers=headers)
    response.raise_for_status()

    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    cleaned_text = " ".join(text.split())

    return html, cleaned_text, url

def check_broken_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a", href=True)
    broken = []
    checked = 0
    headers = {"User-Agent": "Mozilla/5.0 (compatible; UsabilityAnalyzer/1.0)"}

    for link in links[:5]:  # reduced to 5 to avoid memory crash
        href = link["href"]
        if href.startswith("mailto:") or href.startswith("tel:") or href == "#":
            continue
        full_url = urljoin(base_url, href)
        if not full_url.startswith("http"):
            continue
        try:
            r = requests.head(full_url, timeout=3, headers=headers, allow_redirects=True)
            if r.status_code >= 400:
                broken.append({"url": full_url, "status": r.status_code})
            checked += 1
        except Exception:
            broken.append({"url": full_url, "status": "Timeout/Error"})
            checked += 1

    return broken, checked

def extract_seo_data(html, url):
    soup = BeautifulSoup(html, "html.parser")
    seo = {}

    title_tag = soup.find("title")
    seo["title"] = title_tag.get_text().strip() if title_tag else None
    seo["title_length"] = len(seo["title"]) if seo["title"] else 0

    meta_desc = soup.find("meta", attrs={"name": "description"})
    seo["meta_description"] = meta_desc["content"].strip() if meta_desc and meta_desc.get("content") else None
    seo["meta_description_length"] = len(seo["meta_description"]) if seo["meta_description"] else 0

    meta_keywords = soup.find("meta", attrs={"name": "keywords"})
    seo["meta_keywords"] = meta_keywords["content"].strip() if meta_keywords and meta_keywords.get("content") else None

    canonical = soup.find("link", attrs={"rel": "canonical"})
    seo["canonical"] = canonical["href"] if canonical else None

    og_title = soup.find("meta", attrs={"property": "og:title"})
    seo["og_title"] = og_title["content"] if og_title else None

    og_desc = soup.find("meta", attrs={"property": "og:description"})
    seo["og_description"] = og_desc["content"] if og_desc else None

    seo["h1_count"] = len(soup.find_all("h1"))
    seo["h2_count"] = len(soup.find_all("h2"))
    seo["h3_count"] = len(soup.find_all("h3"))

    images = soup.find_all("img")
    seo["total_images"] = len(images)
    seo["images_missing_alt"] = sum(1 for img in images if not img.get("alt"))

    all_links = soup.find_all("a", href=True)
    base_domain = urlparse(url).netloc
    seo["internal_links"] = sum(1 for a in all_links if urlparse(urljoin(url, a["href"])).netloc == base_domain)
    seo["external_links"] = sum(1 for a in all_links if urlparse(urljoin(url, a["href"])).netloc != base_domain and a["href"].startswith("http"))

    robots = soup.find("meta", attrs={"name": "robots"})
    seo["robots"] = robots["content"] if robots else None

    return seo

def check_mobile_responsiveness(html):
    soup = BeautifulSoup(html, "html.parser")
    signals = {}

    viewport = soup.find("meta", attrs={"name": "viewport"})
    signals["has_viewport"] = viewport is not None
    signals["viewport_content"] = viewport["content"] if viewport else None

    raw_html = str(soup)
    signals["has_media_queries"] = "@media" in raw_html
    signals["has_responsive_classes"] = any(cls in raw_html for cls in [
        "col-md", "col-sm", "col-lg", "flex", "grid", "container-fluid",
        "responsive", "mobile", "sm:", "md:", "lg:"
    ])

    signals["has_fixed_widths"] = bool(re.search(r'width\s*:\s*\d{3,}px', raw_html))

    return signals
