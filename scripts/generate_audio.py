#!/usr/bin/env python3
"""
Generate podcast audio from a script using Edge TTS.
Supports both Mandarin Chinese and English with auto-detection from content.

Usage:
    python scripts/generate_audio.py episode-scripts/2026-02-24.md
    python scripts/generate_audio.py episode-scripts/2026-02-24.md -v zh-CN-XiaoxiaoNeural
    python scripts/generate_audio.py episode-scripts/2026-02-24.md -o episodes/custom-name.mp3

Language detection:
    Automatically detects whether the script is Chinese or English by
    analyzing the text content. If most characters are CJK, uses Chinese
    voice; otherwise uses English voice.
"""

import asyncio
import argparse
import os
import sys
import re
from datetime import datetime

import edge_tts


# Available Mandarin Chinese voices
VOICES_ZH = {
    "yunxi": "zh-CN-YunxiNeural",       # Male, professional (default)
    "xiaoxiao": "zh-CN-XiaoxiaoNeural",  # Female, warm
    "yunjian": "zh-CN-YunjianNeural",    # Male, news anchor
    "xiaoyi": "zh-CN-XiaoyiNeural",      # Female, conversational
}

# Available English voices
VOICES_EN = {
    "guy": "en-US-GuyNeural",            # Male, professional (default)
    "jenny": "en-US-JennyNeural",        # Female, warm
    "aria": "en-US-AriaNeural",          # Female, conversational
    "davis": "en-US-DavisNeural",        # Male, authoritative
    "andrew": "en-US-AndrewNeural",      # Male, natural
}

DEFAULT_VOICE_ZH = "zh-CN-YunxiNeural"
DEFAULT_VOICE_EN = "en-US-GuyNeural"


def detect_language_from_content(text):
    """Detect language by analyzing text content. Returns 'en' or 'zh'.

    Counts CJK (Chinese/Japanese/Korean) characters vs Latin characters.
    If CJK characters make up more than 20% of all letters, it's Chinese.
    """
    cjk_count = 0
    latin_count = 0
    for char in text:
        cp = ord(char)
        # CJK Unified Ideographs and extensions
        if (0x4E00 <= cp <= 0x9FFF or    # CJK Unified
            0x3400 <= cp <= 0x4DBF or    # CJK Extension A
            0xF900 <= cp <= 0xFAFF):     # CJK Compatibility
            cjk_count += 1
        elif char.isalpha():
            latin_count += 1
    total = cjk_count + latin_count
    if total == 0:
        return "zh"  # default
    return "zh" if (cjk_count / total) > 0.2 else "en"


def clean_script_for_tts(text):
    """Remove markdown formatting and metadata that shouldn't be read aloud."""
    # Remove markdown headers (# lines)
    text = re.sub(r'^#{1,6}\s+.*$', '', text, flags=re.MULTILINE)
    # Remove markdown bold/italic markers
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    # Remove markdown links [text](url) -> text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Remove horizontal rules
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    # Remove HTML tags if any
    text = re.sub(r'<[^>]+>', '', text)
    # Remove lines that are just metadata (e.g., "Date:", "Voice:", "Format:")
    text = re.sub(r'^(Date|Voice|Format|Topic|Duration|Sources?|Language|Title):.*$', '', text, flags=re.MULTILINE)
    # Collapse multiple blank lines into one
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


async def generate_audio(text, output_file, voice, rate="+0%"):
    """Generate MP3 from text using Edge TTS."""
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_file)


def get_audio_duration(filepath):
    """Get duration of MP3 file in seconds."""
    try:
        from mutagen.mp3 import MP3
        audio = MP3(filepath)
        return audio.info.length
    except Exception:
        return None


def format_duration(seconds):
    """Format seconds into MM:SS or HH:MM:SS."""
    if seconds is None:
        return "unknown"
    minutes, secs = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def main():
    # Fix character output on Windows console
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    all_voices = {**VOICES_ZH, **VOICES_EN}

    parser = argparse.ArgumentParser(
        description="Generate podcast audio from a script (Chinese or English)"
    )
    parser.add_argument(
        "input",
        help="Path to the script file (.md or .txt)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output MP3 file path (default: episodes/<script-basename>.mp3)"
    )
    parser.add_argument(
        "-v", "--voice",
        help=f"Edge TTS voice name or shortcut. Chinese: {', '.join(VOICES_ZH.keys())}. English: {', '.join(VOICES_EN.keys())}. Default: auto-detect from script content."
    )
    parser.add_argument(
        "-r", "--rate",
        default="+0%",
        help="Speaking rate adjustment (e.g., '+10%%' for faster, '-10%%' for slower). Default: +0%%"
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available voices and exit"
    )

    args = parser.parse_args()

    # List voices mode
    if args.list_voices:
        print("Available Mandarin Chinese voices:")
        for shortcut, full_name in VOICES_ZH.items():
            print(f"  {shortcut:12s} -> {full_name}")
        print("\nAvailable English voices:")
        for shortcut, full_name in VOICES_EN.items():
            print(f"  {shortcut:12s} -> {full_name}")
        sys.exit(0)

    # Read script
    if not os.path.exists(args.input):
        print(f"Error: Script file not found: {args.input}")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Clean for TTS
    text = clean_script_for_tts(raw_text)

    # Detect language from script content
    lang = detect_language_from_content(text)

    # Resolve voice
    if args.voice:
        voice = all_voices.get(args.voice, args.voice)
    else:
        voice = DEFAULT_VOICE_EN if lang == "en" else DEFAULT_VOICE_ZH

    if not text:
        print("Error: Script is empty after cleaning")
        sys.exit(1)

    char_count = len(text)
    word_count = len(text.split()) if lang == "en" else None
    print(f"Script: {args.input}")
    print(f"Language: {'English' if lang == 'en' else 'Chinese'}")
    if lang == "en":
        print(f"Words: {word_count}")
    else:
        print(f"Characters: {char_count}")
    print(f"Voice: {voice}")
    print(f"Rate: {args.rate}")

    # Determine output path
    if args.output:
        output_file = args.output
    else:
        basename = os.path.splitext(os.path.basename(args.input))[0]
        output_file = os.path.join("episodes", f"{basename}.mp3")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Generate audio
    print(f"Generating audio...")
    asyncio.run(generate_audio(text, output_file, voice, args.rate))

    # Report results
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    duration = get_audio_duration(output_file)

    print(f"\nDone!")
    print(f"Output: {output_file}")
    print(f"Size: {file_size_mb:.1f} MB")
    print(f"Duration: {format_duration(duration)}")


if __name__ == "__main__":
    main()
