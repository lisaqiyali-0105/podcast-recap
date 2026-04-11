---
name: podcast-recap
description: Transcribe any podcast episode or YouTube video locally using Whisper — no API key, no cost. Accepts YouTube URLs, RSS feed + episode GUID, direct audio URLs, or local mp3 files. Generates role-specific HTML notes with pull quotes, PM/role translation, and a Quill reflections editor.
---

# Podcast Recap

Transcribe any audio locally using mlx-whisper (Apple Silicon GPU) or faster-whisper (CPU fallback), then generate a role-specific HTML note. Free, private, no API key needed.

## Trigger phrases
- "transcribe [YouTube URL]"
- "transcribe this podcast: [RSS URL] [GUID]"
- "transcribe [direct .mp3 URL]"
- "transcribe [local file path]"
- "get me a transcript of [anything]"
- "recap this podcast as an engineer / designer / GTM"
- "[Podcast name], [episode description]" — no URL needed, Claude finds it

## Step 0: Ask two questions before running the script (BOTH MANDATORY)

Before running `transcribe.py`, always ask **both** of these. Never assume either.

### Question 1 — Persona (MANDATORY — always ask, never default)

Ask the persona question with context about the episode woven in. Use the episode title, guest, or topic to make the example concrete and relevant:

> "What's your role or perspective for this recap? For example: PM, founder, engineer, investor — or describe your job.
>
> The podcast might not be in your industry — that's fine. The goal is to find the patterns and parallels that apply to *your* decisions. [A Tony Xu story about last-mile logistics hits differently for a PM than for a founder or an investor.] Pick the perspective that matches the kinds of decisions you make day-to-day."

Replace the bracketed example with a sentence that references the actual episode — guest name, topic, or key idea — so it feels specific, not generic.

Wait for the answer. Use it as the `--persona` value.

**Never assume `pm` or any default.** Even if the user is a PM, they may want a founder or investor perspective on a given episode. Always ask.

**Exception:** If the user already specified a perspective in the trigger message (e.g., "recap this as a founder"), extract that and skip the question.

### Question 2 — Immediate reactions (MANDATORY — ask after persona)

> "Before I generate anything — what's your immediate reaction from listening? What landed? Even one sentence is enough."

Wait for the answer. Use it as the `--notes` value.

**Why this matters:** This step activates your short-term memory before it fades, and anchors the analysis to *your* experience of the episode — not a generic reading of it. Skipping it produces a generic recap. Doing it produces one that's specific to what you actually got out of listening.

**Exception:** If the user already included their reactions in the trigger message, extract that as `--notes` and skip the question. If the user says "just transcribe, no notes" or "skip the reflection prompt", proceed without `--notes`.

### Ask both in one message

To avoid unnecessary back-and-forth, ask both questions together in a single message. Make the persona question specific to the episode:

> "Two quick things before I run this:
> 1. What's your role or perspective for this recap? (PM, founder, engineer, investor — or describe your job.) The podcast might not be in your industry — that's fine. The goal is to find the patterns and parallels that apply to *your* decisions. [A Tony Xu story about earning customer trust hits differently for a PM than for a founder or an investor.] Pick the perspective that matches the kinds of decisions you make day-to-day.
> 2. What's your immediate reaction from listening — what landed for you? Even one sentence."

Replace the bracketed sentence with a reference to the actual episode — guest, topic, or a key idea from it.

Wait for both answers before running the script.

## Script location
`~/.claude/skills/podcast-recap/transcribe.py`

> **Note for new installs:** After cloning the repo, copy `transcribe.py` to this path. See the README for install instructions.

## If the user doesn't have a URL

When the user describes an episode without providing a URL, find it first:

1. **Search YouTube:** `[Podcast Name] [Episode Title/Guest] full episode`
   - If found → use `--youtube` with that URL
   - Lenny's, My First Million, Invest Like the Best, and most major podcasts post full episodes to YouTube

2. **If not on YouTube:** Search for `[Podcast Name] RSS feed`
   - Find the RSS URL + the episode GUID (shown in podcast apps or the feed XML)
   - Use `--rss [RSS_URL] --guid [GUID]`

3. **Set expectations on time:** Always tell the user how long transcription will take before starting.
   - Times below assume mlx-whisper (Apple Silicon). CPU fallback is ~7–10× slower.
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

## How to run

### YouTube URL
```bash
python3 ~/.claude/skills/podcast-recap/transcribe.py \
  --youtube "https://youtube.com/watch?v=..."
```

### YouTube URL with persona lens + immediate reactions
```bash
python3 ~/.claude/skills/podcast-recap/transcribe.py \
  --youtube "https://youtube.com/watch?v=..." \
  --persona pm \
  --notes "The 98% overhead stat blew my mind. Want to apply the idiot index to our roadmap."
```

### With full personal context
```bash
python3 ~/.claude/skills/podcast-recap/transcribe.py \
  --youtube "https://youtube.com/watch?v=..." \
  --persona pm \
  --context "PM at enterprise SaaS, working on AI search features for financial analysts" \
  --notes "Really resonated with the constraint-focus idea"
```

### RSS feed + GUID
```bash
python3 ~/.claude/skills/podcast-recap/transcribe.py \
  --rss "https://feeds.example.com/podcast.rss" \
  --guid "episode-guid-here" \
  --persona gtm
```

### Direct audio URL
```bash
python3 ~/.claude/skills/podcast-recap/transcribe.py \
  --url "https://example.com/episode.mp3"
```

### Local file
```bash
python3 ~/.claude/skills/podcast-recap/transcribe.py \
  --mp3 "/path/to/file.mp3" \
  --persona designer
```

## All flags

| Flag | Default | Description |
|---|---|---|
| `--youtube` | — | YouTube video URL |
| `--url` | — | Direct audio file URL |
| `--mp3` | — | Path to local .mp3 file |
| `--rss` | — | RSS feed URL (requires `--guid`) |
| `--guid` | — | Episode GUID (required with `--rss`) |
| `--persona` | `pm` | Role lens for analysis (any free-text role) |
| `--notes` | `""` | Immediate reactions after listening — woven into the analysis |
| `--context` | `""` | Your specific situation — makes analysis specific to you, not just your role |
| `--model` | `small` | Whisper model: `tiny`, `base`, `small`, `medium` |
| `--output` | `~/Downloads/transcripts/` | Output directory for transcript file |
| `--no-gemma` | off | Skip the Gemma first-pass step even if Ollama is running |

Note: `--youtube`, `--url`, `--mp3`, `--rss` are mutually exclusive. One is required.

## 3-Model Pipeline (automatic when Ollama is running)

After transcription, the script automatically checks for a local Gemma model and runs a first-pass angle extraction before Claude's deep analysis. This is **opt-in by having Ollama running** — no setup required, no failure if it's not installed.

**How it works:**
1. **Whisper** (mlx or faster-whisper) → accurate transcript
2. **Gemma 4 / Gemma 3** (local via Ollama, optional) → fast first-pass: 5 raw angles through the listener's lens. Intentionally lean — divergent, not polished.
3. **Claude** → deep analysis + synthesis. Reads both the transcript AND Gemma's angles. Incorporates the best of both; discards weak ones. Final output is stronger than either model alone.

**What the user sees in stderr:**
```
Checking for Gemma (local first-pass)...
  Found gemma3:12b — running first-pass angle extraction...
  First-pass complete — Claude will synthesize both.
```

Or if Ollama isn't running:
```
Checking for Gemma (local first-pass)...
  Gemma not available (Ollama not running — start it with: ollama serve)
  Continuing with Claude-only recap.
```

**To skip Gemma even when Ollama is running:** pass `--no-gemma`.

## Persona Lenses (--persona flag)

The `--persona` flag is **open-ended** — pass any role, title, or description. Common roles get custom labels:

| Persona | Bridge label | Action label |
|---|---|---|
| `pm` | The PM Translation | In Practice |
| `engineer` | The Engineering Takeaway | This Sprint |
| `designer` | The Design Angle | Try This |
| `founder` | The Founder Lens | This Week |
| `ceo` | The CEO Lens | This Week |
| `investor` | The Investor Read | Due Diligence Note |
| `gtm` | The GTM Read | This Quarter |
| Any other | The [Role] Lens | Try This |

## What it does
1. Detects input type (YouTube / RSS+GUID / URL / local file)
2. For YouTube: uses yt-dlp to download audio as mp3
3. For RSS+GUID: fetches the RSS feed, finds episode by GUID, downloads the mp3 from `<enclosure>`
4. For direct URLs: downloads the audio file
5. Tries **mlx-whisper** (Apple Silicon GPU) first — ~7–10× faster than CPU. Falls back to **faster-whisper** (CPU) if mlx-whisper isn't installed
6. Saves transcript to `~/Downloads/transcripts/<title>.txt`
7. **Optional:** checks for Gemma via Ollama — if available, runs a fast first-pass angle extraction (5 raw angles, role-specific). Gracefully skipped if Ollama isn't running.
8. Prints transcript to stdout
9. Appends persona analysis request block — includes Gemma's angles when available, telling Claude to synthesize both. Claude-only recap if Gemma is unavailable.

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

Then read the full stdout (transcript + analysis block) and generate the role-specific recap. Ask: "Want me to turn this into an HTML note?"

## Generating the HTML note

After generating the recap, offer to build an editorial HTML page. The reference design is at `~/Claude/podcast-recap/library/notes/2026-04-09-spacex-pm-playbook.html`.

**Design spec:**
- **Layout:** Single-scroll page, no pagination
- **Header:** Sticky, with reading progress bar (2px line at bottom), nav links to each lesson
- **Accent color:** Terracotta (`#B5451B`) on warm parchment (`#F7F3EC`)
- **Pull quotes:** Left border (4px solid terracotta), light tinted background — no dark color blocks
- **Each lesson has:**
  - Large faded lesson number
  - Lesson label (e.g., "On Cost") + title
  - Pull quote from source
  - Role bridge section (label varies by persona, e.g., "The PM Translation")
  - In-practice callout (light terracotta tint, lightning bolt icon)
- **Alternating backgrounds:** Even-numbered lessons use `#EFE8DC`
- **Closing section:** "The Single Question" with the essay's closing argument
- **Reflections:** Quill v2 rich-text editor, localStorage auto-save (date-keyed), prompt chip buttons

The HTML structure is persona-agnostic — only the bridge labels and framing change per role.

## Auto-saving to the library (MANDATORY)

Every time an HTML note is generated, Claude must:

1. **Save the HTML** to `~/Claude/podcast-recap/library/notes/YYYY-MM-DD-[slug].html`
   - Slug = lowercase title, spaces → hyphens, special chars stripped
   - Example: `2026-04-10-spacex-pm-playbook.html`

2. **Update `~/Claude/podcast-recap/library/manifest.json`** — append one entry:
   ```json
   {
     "id": "YYYY-MM-DD-[slug]",
     "title": "[The playbook title from the hero h1]",
     "source": "[Podcast/essay name — shown in hero-source-text]",
     "persona": "[persona passed to --persona flag]",
     "date": "YYYY-MM-DD",
     "emoji": "[pick one relevant emoji]",
     "lessonCount": [number of lesson sections],
     "filename": "notes/YYYY-MM-DD-[slug].html"
   }
   ```

3. **Commit and push both files** to GitHub:
   ```bash
   git -C ~/Claude/podcast-recap add library/notes/YYYY-MM-DD-[slug].html library/manifest.json
   git -C ~/Claude/podcast-recap commit -m "Add note: [title]"
   git -C ~/Claude/podcast-recap push origin main
   ```

This keeps the library at `https://lisaqiyali-0105.github.io/podcast-recap/library/` up to date automatically.

**Emoji guide by persona:**
| Persona | Emoji |
|---|---|
| pm | 🚀 |
| engineer / cto | ⚙️ |
| designer | 🎨 |
| founder / ceo | 💡 |
| investor | 📊 |
| manager | 🏗️ |
| gtm / sales | 📣 |
| marketing | 🎯 |
| any other | 📖 |

## Dependencies
- `mlx-whisper` (pip) — preferred on Apple Silicon (M1/M2/M3/M4)
- `faster-whisper` (pip) — CPU fallback, works on any machine
- `yt-dlp` (brew) — only needed for YouTube URLs
- No API keys required

Install:
```bash
pip3 install mlx-whisper        # Apple Silicon (fast)
pip3 install faster-whisper     # CPU fallback
brew install yt-dlp             # YouTube support
```

## Using as a pod2txt replacement in follow-builders
```bash
python3 ~/.claude/skills/podcast-recap/transcribe.py \
  --rss "[podcast.rssUrl]" \
  --guid "[episode.guid]"
```
The transcript is printed to stdout — same interface as pod2txt.
