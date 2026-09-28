import os
import re
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup

BOOK_URL = "https://novelping.com/book/martial-dao-i-can-enhance-my-talents"
FEED_PATH = "feed.xml"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://novelping.com/",
    "Upgrade-Insecure-Requests": "1",
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


def fetch_html(url: str) -> str:
    try:
        response = requests.get(
            url,
            timeout=20,
            headers=DEFAULT_HEADERS,
            allow_redirects=True,
        )
        if response.status_code == 403:
            print(f"Skipping blocked page: {url} (HTTP 403)")
            return ""
        response.raise_for_status()
        return response.text
    except requests.RequestException as exc:
        print(f"Request failed for {url}: {exc}")
        return ""


def extract_chapter_links(html: str):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a_tag in soup.select("a[href]"):
        href = normalize_url(a_tag.get("href", ""))
        if not href:
            continue
        if "chapter-" in href and href not in links:
            links.append(href)
    return links


def extract_chapter_title(url: str):
    try:
        html = fetch_html(url)
    except Exception:
        return None

    if not html:
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
