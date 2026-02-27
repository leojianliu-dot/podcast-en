# Daily News Briefing — Podcast Configuration

## Quick Reference

### Daily Update

When the user says **"make the daily podcast"** or **"make the morning/evening update"**:

1. Search today's news using the pre-set topics and sources below
2. Write an English script (2,000-3,200 words for 10-20 min)
3. Save the script to `episode-scripts/YYYY-MM-DD.md` (or `-morning`/`-evening`)
4. Generate audio: `python scripts/generate_audio.py episode-scripts/YYYY-MM-DD.md`
5. Update RSS feed: `python scripts/update_feed.py`
6. Commit and push to GitHub

**This is fully automated.** After the user agrees on the topic direction, Claude executes ALL steps above without stopping for approval.

### Special Report (Deep Dive)

When the user says **"deep dive on [topic]"** or **"special report on [topic]"**:

1. Research the specific topic in depth
2. Write an English script (2,000-3,200 words for 10-20 min)
3. Save to `episode-scripts/YYYY-MM-DD-topic-keyword.md`
4. Generate audio, update feed, commit and push — all automatic

---

## Podcast Identity

| Field | Value |
|-------|-------|
| **Name** | Daily News Briefing |
| **Host Name** | Claude |
| **Language** | English |
| **Tone** | Concise, direct, conversational — like a quick morning catch-up with a well-informed friend |
| **Target Length** | 10-20 minutes per episode |
| **Word Target** | 2,000-3,200 words |
| **Default Voice** | `en-US-GuyNeural` (male, professional) |
| **AI Disclosure** | Every episode opening must include a brief disclosure that this podcast is AI-generated |

---

## News Sources

### Primary Sources (always check these first)

| Source | Strength |
|--------|----------|
| **The Wall Street Journal (WSJ)** | Finance, markets, business, policy |
| **The New York Times (NYT)** | US politics, investigations, analysis |
| **NPR** | Balanced US news, public policy, culture |
| **Associated Press (AP)** | Breaking news, factual wire reporting |
| **Reuters** | Global breaking news, finance, geopolitics |
| **Bloomberg** | Markets, finance, economics, business |
| **CNBC** | Markets, finance, business news, earnings |

### Secondary Sources

| Source | Strength |
|--------|----------|
| **San Francisco Chronicle** | Bay Area local, food, culture |
| **LA Times** | California politics, state news |
| **CalMatters** | California policy, state legislature |
| **TechCrunch / The Verge / Wired** | Tech and AI news |
| **Eater SF / Infatuation SF** | Bay Area food and restaurants |
| **STAT News** | Health and biotech |

Use any reputable source as needed. These are examples, not an exhaustive list.

---

## Episode Types

### Type 1: Daily Update (Default)

**Frequency:** Up to 2x per day (morning, evening) or a single daily roundup

**Content:** Pick 8-10 top stories from today's news across the pre-set topics. Not every topic needs to appear — prioritize what's actually newsworthy today.

**Source Priority:** Drive the day's agenda from **WSJ, Reuters, and NYT** headlines first. Fill remaining slots from other sources.

**Deduplication Rules (IMPORTANT):**
- **Same day, later edition** (morning → evening): Only cover a story again if there are **meaningful new developments**. Don't re-explain — just say what's new.
- **Across days**: Lead with what's new. One-liner recap max, then straight to the update.
- **No repeats with zero updates**: Find a different story instead of padding.

**Bay Area Weather:** Include a brief weather segment near the end ONLY if there is upcoming severe weather (storms, heat waves, air quality alerts). Skip if normal.

**File naming:**

| Slot | Filename | RSS Title |
|------|----------|-----------|
| Single daily | `YYYY-MM-DD.md` | "YYYY-MM-DD Daily News" |
| Morning | `YYYY-MM-DD-morning.md` | "YYYY-MM-DD Morning News" |
| Evening | `YYYY-MM-DD-evening.md` | "YYYY-MM-DD Evening News" |

**Script structure:**

```
1. Opening                          ~100 words
   - Greeting with host name, date, AI disclosure, quick preview
   - Example: "Hey, I'm Claude, and this is the Daily News Briefing for
     Thursday, February 27th. This podcast is AI-generated, pulling from
     WSJ, Reuters, the New York Times, and other major outlets.
     Today: OpenAI closes a massive funding round, the Anthropic-Pentagon
     standoff hits its deadline, and a new restaurant shaking up the Mission..."

2. Story 1                          ~150-250 words
   - What happened
   - Why it matters
   - What's next

3. Transition                       ~10-20 words
   - Quick bridge: "Turning to Washington..." / "On the local front..."

4. Story 2                          ~150-250 words
   (same structure)

5. ... repeat for 8-10 stories ...

6. Weather (ONLY if severe)         ~50 words

7. Closing                          ~50-75 words
   - Quick recap of 2-3 key takeaways
   - Sign-off: "That's the Daily News Briefing for today. I'm Claude.
     Thanks for listening — catch you next time."
```

**Total: ~2,000-3,200 words for 10-20 minutes**

### Type 2: Special Report (Deep Dive)

**Trigger:** User specifies a topic to explore in depth.

**File naming:** `YYYY-MM-DD-topic-keyword.md` (e.g., `2026-02-25-ai-regulation.md`)

**Episode Title Metadata (IMPORTANT):**

For special reports, add a `Title:` line at the very top of the script file:

```
Title: The Anthropic-Pentagon Standoff Explained

Hey, I'm Claude, and welcome to the Daily News Briefing...
```

The `Title:` line is used in the RSS feed and is automatically stripped from audio generation.

**Script structure:**

```
1. Opening                          ~100 words
   - Greeting, AI disclosure, introduce the topic and why it matters today

2. Background                       ~300-400 words
   - Context, history, key players

3. Latest Developments              ~400-500 words
   - What's happening now

4. Analysis                         ~400-500 words
   - Why it matters, who's affected, broader implications

5. Outlook                          ~200-300 words
   - What to watch for

6. Closing                          ~50-75 words
   - Key takeaways, sign-off
```

**Total: ~2,000-3,200 words for 10-20 minutes**

---

## Topics

Refer to `topics.json` for the full structured list. Summary:

| # | Topic | What to Cover |
|---|-------|---------------|
| 1 | Top Headlines | Biggest stories of the day from WSJ/Reuters/NYT |
| 2 | US Politics | Federal policy, Congress, White House, executive orders, SCOTUS |
| 3 | California & State | Governor, state legislature, ballot measures, regulations |
| 4 | Bay Area Local | SF/South Bay city politics, housing, transit, crime, schools |
| 5 | Economy & Markets | Fed, jobs, inflation, earnings, tariffs |
| 6 | Tech & AI | Silicon Valley, AI, big tech, cybersecurity |
| 7 | Personal Finance | Tax tips, savings, housing market, retirement |
| 8 | Bay Area Life | Restaurants, events, travel, things to do |
| 9 | Health & Science | Medical news, public health, biotech |
| 10 | Weather | Severe weather alerts only |

**Topic mix per episode:** Blend hard news (topics 1-6) with lifestyle/practical content (topics 7-8) and health (topic 9). Aim for roughly 5-6 hard news + 2-4 lifestyle/local stories per episode.

**Source priority:** WSJ, Reuters, and NYT headlines drive the day. Fill remaining slots from other sources.

---

## Language & Style Rules

This podcast is for a **local US audience** — people who live in the Bay Area and follow American news daily. Write accordingly:

1. **Natural spoken English** — Write for the ear, not the eye. Use contractions, conversational transitions. This should sound like a smart friend catching you up, not a textbook.
2. **Be direct** — Get to the point fast. No throat-clearing or excessive setup. Lead with the news, then explain why it matters.
3. **Short transitions** — "Turning to tech..." / "On the local front..." / "And finally..." — keep them tight.
4. **Assume cultural knowledge** — The audience knows how the US government works, what BART is, who their state representatives are. Don't over-explain.
5. **Name local specifics** — Use neighborhood names (the Mission, SoMa, Palo Alto), highway numbers (101, 280), BART lines, local politicians by name. This is a local podcast.
6. **Spell out numbers under 10** — "three percent" not "3%", but "the S&P 500" is fine.
7. **Define acronyms on first use** — "the Federal Reserve, or the Fed" — but only for less common ones. Everyone knows what GDP means.
8. **Conversational transitions** — "Now, turning to...", "Here's where it gets interesting...", "So what does this mean?"
9. **Don't hedge excessively** — Instead of "it could potentially maybe impact...", just say "this will hit..." or "this could affect..."
10. **Per-story length** — 150-250 words per story. Some stories need more, some less. Don't pad short stories and don't truncate important ones.

---

## Audio Settings

| Shortcut | Full Name | Style |
|----------|-----------|-------|
| `guy` | `en-US-GuyNeural` | Male, professional (default) |
| `jenny` | `en-US-JennyNeural` | Female, warm |
| `aria` | `en-US-AriaNeural` | Female, conversational |
| `davis` | `en-US-DavisNeural` | Male, authoritative |
| `andrew` | `en-US-AndrewNeural` | Male, natural |

To override the voice:
```bash
python scripts/generate_audio.py episode-scripts/2026-02-27.md -v andrew
```

---

## Automation Workflow

This is the **only** workflow. All podcast generation runs through Claude Code. After the user agrees on topics:

1. Claude searches today's news (web search)
2. Claude writes the script
3. Claude saves the script to `episode-scripts/`
4. Claude runs `python scripts/generate_audio.py <script-path>`
5. Claude runs `python scripts/update_feed.py`
6. Claude runs `git add`, `git commit`, `git push`

**No manual steps required after topic agreement.**

---

## RSS Feed

The RSS feed at `feed.xml` is auto-generated by `scripts/update_feed.py`.

Technical settings are in `podcast-settings.json` (base URL, author name, etc.).

After generating an episode locally, always run:
```bash
python scripts/update_feed.py
```
This scans `episodes/` and rebuilds `feed.xml` with all episodes.

---

## File Naming Summary

| Type | Filename | Title |
|------|----------|-------|
| Daily (single) | `YYYY-MM-DD.md` | "YYYY-MM-DD Daily News" |
| Daily morning | `YYYY-MM-DD-morning.md` | "YYYY-MM-DD Morning News" |
| Daily evening | `YYYY-MM-DD-evening.md` | "YYYY-MM-DD Evening News" |
| Special report | `YYYY-MM-DD-topic.md` | "YYYY-MM-DD TOPIC Special Report" |
