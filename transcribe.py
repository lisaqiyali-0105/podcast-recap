#!/usr/bin/env python3
"""
transcribe.py — Local podcast transcription using faster-whisper.

Usage:
  python3 transcribe.py --mp3 /path/to/file.mp3
  python3 transcribe.py --url https://example.com/episode.mp3
  python3 transcribe.py --youtube https://youtube.com/watch?v=...
  python3 transcribe.py --rss https://feeds.example.com/podcast.rss --guid abc123

Output: transcript text to stdout + saves to ~/Downloads/transcripts/<title>.txt
"""

import sys
import os
import argparse
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

# Label overrides for common roles — any other string works too, gets auto-labeled
PERSONA_LABELS = {
    'pm':         ('The PM Translation',       'In Practice'),
    'engineer':   ('The Engineering Takeaway', 'This Sprint'),
    'designer':   ('The Design Angle',         'Try This'),
    'gtm':        ('The GTM Read',             'This Quarter'),
    'founder':    ('The Founder Lens',         'This Week'),
    'ceo':        ('The CEO Lens',             'This Week'),
    'cto':        ('The CTO Lens',             'This Sprint'),
    'marketing':  ('The Marketing Angle',      'This Campaign'),
    'sales':      ('The Sales Angle',          'This Week'),
    'investor':   ('The Investor Read',        'Due Diligence Note'),
}


def _persona_prompt(persona: str, title: str, notes: str = '', context: str = '') -> str:
    """Return the analysis instruction block printed after the transcript."""
    key = persona.lower().strip()
    bridge_label, practice_label = PERSONA_LABELS.get(
        key, (f'The {persona.title()} Lens', 'Try This')
    )

    notes_block = ''
    if notes.strip():
        notes_block = f"""
Immediate reactions from the listener (captured right after listening):
  "{notes.strip()}"

These are their short-term memory — the things that hit hardest in the moment.
Factor them into the analysis: connect themes back to what they flagged, and help
convert these fleeting reactions into long-term, applicable knowledge.
"""

    context_block = ''
    if context.strip():
        context_block = f"""
Listener context: {context.strip()}
Apply this when generating insights — make the analysis specific to their actual
situation, not a generic {persona}.
"""

    return f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PODCAST-RECAP ANALYSIS REQUEST
Persona: {persona}
Content: {title}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{notes_block}{context_block}
Using the transcript above, identify 5–7 key themes through the lens of a {persona}.

Think deeply about what someone in this role actually cares about — their daily pressures,
the decisions they own, the metrics they're held to, and what "useful" means to them
specifically. Don't apply a generic lens; apply the real one.

For each theme:
1. Extract 1–2 verbatim quotes that best capture the idea (exact words from the transcript)
2. Write "{bridge_label}": how this insight lands for a {persona} — be specific to that role
3. Write "{practice_label}": one concrete action this person can take, grounded in their actual context

Output format (repeat for each theme):
  ## [Theme Title]
  > [verbatim quote]
  **{bridge_label}:** [2–3 sentences, specific to a {persona}]
  **{practice_label}:** [1 concrete, actionable next step]

After all themes, close with:
  ## The Single Question
  The one question from this content that a {persona} should carry with them.
"""


def fetch_rss_audio_url(rss_url, guid):
    """Parse RSS feed, find episode by GUID, return the .mp3 enclosure URL."""
    print(f"Fetching RSS feed: {rss_url}", file=sys.stderr)
    req = urllib.request.Request(rss_url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    with urllib.request.urlopen(req, timeout=30) as res:
        xml_data = res.read()

    root = ET.fromstring(xml_data)
    ns = {'itunes': 'http://www.itunes.com/dtds/podcast-1.0.dtd'}

    for item in root.iter('item'):
        item_guid = item.findtext('guid', '').strip()
        if item_guid == guid.strip():
            title = item.findtext('title', 'episode').strip()
            enclosure = item.find('enclosure')
            if enclosure is not None:
                audio_url = enclosure.get('url', '')
                print(f"Found episode: {title}", file=sys.stderr)
                print(f"Audio URL: {audio_url}", file=sys.stderr)
                return audio_url, title
            break

    raise ValueError(f"Could not find episode with GUID: {guid}")

def download_audio(url, dest_path):
    """Download audio file from a direct URL."""
    print(f"Downloading audio...", file=sys.stderr)
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })
    with urllib.request.urlopen(req, timeout=60) as res, open(dest_path, 'wb') as f:
        total = int(res.headers.get('Content-Length', 0))
        downloaded = 0
        while chunk := res.read(1024 * 64):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                print(f"\r  {pct:.0f}% ({downloaded // 1024 // 1024}MB / {total // 1024 // 1024}MB)", end='', file=sys.stderr)
    print(file=sys.stderr)

def download_youtube(url, dest_dir):
    """Use yt-dlp to download audio from a YouTube URL."""
    import subprocess
    print(f"Downloading YouTube audio via yt-dlp...", file=sys.stderr)

    # Step 1: fetch title only (--skip-download avoids triggering simulation mode
    # that --print alone causes, which would skip the actual download below).
    title_result = subprocess.run([
        'yt-dlp', '--skip-download', '--print', 'title', url
    ], capture_output=True, text=True)
    title = title_result.stdout.strip().split('\n')[0] if title_result.returncode == 0 else 'episode'

    # Step 2: download audio with a fixed output name to avoid filename
    # sanitization mismatches between raw metadata and filesystem-safe names.
    dl_result = subprocess.run([
        'yt-dlp', '-x', '--audio-format', 'mp3',
        '--audio-quality', '0',
        '-o', str(Path(dest_dir) / 'audio.%(ext)s'),
        url
    ], capture_output=True, text=True)

    if dl_result.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {dl_result.stderr}")

    mp3_path = Path(dest_dir) / 'audio.mp3'
    return str(mp3_path), title

def transcribe(audio_path, model_size='small'):
    """Transcribe audio using mlx-whisper (Apple Silicon GPU) if available,
    falling back to faster-whisper (CPU). Same accuracy either way — mlx is
    just much faster on M-series Macs (~7-10x speedup)."""

    # ── mlx-whisper (Apple Silicon) ──────────────────────────────
    try:
        import mlx_whisper
        repo = f"mlx-community/whisper-{model_size}-mlx"
        print(f"Transcribing with mlx-whisper ({model_size})...", file=sys.stderr)
        result = mlx_whisper.transcribe(audio_path, path_or_hf_repo=repo)

        language = result.get("language", "unknown")
        segments = result.get("segments", [])
        duration = segments[-1]["end"] if segments else 0
        transcript = '\n'.join(s["text"].strip() for s in segments) or result.get("text", "").strip()

        print(f"Language: {language}", file=sys.stderr)
        print(f"Duration: {duration / 60:.1f} minutes", file=sys.stderr)

        class _Info:
            pass
        info = _Info()
        info.language = language
        info.language_probability = 1.0
        info.duration = duration
        return transcript, info

    except ImportError:
        print(f"mlx-whisper not found — falling back to faster-whisper (CPU).", file=sys.stderr)

    # ── faster-whisper fallback (CPU) ─────────────────────────────
    from faster_whisper import WhisperModel
    print(f"Loading Whisper model ({model_size})...", file=sys.stderr)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"Transcribing {Path(audio_path).name}...", file=sys.stderr)
    segments, info = model.transcribe(audio_path)

    print(f"Language: {info.language} ({info.language_probability:.0%} confidence)", file=sys.stderr)
    print(f"Duration: {info.duration / 60:.1f} minutes", file=sys.stderr)

    lines = [s.text.strip() for s in segments]
    return '\n'.join(lines), info

def save_transcript(text, title, output_dir=None):
    """Save transcript to ~/Downloads/transcripts/<title>.txt"""
    if output_dir is None:
        output_dir = Path.home() / 'Downloads' / 'transcripts'
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize title for filename
    safe_title = ''.join(c if c.isalnum() or c in ' -_' else '_' for c in title)
    safe_title = safe_title.strip() or 'transcript'
    out_path = output_dir / f"{safe_title}.txt"
    out_path.write_text(text)
    return str(out_path)

def main():
    parser = argparse.ArgumentParser(description='Transcribe a podcast episode locally using Whisper.')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--mp3', help='Path to a local .mp3 file')
    group.add_argument('--url', help='Direct URL to an audio file (.mp3, .m4a, etc.)')
    group.add_argument('--youtube', help='YouTube video URL')
    group.add_argument('--rss', help='RSS feed URL (use with --guid)')

    parser.add_argument('--guid', help='Episode GUID (required with --rss)')
    parser.add_argument('--model', default='small', choices=['tiny', 'base', 'small', 'medium'],
                        help='Whisper model size (default: small). Claude selects automatically based on content type.')
    parser.add_argument('--output', help='Output directory for transcript file')
    parser.add_argument('--persona', default='pm', metavar='ROLE',
                        help='Your role/perspective for the analysis (default: pm). '
                             'Any role works: pm, engineer, designer, gtm, founder, ceo, '
                             'investor, "chief of staff", "sales rep", etc.')
    parser.add_argument('--notes', default='', metavar='TEXT',
                        help='Your immediate reactions after listening — dictated or typed. '
                             'Gets woven into the analysis to anchor it in your actual experience.')
    parser.add_argument('--context', default='', metavar='TEXT',
                        help='Your specific situation, e.g. "PM at enterprise SaaS focused on search". '
                             'Makes the analysis specific to you, not just your role type.')

    args = parser.parse_args()

    title = 'transcript'
    audio_path = None
    tmp_dir = tempfile.mkdtemp()

    try:
        if args.mp3:
            audio_path = args.mp3
            title = Path(args.mp3).stem

        elif args.url:
            audio_path = os.path.join(tmp_dir, 'audio.mp3')
            download_audio(args.url, audio_path)
            title = 'episode'

        elif args.youtube:
            audio_path, title = download_youtube(args.youtube, tmp_dir)

        elif args.rss:
            if not args.guid:
                print("Error: --guid is required when using --rss", file=sys.stderr)
                sys.exit(1)
            audio_url, title = fetch_rss_audio_url(args.rss, args.guid)
            audio_path = os.path.join(tmp_dir, 'audio.mp3')
            download_audio(audio_url, audio_path)

        # Transcribe
        transcript, info = transcribe(audio_path, model_size=args.model)

        # Save
        out_path = save_transcript(transcript, title, args.output)
        print(f"\nTranscript saved to: {out_path}", file=sys.stderr)
        print(f"Word count: ~{len(transcript.split()):,}", file=sys.stderr)

        # Print transcript to stdout (so Claude can read it)
        print(transcript)

        # Append persona analysis prompt
        print(_persona_prompt(args.persona, title, args.notes, args.context))

    finally:
        # Clean up temp files
        import shutil
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)

if __name__ == '__main__':
    main()
