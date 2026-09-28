import os
import re
import time
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

BOOK_URL = "https://novelping.com/book/martial-dao-i-can-enhance-my-talents"
FEED_PATH = "feed.xml"

REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
}


def normalize_url(href: str) -> str:
    href = (href or "").strip()
    if not href:
        return ""
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return "https://novelping.com" + href
    return href


def fetch_html(url: str, max_retries: int = 3, backoff_seconds: float = 2.0) -> str:
    session = requests.Session()
    session.headers.update(REQUEST_HEADERS)

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = session.get(url, timeout=20, allow_redirects=True)
            if response.status_code == 403:
                print(f"WARNING: Received 403 for {url} on attempt {attempt}/{max_retries}")
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(backoff_seconds * attempt)
                continue

    raise RuntimeError(f"Failed to fetch {url} after {max_retries} attempts") from last_error


def extract_chapter_links(html: str):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    seen = set()
    for a_tag in soup.select("a[href]"):
        href = normalize_url(a_tag.get("href", ""))
        if not href or href in seen:
            continue
        if "chapter" in href.lower() or "chapters" in href.lower() or "novel" in href.lower():
            seen.add(href)
            links.append(href)
    return links


def extract_chapter_title(url: str):
    try:
        html = fetch_html(url)
    except Exception:
        return None

    soup = BeautifulSoup(html, "html.parser")
    selectors = [
        "meta[property='og:title']",
        "meta[name='twitter:title']",
        "h1",
        ".chapter-title",
        ".entry-title",
        "title",
    ]

    for selector in selectors:
        tag = soup.select_one(selector)
        if not tag:
            continue
        value = tag.get("content") or tag.get_text(" ", strip=True)
        if value:
            return re.sub(r"\s+", " ", value).strip()
    return None


def ensure_feed_root():
    if not os.path.exists(FEED_PATH):
        root = ET.Element("rss")
        root.set("version", "2.0")
        channel = ET.SubElement(root, "channel")
        ET.SubElement(channel, "title").text = "Martial Dao: I Can Enhance My Talents — NovelPing"
        ET.SubElement(channel, "link").text = BOOK_URL
        ET.SubElement(channel, "description").text = "Automatic chapter update feed for Martial Dao: I Can Enhance My Talents."
        ET.SubElement(channel, "language").text = "en"
        ET.SubElement(channel, "generator").text = "NovelPing RSS GitHub Action"
        return root

    try:
        tree = ET.parse(FEED_PATH)
        root = tree.getroot()
        if root.tag == "rss":
            return root
    except ET.ParseError:
        pass

    root = ET.Element("rss")
    root.set("version", "2.0")
    channel = ET.SubElement(root, "channel")
    ET.SubElement(channel, "title").text = "Martial Dao: I Can Enhance My Talents — NovelPing"
    ET.SubElement(channel, "link").text = BOOK_URL
    ET.SubElement(channel, "description").text = "Automatic chapter update feed for Martial Dao: I Can Enhance My Talents."
    ET.SubElement(channel, "language").text = "en"
    ET.SubElement(channel, "generator").text = "NovelPing RSS GitHub Action"
    return root


def append_item(root: ET.Element, title: str, url: str):
    channel = root.find("channel")
    if channel is None:
        channel = ET.SubElement(root, "channel")

    for item in channel.findall("item"):
        if item.findtext("link") == url:
            return

    item = ET.Element("item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = url
    guid = ET.SubElement(item, "guid")
    guid.set("isPermaLink", "true")
    guid.text = url
    ET.SubElement(item, "description").text = f"New chapter available: {title}. Read it on NovelPing."

    channel.insert(0, item)


def update_feed():
    html = fetch_html(BOOK_URL)
    chapter_links = extract_chapter_links(html)
    root = ensure_feed_root()

    for url in chapter_links:
        title = extract_chapter_title(url)
        if title:
            append_item(root, title, url)

    ET.ElementTree(root).write(FEED_PATH, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    update_feed()
