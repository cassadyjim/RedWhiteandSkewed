CRITICAL DATE INSTRUCTION

Today's date is [CURRENT_DATE].
You are creating tomorrow's story, which will be dated [TOMORROW_DATE].

When searching for news:

Search for "news today", "[today's topic]", or "latest [topic]"

DO NOT include specific dates in your searches unless absolutely necessary

If you must use dates, verify the CURRENT date first

Look for stories marked "hours ago" or "today"

Ignore results from 1 year ago with similar dates

Please create today's story using the uploaded template.
Follow all requirements below exactly.

1. SOURCING (CRITICAL)

Look for top news stories as of today's date that have deep political party partisan divide.

Only use:

Verifiable claims from actual news sources

Popular political commentators, opinion leaders, pundits, and talk show hosts

Search extensively using web_search to find how conservative outlets and liberal outlets are ACTUALLY reporting the story.

TARGET PARTISAN SOURCES (CRITICAL)

The goal is to show how EACH SIDE'S MEDIA is framing the story — not balanced sources that present both sides.

CONSERVATIVE SOURCES TO TARGET

TV: Fox News, Fox Business, Newsmax, OAN

Print/Online: Washington Examiner, New York Post, Daily Wire, Breitbart, The Federalist, Washington Times, Just The News, American Greatness, National Review

Radio/Podcasts: Sean Hannity, Mark Levin, Dan Bongino, Steve Bannon's War Room, Ben Shapiro, Glenn Beck, Charlie Kirk

Social Media Personalities: Popular conservative figures on X (Twitter)

LIBERAL SOURCES TO TARGET

TV: MSNBC (Rachel Maddow, Joy Reid, Chris Hayes, Lawrence O'Donnell), CNN opinion hosts

Print/Online: The New Republic, Salon, HuffPost, Daily Beast, Mother Jones, The Nation, Common Dreams, Vox, Daily Kos, Raw Story, Talking Points Memo, The Intercept

Radio/Podcasts: Democracy Now, Pod Save America, Crooked Media shows, Mehdi Hasan

Social Media Personalities: Popular progressive figures on X (Twitter)

SEARCH STRATEGY (MANDATORY)

Search: "[topic] Fox News" and "[topic] MSNBC"

Search: "[topic] Hannity" and "[topic] Maddow"

Search: "[topic] conservative reaction" and "[topic] liberal reaction"

Search: "[topic] Breitbart" and "[topic] Daily Beast"

Look for opinion pieces and commentary, not just straight news

Balanced sources like AP, Reuters, or NPR will NOT show partisan framing and should not be relied upon.

WHY THIS MATTERS

Balanced sources present neutral summaries.
This project captures how each side's echo chamber is presenting the same story to their audience.

2. STORY REQUIREMENTS

Show how each side frames the same event differently

Use direct quotes from partisan voices

Maintain factual accuracy

Avoid speculation

Do not editorialize

Do not invent facts or quotes

3. TEMPLATE USAGE

You must output using the uploaded JSON template exactly.
All required fields must be populated.
Do not change field names or structure.

🔒 4. QUOTE VERIFICATION VIA TIERED SOURCE TRUST (CRITICAL)

## 4.1 SOURCE TRUST TIERS

Red White & Skewed showcases **inflammatory partisan content** — that's the point! The most extreme framing often appears in exclusive interviews, original commentary, and partisan outlets. We need a verification system that:

✅ Captures the juiciest partisan takes from established outlets
✅ Prevents fabricated or unverifiable quotes
✅ Documents our sourcing process transparently

### HIGH-TRUST SOURCES (Single source acceptable)

These outlets have editorial oversight, legal accountability, searchable archives, and established reputations. **Single source is sufficient** if you can document the quote exists via search.

**Major US Broadcast/Cable:**
- ABC News, CBS News, NBC News, PBS News, C-SPAN
- CNN, Fox News, MSNBC, Fox Business, Newsmax

**Major US Newspapers:**
- New York Times, Washington Post, Wall Street Journal, USA Today
- Los Angeles Times, Chicago Tribune, Boston Globe, San Francisco Chronicle
- New York Post, NY Daily News, Boston Herald, Chicago Sun-Times
- Christian Science Monitor

**Major US Digital/News:**
- Associated Press (AP), Reuters, Bloomberg
- Axios, Politico, The Hill, Semafor
- Business Insider, MarketWatch, CNBC
- USA Today

**Established Left-Partisan Outlets:**
- HuffPost, Salon, Daily Beast, Mother Jones, The Atlantic
- The New Republic, The Nation, The Intercept, Vox
- Raw Story, Talking Points Memo, Common Dreams, Daily Kos
- MaddowBlog (MSNBC), Mediaite

**Established Right-Partisan Outlets:**
- Breitbart, Daily Caller, National Review, The Federalist
- Newsmax, Washington Examiner, Washington Times
- Just The News, American Greatness, Free Press, Reason

**Major International News:**
- BBC (UK), The Guardian (UK), The Telegraph (UK), The Times (UK)
- The Independent (UK), Daily Mail (UK), Daily Mirror (UK), Daily Express (UK)
- Financial Times (UK), The Economist (UK), Sky News (UK)
- Le Monde (France), Le Figaro (France)
- El País (Spain), El Mundo (Spain)
- Die Zeit (Germany), Die Welt (Germany)
- Haaretz (Israel), Jerusalem Post (Israel), Yeshiva World
- Times of India, Hindustan Times, The Hindu
- Japan Times, Yomiuri Shimbun, Nikkei Asia
- Sydney Morning Herald (Australia)
- China People's Daily, Arab News, Moscow Times

**Entertainment/Trade Publications (with editorial standards):**
- TMZ, Variety, Hollywood Reporter, Deadline Hollywood
- Billboard, Rolling Stone, Entertainment Weekly
- People Magazine, Vanity Fair

**Regional/Specialty (when covering local/specialty topics):**
- El Nuevo Día (Puerto Rico), La Prensa, La Repubblica
- Folha de S.Paulo, Rio Times, Clarín
- Gazeta Wyborcza

**WHY THESE ARE TRUSTED:**
- Editorial oversight: Multiple editors review content before publication
- Legal accountability: Can be sued for defamation, incentivizing accuracy
- Searchable archives: Claims can be independently verified
- Established reputation: Years/decades of journalism, reputation at stake
- Named bylines: Real journalists whose careers depend on accuracy

### MEDIUM-TRUST SOURCES (Single source acceptable for distinctive/inflammatory quotes)

These sources have some editorial standards but are newer, less established, or more niche:

- NY Magazine, Vanity Fair (for politics), New Yorker (breaking news)
- Mediaite, Deadline Hollywood, Wrap
- CBS News Local affiliates
- State-level news sites (Stateline)

**Single source acceptable IF:**
- Quote is particularly distinctive or inflammatory (exactly what RWS needs)
- Search query documented
- Search result excerpt proves quote exists

### LOW-TRUST SOURCES (Require 2+ corroborating sources)

These lack consistent editorial standards or are pure aggregators:

- Anonymous gossip blogs (e.g., Crazy Days and Nights)
- Pure aggregators (Yahoo News aggregated content, MSN aggregated content, Newzit)
- Social media screenshots without verification
- Blogs without established track records
- "World of Reel" and similar entertainment gossip sites
- Any source without named authors/editors

## 4.2 Build a Quote Ledger (MANDATORY)

Before writing the story, create a Quote Ledger table.

Each row MUST include:

**Quote ID** (Q001, Q002…)

**Speaker name**

**Speaker role**

**Exact quote** (verbatim)

**Search Query Used** (exact search string you ran to find this quote)

**Search Result Context** (copy 30+ word excerpt from search result showing quote with surrounding text)

**Corroborating Sources** (list ALL outlets that reported this quote)

**Source Count** (number of independent sources: 0, 1, 2, 3+)

**Source Trust Tier** (HIGH / MEDIUM / LOW)

**Canonical Source URL** (ONE only - selected using Source Hierarchy below)

**Outlet name**

**Page title**

**Publish date**

**Distinctive anchor phrase** (exact substring of the quote to hyperlink)

**Verification Status:**
- ✅ VERIFIED - HIGH-TRUST (1+ high-trust sources)
- ✅ VERIFIED - MULTI-SOURCE (2+ sources, any tier)
- ⚠️ SINGLE MEDIUM-TRUST (acceptable if inflammatory/distinctive)
- ❌ SINGLE LOW-TRUST (requires corroboration - remove if not found)
- ❌ UNVERIFIED (0 sources - REMOVE immediately)

**Duplicate check:**
"Also appears at: [URL1], [URL2]" (if applicable)

## 4.3 ENFORCEMENT RULES (NON-NEGOTIABLE)

**VERIFICATION REQUIREMENTS:**

0. **PERSON MUST BE ALIVE (NON-NEGOTIABLE)**
   - Before adding ANY quote from a named individual, search "[person name] death 2025 2026" to confirm they are currently alive.
   - If the person is deceased, **remove the quote entirely** — do not rephrase, do not reassign, just delete it.
   - Quoting a dead person as if they are actively commenting is a critical factual error.

0b. **SPEAKER'S NAME MUST APPEAR IN THE SOURCE URL'S CONTENT**
   - The search result context must contain BOTH the speaker's name AND the quote text.
   - If the source URL does not mention the speaker's name, the quote is fabricated. Mark ❌ UNVERIFIED and DELETE immediately.
   - A URL about a related topic is NOT proof that the person said something.

1. **Every quote MUST have a documented WebSearch query**

2. **Search Result Context MUST show actual quote text with 30+ surrounding words**

3. **HIGH-TRUST sources:** Single source acceptable
   - If CBS News, NBC News, Fox News, MSNBC, NYT, WaPo, WSJ, Breitbart, Salon, HuffPost, Daily Beast, National Review, etc. publishes it → their editorial process verified it
   - Must still document: search query + search result excerpt + URL

4. **MEDIUM-TRUST sources:** Single source acceptable for distinctive/inflammatory content
   - These quotes are often the most valuable for showing partisan framing
   - Must document: search query + search result excerpt + URL

5. **LOW-TRUST sources:** Require 2+ corroborating sources
   - Anonymous blogs, pure aggregators, unestablished sites need corroboration

6. **ZERO sources found:** Mark ❌ UNVERIFIED and DELETE immediately

7. **Generic search summaries like "sources say..." are NOT verification** - must see actual quote in search result

**BEFORE MOVING TO QUOTE AUDIT:**
Count verification statuses:
- How many ✅ VERIFIED - HIGH-TRUST?
- How many ✅ VERIFIED - MULTI-SOURCE?
- How many ⚠️ SINGLE MEDIUM-TRUST?
- How many ❌ SINGLE LOW-TRUST?
- How many ❌ UNVERIFIED?

If any ❌ SINGLE LOW-TRUST or ❌ UNVERIFIED exist, remove them.

## 4.4 Source Hierarchy for Canonical URL Selection

When multiple sources report the same quote, choose ONE canonical source using this priority:

**Tier 1:** Original statement
- Official social media (Twitter/Truth Social verified account)
- Official press release
- Official transcript

**Tier 2:** Primary broadcaster/interviewer
- The show where the interview occurred (Charlie Kirk Show, Fox News, CNN, etc.)
- Press conference video/transcript

**Tier 3:** Major news outlet
- National networks: ABC, CBS, NBC, CNN, Fox News, MSNBC
- Major newspapers: NYT, WaPo, WSJ, USA Today

**Tier 4:** Partisan outlets (PREFER for partisan commentary)
- Conservative: Breitbart, Daily Wire, National Review, Washington Examiner, Newsmax
- Liberal: Salon, HuffPost, Daily Beast, Mother Jones, The New Republic, Raw Story
- **WHY:** Partisan outlets often have the most inflammatory framing — that's the value!

**Tier 5:** Regional/local news
- Local broadcast stations
- Regional newspapers

**Tier 6:** Aggregators (AVOID if possible)
- Yahoo News, MSN, Google News aggregated content

## 4.5 Duplicate Quote Resolution (NON-NEGOTIABLE)

If the same quote text appears in multiple sources:

1. List ALL sources in "Corroborating Sources" field
2. Count them in "Source Count" field
3. Select canonical URL using Source Hierarchy above
4. That URL becomes the ONLY valid link for that quote
5. Other appearances recorded but never linked

## 4.6 Anchor Phrase Locking

When inserting quotes in the story:

The hyperlink must wrap ONLY the ledger's Distinctive Anchor Phrase

The phrase must be copied verbatim from the ledger

Do not invent new anchor phrases

Do not wrap full paragraphs

Format:

<a href="LEDGER_URL">DISTINCTIVE_ANCHOR_PHRASE</a>

## 4.7 No Cross-Linking Rule (STRICT)

If two sources contain the same quote:

❌ Do not attach Source B's URL to Source A's quote

❌ Do not rotate or substitute URLs

❌ Do not mix quote text from one page with URL from another

❌ Do not link aggregators if an original exists

Only the canonical URL from the ledger is permitted.

5. QUOTE AUDIT (MANDATORY)

Before producing the final output, generate a Quote Audit Table with:

Quote ID

Speaker

Search Query Used

Source Count

Source Trust Tier

Verification Status

Canonical URL

**ACCEPTABLE VERIFICATION STATUSES FOR PUBLICATION:**
- ✅ VERIFIED - HIGH-TRUST
- ✅ VERIFIED - MULTI-SOURCE
- ⚠️ SINGLE MEDIUM-TRUST (if quote is inflammatory/distinctive)

**MUST BE REMOVED:**
- ❌ SINGLE LOW-TRUST
- ❌ UNVERIFIED

SELF-CHECK BEFORE AUDIT:
- How many quotes are in my ledger?
- How many are from HIGH-TRUST sources?
- How many have 2+ corroborating sources?
- How many are SINGLE MEDIUM-TRUST?
- How many are SINGLE LOW-TRUST?
- How many are UNVERIFIED?

If "SINGLE LOW-TRUST" + "UNVERIFIED" > 0, STOP and remove those quotes.

6. FAILURE CONDITIONS (OUTPUT INVALID IF ANY OCCUR)

A quote is attributed to a person who is deceased

A quote appears in the story but not in the Quote Ledger

The source URL does not mention the speaker's name (fabricated attribution)

A quote links to a URL different from its ledger entry

A duplicate quote links to a non-canonical source

Search Query Used field is missing

Search Result Context is missing or doesn't contain the actual quote

Quote from LOW-TRUST source has fewer than 2 corroborating sources

Verification Status shows ❌ SINGLE LOW-TRUST or ❌ UNVERIFIED

Quote audit is skipped

Any quote without documented search query and search result context

7. OUTPUT ORDER (MANDATORY)

Output in this exact order:

Quote Ledger table (with all required fields including Source Trust Tier)

Self-Check Results (quote counts by verification status)

Quote Audit table

Final JSON story output (using the uploaded template)

## 8. POLL BUTTON CUSTOMIZATION

**CRITICAL: Every story must include a `poll` field with customized button labels that reflect the specific debate framing in the title.**

Do NOT use generic labels like "I support the Conservative View" or "I support the Liberal View". Instead, extract the core tension from the title and create concise poll options.

### Poll Field Structure:

```json
{
  "poll": {
    "question": "Short question about the topic (e.g., 'What do you think about...')",
    "options": [
      {
        "label": "Conservative Frame",
        "description": "Brief description of conservative position (shown on hover)"
      },
      {
        "label": "Liberal Frame",
        "description": "Brief description of liberal position (shown on hover)"
      }
    ]
  }
}
```

### Examples:

**Title:** "Justice or Retribution? FBI Raids Georgia Election Office"
```json
"poll": {
  "question": "What do you think about the FBI raid?",
  "options": [
    {
      "label": "Justice",
      "description": "Legitimate investigation to uncover the truth about 2020"
    },
    {
      "label": "Retribution",
      "description": "Political revenge against officials who refused to overturn 2020"
    }
  ]
}
```

### Guidelines:
- Labels should be 1-3 words maximum
- Labels should capture the essence of each side's framing
- Descriptions should be concise (under 15 words)
- The poll field must be placed in the JSON immediately after the `subtitle` field and before the `conservative` field
- Conservative option always goes first (index 0), liberal second (index 1)

---

Look for stories that have been national news headlines as of today's date. The story in the JSON will be for tomorrow. Show me 10 story options.

---
### 9. Reverify that URL are linked to the propoer sources
Do one more check that all facts and quotes are referenced and linked to a source. To avoid mistakes that you made before, search result summaries that said "Daily Caller reported X" and verify the quotes throughout the content actually appeared at that URL.

---
### 10. Pre-Publish Verification (MANDATORY — do this BEFORE providing publish commands) ###

After the story JSON is complete, STOP and ask the user to verify before publishing. Present:

**A. Image preview link**
Provide the direct image URL as a clickable link so the user can open it in their browser and confirm it's the right photo:
> 🖼️ **Preview image:** [filename or description](IMAGE_URL)

**B. Story summary for approval**
Show a compact summary:
> 📰 **Title:** [title]
> 📅 **Date:** [date]
> 🔴 **Conservative headline:** [headline]
> 🔵 **Liberal headline:** [headline]
> ✅ **Poll:** "[question]" — [option 1] vs [option 2]

Then ask:
> "Does the image and story look good? Reply **yes** to publish, or tell me what to change."

Do NOT provide the publish commands until the user confirms. Only after receiving approval, provide:
```
./rws_publish.sh yyyy-mm-dd-story-name.json
python3 rws_to_wix.py yyyy-mm-dd-story-name.json
```

---
### 11. Story Image (MANDATORY) ###

Every story JSON must include an `image` field. The image must be **royalty-free and publicly licensed**.

**NEUTRALITY RULE (CRITICAL):**
The image must illustrate the **topic**, never the **subject**.
- ❌ DO NOT use official portraits or favorable photos of politicians — this makes the site appear biased toward whichever politician is featured.
- ✅ DO use images of places, institutions, symbols, or objects related to the story.

**Image Selection by Story Type:**

| Story Topic | Use This Type of Image |
|---|---|
| Elections / Voting / Ballots | Polling station, voting booth, ballot box, "Vote Here" sign |
| Congress / Legislation | Capitol building exterior, Senate/House chamber |
| White House / Executive Orders | White House exterior, Oval Office (empty), Rose Garden |
| Supreme Court / Legal | Supreme Court building, gavel, scales of justice |
| Economy / Budget / Taxes | Stock ticker, Federal Reserve building, currency |
| Immigration / Border | Border landscape, immigration court, naturalization ceremony |
| Military / Foreign Policy | Pentagon exterior, flag, military equipment (generic) |
| Healthcare | Hospital exterior, stethoscope, prescription bottles |
| Climate / Environment | Smokestacks, clean energy (wind/solar), natural landscape |
| Education | Classroom, school building, books |
| Social Security / Entitlements | Social Security Administration building, elderly Americans |

**Approved Free Sources (in order of preference):**
1. **Pexels** — `pexels.com` — Free for commercial use, hotlink-friendly, verified working ✅
2. **Wikimedia Commons** — `commons.wikimedia.org` — Search for CC0 or Public Domain images
3. **U.S. Government Photos** — Congress, federal agencies, military — all public domain by law
4. **Unsplash** — `unsplash.com` — Free for commercial use, no attribution required

**⚠️ White House Flickr Caution:**
White House Flickr photos are public domain but are professionally curated to make the current president look favorable. Avoid using them as the primary image — it creates the appearance that RWS endorses the administration. Use only as a last resort if no neutral topical image is available.

**HOW TO FIND THE IMAGE (Cowork/VM mode — MANDATORY process):**

The `rws_find_image.py` script cannot run from the VM (outbound network is blocked). Instead, use WebSearch to find and verify a Pexels image URL directly. This is the required process:

**Step 1 — Search Pexels via WebSearch:**
```
WebSearch: site:pexels.com "[story topic keywords]"
```
Example: `site:pexels.com "fighter jet military aircraft"`

**Step 2 — Extract the Pexels photo ID from the result URL:**
The result URL will look like: `https://www.pexels.com/photo/some-title-here-XXXXXX/`
The number at the end is the photo ID.

**Step 3 — Construct the hotlink URL using this pattern:**
```
https://images.pexels.com/photos/{ID}/pexels-photo-{ID}.jpeg?auto=compress&cs=tinysrgb&w=1200
```
Example: Photo ID 7517886 → `https://images.pexels.com/photos/7517886/pexels-photo-7517886.jpeg?auto=compress&cs=tinysrgb&w=1200`

**⚠️ Photo ID must be above 500,000.** Very old Pixabay-migrated photos (low IDs like 66872, 72593) use a different CDN path and will NOT hotlink reliably. Always pick a recent, native Pexels photo with a high ID number from the search results.

**Step 4 — Fill in the image JSON:**
```json
"image": {
  "url": "https://images.pexels.com/photos/{ID}/pexels-photo-{ID}.jpeg?auto=compress&cs=tinysrgb&w=1200",
  "credit": "Photo: [Photographer Name] / Pexels",
  "alt": "Descriptive alt text for the image",
  "source": "Pexels",
  "page": "https://www.pexels.com/photo/[slug]-{ID}/",
  "license": "Pexels License"
}
```

**WIKIMEDIA COMMONS — Use when Pexels has no suitable image (e.g. missile intercepts, specific political institutions):**

Step 1 — Find the exact filename via WebSearch:
```
WebSearch: "commons.wikimedia.org/wiki/Category:" [topic]
```
Read the category description carefully — it lists exact filenames with dimensions.

Step 2 — Compute the MD5-based URL entirely offline using bash (no network needed):
```bash
python3 -c "
import hashlib
fn = 'Exact_Filename_With_Underscores.jpg'
h = hashlib.md5(fn.encode('utf-8')).hexdigest()
print(f'https://upload.wikimedia.org/wikipedia/commons/thumb/{h[0]}/{h[0:2]}/{fn}/1200px-{fn}')
"
```

Step 3 — Fill in the image JSON:
```json
"image": {
  "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/[a]/[ab]/Filename.jpg/1200px-Filename.jpg",
  "credit": "Photo: Photographer / Wikimedia Commons",
  "alt": "Descriptive alt text",
  "source": "Wikimedia Commons",
  "page": "https://commons.wikimedia.org/wiki/File:Filename.jpg",
  "license": "CC BY-SA 2.0"
}
```

**To find a Wikimedia Commons image URL** (when running from Mac Terminal only), use the `rws_find_image.py` script:
```bash
python3 rws_find_image.py "voting booth election"
```

---

DESIGN GOAL

This system ensures:

Real-time relevance

Strong partisan contrast

Deterministic quote attribution

No link drift

Auditable sourcing through documented search queries

Inflammatory partisan content from established outlets (the whole point of RWS!)

Protection against fabricated quotes while trusting editorial processes

Transparent verification that anyone can reproduce

Dynamic poll framing tied to the story's core debate
