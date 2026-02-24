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

Print/Online: The New Republic, Salon, HuffPost, Daily Beast, Mother Jones, The Nation, Common Dreams, Vox, Daily Kos, Raw Story, Talking Points Memo

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

🔒 4. QUOTE VERIFICATION VIA MULTI-SOURCE CORROBORATION (CRITICAL)

4.1 Build a Quote Ledger (MANDATORY)

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

**Canonical Source URL** (ONE only - selected using Source Hierarchy below)

**Outlet name**

**Page title**

**Publish date**

**Distinctive anchor phrase** (exact substring of the quote to hyperlink)

**Verification Status:**
- ✅ VERIFIED (2+ sources)
- ⚠️ SINGLE SOURCE (1 source only - requires additional verification)
- ❌ UNVERIFIED (0 sources - REMOVE immediately)

**Duplicate check:**
"Also appears at: [URL1], [URL2]" (if applicable)

🚨 ENFORCEMENT RULES (NON-NEGOTIABLE):

1. Every quote MUST have a documented WebSearch query
2. Search Result Context MUST show actual quote text with 30+ surrounding words
3. Minimum 2 independent sources required for ✅ VERIFIED status
4. If only 1 source found: Mark ⚠️ SINGLE SOURCE and search again with different queries
5. If 0 sources found: Mark ❌ UNVERIFIED and DELETE from ledger immediately
6. Generic search result summaries like "sources say..." are NOT verification
7. Before moving to Quote Audit: Count single-source quotes. If >0, remove them or find corroboration.

4.2 Source Hierarchy for Canonical URL Selection

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

**Tier 4:** Partisan outlets (for partisan commentary)
- Conservative: Breitbart, Daily Wire, National Review, Washington Examiner
- Liberal: Salon, HuffPost, Daily Beast, Mother Jones, The New Republic

**Tier 5:** Regional/local news
- Local broadcast stations
- Regional newspapers

**Tier 6:** Aggregators (AVOID if possible)
- Yahoo News, MSN, Google News aggregated content

4.3 Duplicate Quote Resolution (NON-NEGOTIABLE)

If the same quote text appears in multiple sources:

1. List ALL sources in "Corroborating Sources" field
2. Count them in "Source Count" field
3. Select canonical URL using Source Hierarchy above
4. That URL becomes the ONLY valid link for that quote
5. Other appearances recorded but never linked

4.4 Anchor Phrase Locking

When inserting quotes in the story:

The hyperlink must wrap ONLY the ledger's Distinctive Anchor Phrase

The phrase must be copied verbatim from the ledger

Do not invent new anchor phrases

Do not wrap full paragraphs

Format:

<a href="LEDGER_URL">DISTINCTIVE_ANCHOR_PHRASE</a>

4.5 No Cross-Linking Rule (STRICT)

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

Verification Status (✅ VERIFIED / ⚠️ SINGLE SOURCE / ❌ UNVERIFIED)

Canonical URL

If any entry shows ⚠️ SINGLE SOURCE or ❌ UNVERIFIED:

Remove that quote from the ledger

Remove it from the story

SELF-CHECK BEFORE AUDIT:
- How many quotes are in my ledger?
- How many have 2+ corroborating sources?
- How many have only 1 source?
- How many have 0 sources?

If "only 1 source" + "0 sources" > 0, STOP and remove those quotes.

6. FAILURE CONDITIONS (OUTPUT INVALID IF ANY OCCUR)

A quote appears in the story but not in the Quote Ledger

A quote links to a URL different from its ledger entry

A duplicate quote links to a non-canonical source

Search Query Used field is missing

Search Result Context is missing or doesn't contain the actual quote

Source Count is less than 2

Verification Status shows ⚠️ SINGLE SOURCE or ❌ UNVERIFIED

Quote audit is skipped

Any quote without documented corroborating sources

7. OUTPUT ORDER (MANDATORY)

Output in this exact order:

Quote Ledger table (with all required fields)

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

### Provide Publish Command ###
After the new story is created in the proper JSON format, Provide me the terminal command to run in the format of "./rws_publish.sh yyyy-mm-dd-story-name.json".

---

DESIGN GOAL

This system ensures:

Real-time relevance

Strong partisan contrast

Deterministic quote attribution

No link drift

Auditable sourcing through documented search queries

Multi-source corroboration preventing fabricated quotes

Transparent verification that anyone can reproduce

Dynamic poll framing tied to the story's core debate
