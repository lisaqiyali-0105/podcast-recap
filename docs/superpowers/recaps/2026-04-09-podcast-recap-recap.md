## Build Journal — podcast-recap — 2026-04-09

### What We Built

A local podcast transcription tool (`transcribe.py`) that generates role-specific HTML playbooks from any podcast or essay — using mlx-whisper (Apple Silicon GPU) with a faster-whisper CPU fallback, no API keys required. The example output is a fully designed single-scroll HTML page: the SpaceX PM Playbook, analyzed through the lens of a product manager.

---

### Key Decisions & Why

**Single-scroll layout over paginated**
Started with a paginated layout (prev/next buttons, one lesson per "screen"). Switched to single-scroll with a sticky header mid-build because it felt more like reading a real article and less like navigating a slide deck. The sticky nav with IntersectionObserver-based active state tracking gives the same orientation cues without forcing page changes.

**Terracotta accent (#B5451B) over amber or blue**
Amber was the default Lisa design system color, but the SpaceX content called for something more editorial and distinctive. Baby blue was tried and immediately rejected — the temperature clash between cool blue and the warm parchment background (`#F7F3EC`) made it jarring. Created a `color-options.html` 2×2 grid mockup showing Forest Green, Terracotta, Deep Sage, and Burgundy at full fidelity before asking for a pick. Terracotta won — warm-on-warm, energetic without being aggressive.

**Eyebrow "Podcast Recap · For Product Managers" over "7 Lessons for Product Managers"**
The first hero draft didn't make clear this was a podcast recap — it read like original content. Changing the eyebrow to signal the source format fixed the framing. This also removed the redundancy with the h1 ("7 lessons...") leading the eyebrow.

**Hero title "7 lessons SpaceX taught me about product." over "SpaceX accidentally wrote a PM playbook"**
The first title was too clever — it lost the personal learning frame and felt like a marketing line. The final title keeps the number, names the source, and signals it's personal takeaways.

**Progress bar instead of pagination indicator**
User specifically requested a horizontal reading progress bar after the CTA button was removed from the hero. Added as a 2px bar at the bottom of the fixed header — updates on scroll via a passive event listener. This replaced the "what page am I on" signal that the paginated layout provided.

**Visual color mockup before asking for a choice**
Any time multiple design options were in play, built a live HTML file showing all options side-by-side rather than describing them in text. This was especially useful for the color decision — four warm-compatible options at real fidelity vs. four hex values in prose.

---

### Tradeoffs Considered

**Paginated vs. single-scroll:** Paginated felt more "app-like" and controlled — one idea at a time. Chose single-scroll because the content reads better as a continuous piece, and the sticky nav handles orientation. If the lessons were longer or more interactive, paginated would be worth revisiting.

**Dark pull-quote blocks vs. editorial left-border style:** The original design used dark terracotta backgrounds for pull quotes (similar to the "dark color blocks" pattern). Removed them after user feedback — the warm parchment + light quote background reads more like an editorial magazine, which fits the content better than a card-heavy layout.

**localStorage vs. no persistence for reflections:** Could have skipped saving entirely for simplicity. Chose localStorage with a date-keyed key so reflections persist per-day without any backend. Tradeoff: if you come back two days later, the editor is empty (by design — the key resets daily). Long-term, this should move to IndexedDB or a proper sync system.

**mlx-whisper as primary vs. faster-whisper:** mlx-whisper is 7–10× faster on Apple Silicon but requires a separate install. Made it the primary with a clean ImportError fallback to faster-whisper. No user configuration needed — the script detects what's available.

---

### Problems Encountered & How They Were Fixed

**Baby blue clashing with warm background**
Baby blue (#60A5FA or similar) was tried as the accent color at user request. Immediately looked wrong — the cool/warm temperature mismatch made the page feel disconnected. Root cause: blue is a cool color; the parchment palette is warm. Fix: built `mockups/color-options.html` with four warm-compatible alternatives and let user pick. Terracotta chosen.

**Touch target FAIL in mobile check**
Header nav `<a>` tags were rendering at ~22px tall — well below the 44px minimum. Root cause: the links had padding but no explicit height, and the flex container wasn't stretching them. Fix: added `min-height: 44px; display: inline-flex; align-items: center` to `.header-nav a`. Prompt chips also got `min-height: 44px` for the same reason.

**Voice-dna check skipped initially**
Voice-dna was not run before presenting the first draft of the playbook content. User caught it. Fix: ran the skill, loaded `ai-dead-language.md`, found and fixed 9 violations — 8 em dashes used as prose punctuation (banned) and 2 contrast framing instances ("isn't X — it's Y" pattern). Rule for next time: run voice-dna before presenting any written content, not after.

**Hero title too clever**
"SpaceX accidentally wrote a PM playbook" was the first title. Feedback: too far from the personal learning frame, reads like marketing copy. Fixed by going back to the simpler, more direct form: "7 lessons SpaceX taught me about product." Second iteration was immediately approved.

**No formal spec file**
This project didn't go through Stage 1 brainstorming, so there was no spec to reference during QA. Used `README.md` as a substitute. For future builds, even a lightweight spec saves time during QA test case generation.

---

### What Worked Well

**IntersectionObserver for active nav** — cleaner than scroll position calculations, handles edge cases (section at bottom of page, etc.) without extra logic. The `rootMargin: '-20% 0px -70% 0px'` sweet spot prevents flickering at section boundaries.

**Playwright screenshots via `take-screenshots.js`** — generating README screenshots programmatically took ~5 minutes total (including install) and produced pixel-perfect results. Reusable pattern: capture by element position, not fixed coordinates, so it adapts if the layout changes.

**Color options mockup approach** — showing 4 options at full fidelity in a 2×2 grid before asking for a pick produced a faster, more confident decision than describing options in text ever would. This is the right pattern for any visual decision with 3+ options.

**Terracotta palette cohesion** — the warm-on-warm combination (`#F7F3EC` background, `#B5451B` accent, `#FAE2D9` light tint) held up across all components: pull quotes, in-practice blocks, nav active states, progress bar. No secondary accent needed.

**Quill v2 reflection editor** — the rich text editor with localStorage auto-save, date display, and prompt chips came together cleanly. The debounced save with "saving… / saved" status feedback felt polished without extra complexity.

---

### What To Do Differently Next Time

**Run voice-dna before presenting written content** — not after. Catching 9 violations post-presentation added an unnecessary round-trip. Make it a mandatory step before any written output is shown.

**Lock the color palette before building** — the baby blue detour cost a full iteration cycle. For any project using a warm background, establish the accent color and palette before writing a single line of CSS. The color-options.html mockup approach is the right pattern, but it should happen before the main build, not mid-build.

**Create a formal spec even for quick projects** — the lack of a Stage 1 spec meant using README.md as a QA reference, which is a workaround. Even a 1-page spec with features + scope saves time during QA and critique stages.

**Add `.gitignore` before `git init`** — `node_modules/` was already on disk when the repo was initialized, which required adding it to `.gitignore` retroactively. Creating the `.gitignore` before running `npm install` is cleaner.

---

### Dynamic Data Check Results

No hardcoded data issues found. The reflections date (`reflect-date`) is generated dynamically via `new Date().toLocaleDateString()`. The localStorage key is date-keyed (`spacex-playbook-reflect-` + ISO date). Persona labels in `transcribe.py` are a lookup dict, not hardcoded strings in the output.

---

### Repo
https://github.com/lisaqiyali-0105/podcast-recap
