CRITICAL DATE INSTRUCTION

Today's date is [CURRENT_DATE].
You are creating tomorrow’s story, which will be dated [TOMORROW_DATE].

When searching for news:

Search for "news today", "[today's topic]", or "latest [topic]"

DO NOT include specific dates in your searches unless absolutely necessary

If you must use dates, verify the CURRENT date first

Look for stories marked "hours ago" or "today"

Ignore results from 1 year ago with similar dates

Please create today’s story using the uploaded template.
Follow all requirements below exactly.

1. SOURCING (CRITICAL)

Look for top news stories as of today’s date that have deep political party partisan divide.

Only use:

Verifiable claims from actual news sources

Popular political commentators, opinion leaders, pundits, and talk show hosts

Search extensively using web_search to find how conservative outlets and liberal outlets are ACTUALLY reporting the story.

TARGET PARTISAN SOURCES (CRITICAL)

The goal is to show how EACH SIDE’S MEDIA is framing the story — not balanced sources that present both sides.

CONSERVATIVE SOURCES TO TARGET

TV: Fox News, Fox Business, Newsmax, OAN

Print/Online: Washington Examiner, New York Post, Daily Wire, Breitbart, The Federalist, Washington Times, Just The News, American Greatness, National Review

Radio/Podcasts: Sean Hannity, Mark Levin, Dan Bongino, Steve Bannon’s War Room, Ben Shapiro, Glenn Beck, Charlie Kirk

Social Media Personalities: Popular conservative figures on X (Twitter)

LIBERAL SOURCES TO TARGET

TV: MSNBC (Rachel Maddow, Joy Reid, Chris Hayes, Lawrence O’Donnell), CNN opinion hosts

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
This project captures how each side’s echo chamber is presenting the same story to their audience.

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

🔒 4. QUOTE–SOURCE BINDING & DISAMBIGUATION (CRITICAL)
4.1 Build a Quote Ledger (MANDATORY)

Before writing the story, create a Quote Ledger table.

Each row MUST include:

Quote ID (Q001, Q002…)

Speaker name

Speaker role

Exact quote (verbatim)

Canonical source URL (ONE only)

Outlet name

Page title

Publish date

Distinctive anchor phrase (exact substring of the quote to hyperlink)

Proof-of-presence (copy 15–30 surrounding words from the page showing the quote in context)

Duplicate check:
“Also appears at: [URL1], [URL2]” (if applicable)

RULE:
If a quote is not in the Quote Ledger, it may NOT appear in the story.

4.2 Duplicate Quote Resolution (NON-NEGOTIABLE)

If the same quote text appears in multiple sources, choose ONE canonical source using this priority:

Official transcript / official statement / original social media post

Primary broadcaster or interviewer’s page

Full partisan article containing the quote

Once selected:

That URL becomes the ONLY valid link for that quote

Other appearances are recorded but never linked

4.3 Anchor Phrase Locking

When inserting quotes in the story:

The hyperlink must wrap ONLY the ledger’s Distinctive Anchor Phrase

The phrase must be copied verbatim from the ledger

Do not invent new anchor phrases

Do not wrap full paragraphs

Format:

<a href="LEDGER_URL">DISTINCTIVE_ANCHOR_PHRASE</a>

4.4 No Cross-Linking Rule (STRICT)

If two sources contain the same quote:

❌ Do not attach Source B’s URL to Source A’s quote

❌ Do not rotate or substitute URLs

❌ Do not mix quote text from one page with URL from another

❌ Do not link aggregators if an original exists

Only the canonical URL from the ledger is permitted.

5. QUOTE AUDIT (MANDATORY)

Before producing the final output, generate a Quote Audit Table with:

Quote ID

Anchor phrase

Canonical URL

“Quote found on page?” (Yes/No)

If any entry is “No”:

Remove that quote from the ledger

Remove it from the story

6. FAILURE CONDITIONS (OUTPUT INVALID IF ANY OCCUR)

A quote appears in the story but not in the Quote Ledger

A quote links to a URL different from its ledger entry

A duplicate quote links to a non-canonical source

Proof-of-presence is missing

Quote audit is skipped

7. OUTPUT ORDER (MANDATORY)

Output in this exact order:

Quote Ledger table

Quote Audit table

Final JSON story output (using the uploaded template)

1## 11. POLL BUTTON CUSTOMIZATION

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

**Title:** "Economic Boom or Bubble? Markets Hit Record Highs"
```json
"poll": {
  "question": "How would you characterize the current markets?",
  "options": [
    {
      "label": "Boom",
      "description": "Strong fundamentals driving sustainable growth"
    },
    {
      "label": "Bubble",
      "description": "Unsustainable speculation heading for a crash"
    }
  ]
}
```

**Title:** "National Security or Civil Liberties? New Surveillance Program Announced"
```json
"poll": {
  "question": "What's your view on the surveillance program?",
  "options": [
    {
      "label": "National Security",
      "description": "Necessary protection against threats"
    },
    {
      "label": "Civil Liberties",
      "description": "Unconstitutional invasion of privacy"
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



DESIGN GOAL

This system ensures:

Real-time relevance

Strong partisan contrast

Deterministic quote attribution

No link drift

Auditable sourcing

Dynamic poll framing tied to the story’s core debate

