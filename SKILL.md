---
name: podcast-recap
description: Transcribe any podcast episode or YouTube video locally using Whisper — no API key, no cost. Accepts YouTube URLs, RSS feed + episode GUID, direct audio URLs, or local mp3 files. Supports role-specific analysis lenses (PM, Engineer, Designer, GTM) to generate perspective-tailored recaps. Drop-in replacement for pod2txt in follow-builders.
---

# Podcast Recap

Transcribe any audio locally using faster-whisper, then generate a role-specific analysis. Free, private, no API key needed.

## Trigger phrases
- "transcribe [YouTube URL]"
- "transcribe this podcast: [RSS URL] [GUID]"
- "transcribe [direct .mp3 URL]"
- "transcribe [local file path]"
- "get me a transcript of [anything]"
- "recap this podcast as an engineer / designer / GTM"
- "[Podcast name], [episode description]" — no URL needed, Claude finds it

## If the user doesn't have a URL

When the user describes an episode without providing a URL, find it first:

1. **Search YouTube:** `[Podcast Name] [Episode Title/Guest] full episode`
   - If found → use `--youtube` with that URL
   - Lenny's, My First Million, Invest Like the Best, and most major podcasts post full episodes to YouTube

2. **If not on YouTube:** Search for `[Podcast Name] RSS feed`
   - Find the RSS URL + the episode GUID (shown in podcast apps or the feed XML)
   - Use `--rss [RSS_URL] --guid [GUID]`

3. **Set expectations on time:** Always tell the user how long transcription will take before starting.
   - Times below assume mlx-whisper (Apple Silicon). CPU (faster-whisper fallback) is ~7–10× slower.
   - `small` model: 30 min → ~1 min | 1 hour → ~2 min | 2 hours → ~4 min
   - `tiny` model: ~2× faster than small; use only if user explicitly wants speed over accuracy

## Dynamic model selection

**Do not always use the default.** Choose the model based on what the user is trying to get out of the episode:

| Signal | Model | Reason |
|---|---|---|
| Casual interview, narrative storytelling | `base` | Conversational speech; `base` is accurate enough and fast |
| Technical content (finance, engineering, AI, medicine) | `small` | Jargon-heavy; `small` handles domain vocab better |
| Academic lecture, dense research discussion | `medium` | Maximum accuracy for complex terminology |
| User explicitly wants it fast ("quick take") | `tiny` | Speed over precision |
| User says accuracy matters ("I need the exact quotes") | `small` or `medium` | Don't compromise |

**Default when unsure:** `small`. It's fast enough on MLX and accurate enough for almost everything.

## Script location
`~/.claude/skills/transcribe-podcast/transcribe.py`

> **Note for new installs:** This path is specific to the original author's machine. After cloning the repo, update this path to wherever you placed `transcribe.py`. See the README for install instructions.

## How to run

### YouTube URL
```bash
python3 ~/.claude/skills/transcribe-podcast/transcribe.py \
  --youtube "https://youtube.com/watch?v=..."
```

### YouTube URL with persona lens
```bash
python3 ~/.claude/skills/transcribe-podcast/transcribe.py \
  --youtube "https://youtube.com/watch?v=..." \
  --persona engineer
```

### RSS feed + GUID (follow-builders / pod2txt replacement)
```bash
python3 ~/.claude/skills/transcribe-podcast/transcribe.py \
  --rss "https://feeds.example.com/podcast.rss" \
  --guid "episode-guid-here" \
  --persona gtm
```

### Direct audio URL
```bash
python3 ~/.claude/skills/transcribe-podcast/transcribe.py \
  --url "https://example.com/episode.mp3"
```

### Local file
```bash
python3 ~/.claude/skills/transcribe-podcast/transcribe.py \
  --mp3 "/path/to/file.mp3" \
  --persona designer
```

### Model sizes (optional --model flag)
- `tiny` — fastest, good accuracy
- `base` — fast, better accuracy (default)
- `small` — slower, great accuracy
- `medium` — slow, excellent accuracy

## Persona Lenses (--persona flag)

The `--persona` flag is **open-ended** — pass any role, title, or description. The script doesn't limit you to a preset list. Claude infers what that role cares about and applies the right lens.

```bash
--persona founder
--persona "chief of staff"
--persona investor
--persona "sales rep"
--persona "head of partnerships"
--persona "engineering manager"
--persona "early-stage startup ceo"
```

**How it works:** After transcription, the script appends a structured analysis instruction to stdout. Claude reads the full transcript + the instruction in one pass and generates a role-specific recap — no second call needed.

The analysis prompt tells Claude: think about what this role actually cares about — their daily pressures, the decisions they own, the metrics they're held to — and apply that lens authentically. Not a generic filter.

**Label customization:** Common roles get thoughtful bridge/action labels (e.g., `pm` → "The PM Translation / In Practice", `founder` → "The Founder Lens / This Week"). Any other role gets auto-labeled from the persona string.

---

## What it does
1. Detects input type (YouTube / RSS+GUID / URL / local file)
2. For YouTube: uses yt-dlp to download audio as mp3
3. For RSS+GUID: fetches the RSS feed, finds the episode by GUID, downloads the .mp3 from the `<enclosure>` tag
4. For direct URLs: downloads the audio file
5. Runs faster-whisper locally (no data sent anywhere)
6. Saves transcript to `~/Downloads/transcripts/<title>.txt`
7. Prints transcript to stdout
8. Appends persona analysis request block — Claude reads both and generates the recap

## Output
- Transcript saved to: `~/Downloads/transcripts/<title>.txt`
- Full text + analysis request printed to stdout
- Language + duration + word count logged to stderr

## After transcribing
Always confirm the file was saved and show the user:
- Where it was saved
- Duration of the audio
- Word count
- First 3–4 sentences of the transcript so they can verify accuracy

Then read the full stdout (transcript + analysis block) and generate the role-specific recap. Ask: "Want me to turn this into an HTML playbook?"

## Generating the HTML playbook
After generating the recap, offer to build an editorial HTML page using the same format as the SpaceX PM Playbook (`~/Documents/spacex-pm-playbook.html`):
- Pull quotes with dark bands
- Role-specific bridge section (label varies by persona)
- In-practice callout (amber)
- Left sidebar navigation
- Paginated lesson view
- Quill reflections section

The HTML output is persona-agnostic in structure — only the bridge labels and framing change.

## Using as a pod2txt replacement in follow-builders
To replace the pod2txt call in `generate-feed.js`, the equivalent is:
```bash
python3 ~/.claude/skills/transcribe-podcast/transcribe.py \
  --rss "[podcast.rssUrl]" \
  --guid "[episode.guid]"
```
The transcript is printed to stdout — same interface as pod2txt's ready response.

## Dependencies
- `faster-whisper` (pip) — already installed
- `yt-dlp` (brew) — already installed, only needed for YouTube URLs
- No API keys required
