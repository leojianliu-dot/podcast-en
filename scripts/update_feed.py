#!/usr/bin/env python3
"""
Generate/update the RSS podcast feed (feed.xml) by scanning the episodes/ folder.

Usage:
    python scripts/update_feed.py

Reads settings from podcast-settings.json and scans episodes/ for MP3 files.
Generates a valid podcast RSS 2.0 feed with iTunes namespace.

Language is detected from the matching script file content (Chinese vs English).
Episode titles are generated based on filename pattern and detected language.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from email.utils import formatdate
from xml.sax.saxutils import escape

# Try to import mutagen for MP3 duration; fall back to estimation
try:
    from mutagen.mp3 import MP3
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False
    print("Warning: mutagen not installed. Episode durations will be estimated.")


# Paths (relative to project root)
SETTINGS_FILE = "podcast-settings.json"
EPISODES_DIR = "episodes"
SCRIPTS_DIR = "episode-scripts"
FEED_FILE = "feed.xml"

# Daily update slot names
DAILY_SLOTS_ZH = {
    "morning": "早间新闻",
    "midday": "午间新闻",
    "evening": "晚间新闻",
}

DAILY_SLOTS_EN = {
    "morning": "Morning News",
    "midday": "Midday News",
    "evening": "Evening News",
}


def load_settings():
    """Load podcast settings from JSON file."""
    if not os.path.exists(SETTINGS_FILE):
        print(f"Error: {SETTINGS_FILE} not found. Run from project root.")
        sys.exit(1)

    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def get_mp3_info(filepath):
    """Get duration (seconds) and size (bytes) of an MP3 file."""
    size = os.path.getsize(filepath)
    duration = None

    if HAS_MUTAGEN:
        try:
            audio = MP3(filepath)
            duration = int(audio.info.length)
        except Exception:
            pass

    # Estimate duration from file size if mutagen fails
    # ~128kbps is typical for edge-tts output
    if duration is None:
        duration = int(size / (128 * 1000 / 8))

    return size, duration


def format_duration_itunes(seconds):
    """Format seconds as HH:MM:SS for iTunes duration tag."""
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def detect_language_from_content(text):
    """Detect language by analyzing text content. Returns 'en' or 'zh'.

    Counts CJK characters vs Latin characters.
    If CJK characters make up more than 20% of all letters, it's Chinese.
    """
    cjk_count = 0
    latin_count = 0
    for char in text:
        cp = ord(char)
        if (0x4E00 <= cp <= 0x9FFF or
            0x3400 <= cp <= 0x4DBF or
            0xF900 <= cp <= 0xFAFF):
            cjk_count += 1
        elif char.isalpha():
            latin_count += 1
    total = cjk_count + latin_count
    if total == 0:
        return "zh"
    return "zh" if (cjk_count / total) > 0.2 else "en"


def detect_language_for_episode(mp3_filename):
    """Detect language for an episode by reading its script file content."""
    name = os.path.splitext(mp3_filename)[0]
    for ext in [".md", ".txt"]:
        script_path = os.path.join(SCRIPTS_DIR, name + ext)
        if os.path.exists(script_path):
            with open(script_path, "r", encoding="utf-8") as f:
                text = f.read()
            return detect_language_from_content(text)
    # Fallback: assume Chinese
    return "zh"


def get_episode_title(mp3_filename, lang="zh"):
    """Generate episode title from filename and detected language.

    Naming conventions:
        2026-02-25.mp3          + zh -> "2026-02-25 每日新闻"
        2026-02-25.mp3          + en -> "2026-02-25 Daily News"
        2026-02-25-morning.mp3  + zh -> "2026-02-25 早间新闻"
        2026-02-25-morning.mp3  + en -> "2026-02-25 Morning News"
        2026-02-25-ai.mp3       + zh -> "2026-02-25 AI 专题"
        2026-02-25-ai.mp3       + en -> "2026-02-25 AI Special Report"
    """
    name = os.path.splitext(mp3_filename)[0]

    # Split into date and topic parts: YYYY-MM-DD-topic
    parts = name.split("-", 3)
    date_str = f"{parts[0]}-{parts[1]}-{parts[2]}" if len(parts) >= 3 else name

    if len(parts) > 3:
        topic = parts[3]

        if lang == "en":
            slot_title = DAILY_SLOTS_EN.get(topic)
            if slot_title:
                return f"{date_str} {slot_title}"
            return f"{date_str} {topic.upper()} Special Report"
        else:
            slot_title = DAILY_SLOTS_ZH.get(topic)
            if slot_title:
                return f"{date_str} {slot_title}"
            return f"{date_str} {topic.upper()} 专题"
    else:
        if lang == "en":
            return f"{date_str} Daily News"
        else:
            return f"{date_str} 每日新闻"


def get_custom_title_from_script(mp3_filename):
    """Try to read a custom Title: metadata line from the matching script file.

    If the script file contains a line like 'Title: 墨西哥毒枭专题报道',
    that title is used instead of the auto-generated filename-based title.

    Searches the first 15 lines to be resilient against preamble text
    that the model may have inserted before the Title: line.
    """
    name = os.path.splitext(mp3_filename)[0]
    for ext in [".md", ".txt"]:
        script_path = os.path.join(SCRIPTS_DIR, name + ext)
        if os.path.exists(script_path):
            with open(script_path, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i >= 15:
                        break
                    line = line.strip()
                    if line.startswith("Title:"):
                        return line[len("Title:"):].strip()
    return None


def get_episode_description(mp3_filename):
    """Try to read the first few lines of the matching script file for description."""
    name = os.path.splitext(mp3_filename)[0]

    # Look for matching script file
    for ext in [".md", ".txt"]:
        script_path = os.path.join(SCRIPTS_DIR, name + ext)
        if os.path.exists(script_path):
            with open(script_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            # Get first non-empty, non-header lines as description
            desc_lines = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("---"):
                    continue
                if line.startswith(("Date:", "Voice:", "Format:", "Language:", "Topic:", "Sources:", "Title:")):
                    continue
                desc_lines.append(line)
                if len(desc_lines) >= 3:
                    break
            if desc_lines:
                return " ".join(desc_lines)[:300]

    return f"{get_episode_title(mp3_filename)}"


def get_file_date(filepath):
    """Get file modification time as a datetime."""
    timestamp = os.path.getmtime(filepath)
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def generate_feed(settings, episodes):
    """Generate RSS XML string."""
    base_url = settings["base_url"].rstrip("/")
    podcast_name = escape(settings["podcast_name"])
    description = escape(settings["description"])
    author = escape(settings["author"])
    language = settings["language"]
    category = escape(settings.get("category", "News"))
    subcategory = escape(settings.get("subcategory", "Daily News"))
    image_url = settings.get("image_url", "")

    # Build date for channel
    now_rfc2822 = formatdate(timeval=None, localtime=False, usegmt=True)

    # Start building XML
    xml_parts = []
    xml_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    xml_parts.append('<rss version="2.0"')
    xml_parts.append('  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"')
    xml_parts.append('  xmlns:content="http://purl.org/rss/1.0/modules/content/"')
    xml_parts.append('  xmlns:atom="http://www.w3.org/2005/Atom">')
    xml_parts.append("  <channel>")

    # Channel metadata
    xml_parts.append(f"    <title>{podcast_name}</title>")
    xml_parts.append(f"    <description>{description}</description>")
    xml_parts.append(f"    <language>{language}</language>")
    xml_parts.append(f"    <lastBuildDate>{now_rfc2822}</lastBuildDate>")
    xml_parts.append(f"    <link>{escape(base_url)}</link>")
    xml_parts.append(f'    <atom:link href="{escape(base_url)}/feed.xml" rel="self" type="application/rss+xml"/>')

    # iTunes tags
    xml_parts.append(f"    <itunes:author>{author}</itunes:author>")
    xml_parts.append(f"    <itunes:summary>{description}</itunes:summary>")
    xml_parts.append(f'    <itunes:category text="{category}">')
    xml_parts.append(f'      <itunes:category text="{subcategory}"/>')
    xml_parts.append("    </itunes:category>")
    xml_parts.append("    <itunes:explicit>no</itunes:explicit>")
    xml_parts.append(f"    <itunes:type>episodic</itunes:type>")

    if image_url:
        xml_parts.append(f'    <itunes:image href="{escape(image_url)}"/>')

    # Episodes (newest first)
    for ep in episodes:
        pub_date = formatdate(timeval=ep["date"].timestamp(), localtime=False, usegmt=True)
        title = escape(ep["title"])
        desc = escape(ep["description"])
        url = escape(f'{base_url}/episodes/{ep["filename"]}')
        duration = format_duration_itunes(ep["duration"])
        guid = f'{base_url}/episodes/{ep["filename"]}'

        xml_parts.append("    <item>")
        xml_parts.append(f"      <title>{title}</title>")
        xml_parts.append(f"      <description>{desc}</description>")
        xml_parts.append(f'      <enclosure url="{url}" length="{ep["size"]}" type="audio/mpeg"/>')
        xml_parts.append(f"      <guid isPermaLink=\"true\">{escape(guid)}</guid>")
        xml_parts.append(f"      <pubDate>{pub_date}</pubDate>")
        xml_parts.append(f"      <itunes:duration>{duration}</itunes:duration>")
        xml_parts.append(f"      <itunes:author>{author}</itunes:author>")
        xml_parts.append(f"      <itunes:summary>{desc}</itunes:summary>")
        xml_parts.append("      <itunes:explicit>no</itunes:explicit>")
        xml_parts.append("    </item>")

    xml_parts.append("  </channel>")
    xml_parts.append("</rss>")

    return "\n".join(xml_parts)


def cleanup_old_episodes(max_age_days=2):
    """Delete episodes and scripts older than max_age_days based on filename date.

    Parses the date from filenames like 2026-02-25-morning.mp3 and removes
    both the .mp3 in episodes/ and the matching .md in episode-scripts/.
    """
    today = datetime.now(timezone.utc).date()
    cutoff = today - timedelta(days=max_age_days)
    date_pattern = re.compile(r'^(\d{4}-\d{2}-\d{2})')
    removed = []

    # Clean episodes/
    if os.path.exists(EPISODES_DIR):
        for f in os.listdir(EPISODES_DIR):
            if not f.endswith(".mp3"):
                continue
            m = date_pattern.match(f)
            if not m:
                continue
            try:
                file_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
            except ValueError:
                continue
            if file_date < cutoff:
                path = os.path.join(EPISODES_DIR, f)
                os.remove(path)
                removed.append(f"episodes/{f}")

    # Clean episode-scripts/
    if os.path.exists(SCRIPTS_DIR):
        for f in os.listdir(SCRIPTS_DIR):
            if not (f.endswith(".md") or f.endswith(".txt")):
                continue
            m = date_pattern.match(f)
            if not m:
                continue
            try:
                file_date = datetime.strptime(m.group(1), "%Y-%m-%d").date()
            except ValueError:
                continue
            if file_date < cutoff:
                path = os.path.join(SCRIPTS_DIR, f)
                os.remove(path)
                removed.append(f"episode-scripts/{f}")

    if removed:
        print(f"Cleaned up {len(removed)} old files (>{max_age_days} days):")
        for r in removed:
            print(f"  - {r}")
    return removed


def main():
    # Fix Chinese character output on Windows console
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # Clean up episodes older than 2 days
    cleanup_old_episodes(max_age_days=2)

    # Load settings
    settings = load_settings()

    if settings["base_url"] == "REPLACE_WITH_GITHUB_PAGES_URL":
        print("Warning: base_url in podcast-settings.json is not configured yet.")
        print("The feed will be generated but episode URLs won't work until you set the base URL.")
        print("After enabling GitHub Pages, update base_url to: https://USERNAME.github.io/REPO-NAME")
        print()

    # Scan episodes directory
    if not os.path.exists(EPISODES_DIR):
        print(f"No episodes/ directory found. Nothing to do.")
        sys.exit(0)

    mp3_files = sorted(
        [f for f in os.listdir(EPISODES_DIR) if f.endswith(".mp3")],
        reverse=True  # Newest first
    )

    if not mp3_files:
        print("No MP3 files found in episodes/. Nothing to do.")
        sys.exit(0)

    # Build episode list
    episodes = []
    for filename in mp3_files:
        filepath = os.path.join(EPISODES_DIR, filename)
        size, duration = get_mp3_info(filepath)
        lang = detect_language_for_episode(filename)
        title = get_custom_title_from_script(filename) or get_episode_title(filename, lang)
        description = get_episode_description(filename)
        date = get_file_date(filepath)

        episodes.append({
            "filename": filename,
            "title": title,
            "description": description,
            "size": size,
            "duration": duration,
            "date": date,
        })

    # Generate feed
    feed_xml = generate_feed(settings, episodes)

    # Write feed
    with open(FEED_FILE, "w", encoding="utf-8") as f:
        f.write(feed_xml)

    print(f"Feed updated: {FEED_FILE}")
    print(f"Episodes: {len(episodes)}")
    for ep in episodes:
        dur = format_duration_itunes(ep["duration"])
        print(f"  - {ep['title']} ({dur})")


if __name__ == "__main__":
    main()
