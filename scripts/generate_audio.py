#!/usr/bin/env python3
"""
Generate podcast audio from a script using Edge TTS.
Supports both Mandarin Chinese and English with auto-detection from content.
Supports music clip insertion and background music via markers in the script.

Usage:
    python scripts/generate_audio.py episode-scripts/2026-02-24.md
    python scripts/generate_audio.py episode-scripts/2026-02-24.md -v zh-CN-XiaoxiaoNeural
    python scripts/generate_audio.py episode-scripts/2026-02-24.md -o episodes/custom-name.mp3

Music markers (in the episode script):
    [MUSIC: audio/clips/song.mp3]
    [MUSIC: audio/clips/song.mp3 fade_in=2 fade_out=2]
    [MUSIC: audio/clips/song.mp3 start=1:05 end=1:30 fade_in=2 fade_out=2]
    [MUSIC: audio/clips/song.mp3 fade_in=2 fade_out=2 volume=-8]
    [BGM_START: audio/bgm/soft.mp3 volume=-15]
    [BGM_END fade_out=3]

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
import shutil
import tempfile
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

# Regex patterns for music markers
MUSIC_PATTERN = re.compile(
    r'^\[MUSIC:\s*(?P<file>[^\]\s]+)'
    r'(?:\s+start=(?P<start>[^\]\s]+))?'
    r'(?:\s+end=(?P<end>[^\]\s]+))?'
    r'(?:\s+fade_in=(?P<fade_in>[^\]\s]+))?'
    r'(?:\s+fade_out=(?P<fade_out>[^\]\s]+))?'
    r'(?:\s+volume=(?P<volume>[^\]\s]+))?'
    r'\s*\]$',
    re.MULTILINE
)

BGM_START_PATTERN = re.compile(
    r'^\[BGM_START:\s*(?P<file>[^\]\s]+)'
    r'(?:\s+volume=(?P<volume>[^\]\s]+))?'
    r'\s*\]$',
    re.MULTILINE
)

BGM_END_PATTERN = re.compile(
    r'^\[BGM_END'
    r'(?:\s+fade_out=(?P<fade_out>[^\]\s]+))?'
    r'\s*\]$',
    re.MULTILINE
)


def find_ffmpeg():
    """Find ffmpeg executable, checking common Windows install locations."""
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    winget_base = os.path.expanduser(
        r"~\AppData\Local\Microsoft\WinGet\Packages"
    )
    if os.path.isdir(winget_base):
        for folder in os.listdir(winget_base):
            if "FFmpeg" in folder:
                candidate = os.path.join(winget_base, folder)
                for root, dirs, files in os.walk(candidate):
                    if "ffmpeg.exe" in files:
                        return os.path.join(root, "ffmpeg.exe")
    return None


def setup_ffmpeg_env():
    """Add ffmpeg to PATH so pydub can find it."""
    ffmpeg_path = find_ffmpeg()
    if ffmpeg_path:
        ffmpeg_dir = os.path.dirname(ffmpeg_path)
        if ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")


def parse_timestamp(ts):
    """Parse timestamp like '1:05' or '65' into seconds."""
    if ts is None:
        return None
    parts = ts.split(":")
    if len(parts) == 1:
        return float(parts[0])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    raise ValueError(f"Invalid timestamp: {ts}")


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
    text = re.sub(r'^(Date|Voice|Format|Topic|Duration|Sources?|Language|Title|PubDate|Keep|Created):.*$', '', text, flags=re.MULTILINE)
    # Collapse multiple blank lines into one
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def has_music_markers(text):
    """Check if the script contains any music markers."""
    return bool(MUSIC_PATTERN.search(text) or BGM_START_PATTERN.search(text))


def parse_script_segments(text):
    """Parse script into segments of text and music markers.

    Returns a list of dicts, each either:
      {"type": "text", "content": "..."}
      {"type": "music", "file": "...", "start": float, "end": float, "fade_in": float, "fade_out": float}
      {"type": "bgm_start", "file": "...", "volume": float}
      {"type": "bgm_end", "fade_out": float}
    """
    # Combined pattern to split on any marker
    marker_pattern = re.compile(
        r'(\[MUSIC:[^\]]+\]|\[BGM_START:[^\]]+\]|\[BGM_END[^\]]*\])',
        re.MULTILINE
    )

    segments = []
    last_end = 0

    for match in marker_pattern.finditer(text):
        # Text before this marker
        before = text[last_end:match.start()].strip()
        if before:
            segments.append({"type": "text", "content": before})

        marker_text = match.group(0)
        last_end = match.end()

        # Parse the marker
        m = MUSIC_PATTERN.match(marker_text)
        if m:
            segments.append({
                "type": "music",
                "file": m.group("file"),
                "start": parse_timestamp(m.group("start")),
                "end": parse_timestamp(m.group("end")),
                "fade_in": float(m.group("fade_in")) if m.group("fade_in") else 0,
                "fade_out": float(m.group("fade_out")) if m.group("fade_out") else 0,
                "volume": float(m.group("volume")) if m.group("volume") else -6,
            })
            continue

        m = BGM_START_PATTERN.match(marker_text)
        if m:
            segments.append({
                "type": "bgm_start",
                "file": m.group("file"),
                "volume": float(m.group("volume")) if m.group("volume") else -12,
            })
            continue

        m = BGM_END_PATTERN.match(marker_text)
        if m:
            segments.append({
                "type": "bgm_end",
                "fade_out": float(m.group("fade_out")) if m.group("fade_out") else 2,
            })
            continue

    # Remaining text after last marker
    remaining = text[last_end:].strip()
    if remaining:
        segments.append({"type": "text", "content": remaining})

    return segments


def split_text_into_chunks(text, max_chars=2000):
    """Split text into chunks at paragraph boundaries, each under max_chars."""
    paragraphs = text.split('\n\n')
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if current_chunk and len(current_chunk) + len(para) + 2 > max_chars:
            chunks.append(current_chunk.strip())
            current_chunk = para
        else:
            current_chunk = current_chunk + "\n\n" + para if current_chunk else para
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks if chunks else [text]


async def generate_tts_bytes(text, voice, rate="+0%"):
    """Generate MP3 bytes from text using Edge TTS."""
    chunks = split_text_into_chunks(text, max_chars=2000)
    audio_data = b""
    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            print(f"    TTS chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
        communicate = edge_tts.Communicate(chunk, voice, rate=rate)
        chunk_bytes = b""
        async for msg in communicate.stream():
            if msg["type"] == "audio":
                chunk_bytes += msg["data"]
        if not chunk_bytes:
            raise RuntimeError(f"No audio received for chunk {i+1}")
        audio_data += chunk_bytes
    return audio_data


async def generate_audio_simple(text, output_file, voice, rate="+0%"):
    """Generate MP3 from text using Edge TTS (no music markers)."""
    chunks = split_text_into_chunks(text, max_chars=2000)
    if len(chunks) == 1:
        communicate = edge_tts.Communicate(chunks[0], voice, rate=rate)
        await communicate.save(output_file)
    else:
        print(f"  Splitting into {len(chunks)} chunks for TTS...")
        audio_data = b""
        for i, chunk in enumerate(chunks):
            print(f"  Generating chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
            communicate = edge_tts.Communicate(chunk, voice, rate=rate)
            chunk_bytes = b""
            async for msg in communicate.stream():
                if msg["type"] == "audio":
                    chunk_bytes += msg["data"]
            if not chunk_bytes:
                raise RuntimeError(f"No audio received for chunk {i+1}")
            audio_data += chunk_bytes
        with open(output_file, "wb") as f:
            f.write(audio_data)


async def generate_audio_with_music(raw_text, output_file, voice, rate="+0%"):
    """Generate MP3 with interleaved TTS speech and music clips using pydub."""
    try:
        from pydub import AudioSegment
    except ImportError:
        print("Error: pydub is required for music markers. Install with: pip install pydub")
        sys.exit(1)

    def load_audio_file(filepath):
        """Load an audio file, auto-detecting format from extension."""
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".m4a":
            return AudioSegment.from_file(filepath, format="m4a")
        elif ext == ".mp3":
            return AudioSegment.from_mp3(filepath)
        else:
            return AudioSegment.from_file(filepath)

    # Clean text but preserve music markers
    # First extract markers, clean text around them, then re-parse
    cleaned = clean_script_for_tts_preserve_markers(raw_text)
    segments = parse_script_segments(cleaned)

    if not segments:
        print("Error: No content found in script")
        sys.exit(1)

    print(f"  Found {len(segments)} segments: "
          f"{sum(1 for s in segments if s['type'] == 'text')} text, "
          f"{sum(1 for s in segments if s['type'] == 'music')} music clips, "
          f"{sum(1 for s in segments if s['type'] == 'bgm_start')} BGM sections")

    # Build the final audio by processing each segment
    final_audio = AudioSegment.empty()
    bgm_active = None  # Holds BGM AudioSegment when active
    bgm_speech_buffer = AudioSegment.empty()  # Accumulate speech over BGM
    bgm_volume = -12

    with tempfile.TemporaryDirectory() as tmp_dir:
        for i, seg in enumerate(segments):
            if seg["type"] == "text":
                text_clean = clean_script_for_tts(seg["content"])
                if not text_clean.strip():
                    continue
                print(f"  [{i+1}/{len(segments)}] Generating TTS ({len(text_clean)} chars)...")
                tts_bytes = await generate_tts_bytes(text_clean, voice, rate)
                tmp_file = os.path.join(tmp_dir, f"tts_{i}.mp3")
                with open(tmp_file, "wb") as f:
                    f.write(tts_bytes)
                tts_audio = AudioSegment.from_mp3(tmp_file)

                if bgm_active is not None:
                    # Accumulate speech for later BGM overlay
                    bgm_speech_buffer += tts_audio
                else:
                    final_audio += tts_audio

            elif seg["type"] == "music":
                print(f"  [{i+1}/{len(segments)}] Inserting music clip: {seg['file']}")
                if not os.path.exists(seg["file"]):
                    print(f"    Warning: Music file not found: {seg['file']} — skipping")
                    continue
                clip = load_audio_file(seg["file"])

                # Trim if start/end specified
                start_ms = int(seg["start"] * 1000) if seg["start"] is not None else 0
                end_ms = int(seg["end"] * 1000) if seg["end"] is not None else len(clip)
                clip = clip[start_ms:end_ms]

                # Apply volume adjustment (default -6 dB to match TTS loudness)
                clip = clip + seg["volume"]

                # Apply fades
                if seg["fade_in"] > 0:
                    clip = clip.fade_in(int(seg["fade_in"] * 1000))
                if seg["fade_out"] > 0:
                    clip = clip.fade_out(int(seg["fade_out"] * 1000))

                if bgm_active is not None:
                    bgm_speech_buffer += clip
                else:
                    final_audio += clip

            elif seg["type"] == "bgm_start":
                print(f"  [{i+1}/{len(segments)}] Starting background music: {seg['file']}")
                if not os.path.exists(seg["file"]):
                    print(f"    Warning: BGM file not found: {seg['file']} — skipping BGM")
                    continue
                bgm_active = load_audio_file(seg["file"])
                bgm_volume = seg["volume"]
                bgm_speech_buffer = AudioSegment.empty()

            elif seg["type"] == "bgm_end":
                if bgm_active is not None and len(bgm_speech_buffer) > 0:
                    print(f"  [{i+1}/{len(segments)}] Ending background music (overlay {len(bgm_speech_buffer)/1000:.1f}s)")
                    # Loop BGM if needed to cover speech duration
                    speech_len = len(bgm_speech_buffer)
                    bgm_track = bgm_active
                    while len(bgm_track) < speech_len:
                        bgm_track += bgm_active
                    bgm_track = bgm_track[:speech_len]

                    # Adjust BGM volume and apply fade out
                    bgm_track = bgm_track + bgm_volume
                    fade_ms = int(seg["fade_out"] * 1000)
                    if fade_ms > 0:
                        bgm_track = bgm_track.fade_out(fade_ms)

                    # Overlay speech on top of BGM
                    mixed = bgm_track.overlay(bgm_speech_buffer)
                    final_audio += mixed
                else:
                    # No BGM was active or no speech accumulated
                    if len(bgm_speech_buffer) > 0:
                        final_audio += bgm_speech_buffer

                bgm_active = None
                bgm_speech_buffer = AudioSegment.empty()

    # If BGM was never closed, just append remaining speech
    if len(bgm_speech_buffer) > 0:
        if bgm_active is not None:
            speech_len = len(bgm_speech_buffer)
            bgm_track = bgm_active
            while len(bgm_track) < speech_len:
                bgm_track += bgm_active
            bgm_track = bgm_track[:speech_len] + bgm_volume
            bgm_track = bgm_track.fade_out(2000)
            mixed = bgm_track.overlay(bgm_speech_buffer)
            final_audio += mixed
        else:
            final_audio += bgm_speech_buffer

    # Export
    final_audio.export(output_file, format="mp3", bitrate="192k")


def clean_script_for_tts_preserve_markers(text):
    """Clean script but preserve [MUSIC:], [BGM_START:], [BGM_END] markers."""
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Preserve music markers as-is
        if (stripped.startswith('[MUSIC:') or
            stripped.startswith('[BGM_START:') or
            stripped.startswith('[BGM_END')):
            cleaned_lines.append(stripped)
            continue
        cleaned_lines.append(line)

    text = '\n'.join(cleaned_lines)
    # Apply standard cleaning
    text = re.sub(r'^#{1,6}\s+.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'^(Date|Voice|Format|Topic|Duration|Sources?|Language|Title|PubDate|Keep|Created):.*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


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

    # Detect language from script content (from cleaned text without markers)
    text_for_detection = clean_script_for_tts(raw_text)
    lang = detect_language_from_content(text_for_detection)

    # Resolve voice
    if args.voice:
        voice = all_voices.get(args.voice, args.voice)
    else:
        voice = DEFAULT_VOICE_EN if lang == "en" else DEFAULT_VOICE_ZH

    if not text_for_detection:
        print("Error: Script is empty after cleaning")
        sys.exit(1)

    char_count = len(text_for_detection)
    word_count = len(text_for_detection.split()) if lang == "en" else None
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

    # Check for music markers and use appropriate generation path
    uses_music = has_music_markers(raw_text)
    if uses_music:
        setup_ffmpeg_env()
        print(f"Music markers detected — using mixed audio pipeline")
        asyncio.run(generate_audio_with_music(raw_text, output_file, voice, args.rate))
    else:
        text = clean_script_for_tts(raw_text)
        print(f"Generating audio...")
        asyncio.run(generate_audio_simple(text, output_file, voice, args.rate))

    # Report results
    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    duration = get_audio_duration(output_file)

    print(f"\nDone!")
    print(f"Output: {output_file}")
    print(f"Size: {file_size_mb:.1f} MB")
    print(f"Duration: {format_duration(duration)}")


if __name__ == "__main__":
    main()
