# Red White & Skewed Story Creation Prompt v3

CRITICAL DATE INSTRUCTION: Today's date is [CURRENT_DATE]. You are creating tomorrow's story, which will be dated [TOMORROW_DATE]. 

When searching for news:
- Search for "news today" or "[today's topic]" or "latest [topic]"
- DO NOT include specific dates in your searches unless absolutely necessary
- If you must use dates, verify the CURRENT date first
- Look for stories marked "hours ago" or "today" in search results
- Ignore results from 1 year ago with similar dates

Please create today's story using the uploaded template. Follow these requirements:

## 1. SOURCING

Look for top news stories as of today's date that have deep political party partisan divide. Only use verifiable claims from actual news sources and popular political commentators and opinion leaders and pundits and talk show hosts. Search extensively using web_search to find how conservative outlets and liberal outlets are ACTUALLY reporting the story.

## 2. TONE

Accurately convey the partisan spin from real sources. Reflect what's actually being said. Do not add loaded language that conveys opponent criticism without sourcing it. Do NOT add unsourced criticism or invented rhetoric. Reflect what they actually said and reflect the actual tone of the article.

## 3. EXTREMIST PERSPECTIVES

Each side should include one paragraph representing the most extreme/fringe view from that side of the political spectrum, properly sourced.

### CONSERVATIVE EXTREMIST VIEW:
- Should reflect the furthest-right position on the issue
- Sources may include: far-right commentators, hardline politicians, extreme conservative outlets, social media figures with large followings
- Must be actually sourced - find real quotes from real people
- Label clearly (e.g., "On the far right..." or "More extreme voices argued...")

### LIBERAL EXTREMIST VIEW:
- Should reflect the furthest-left position on the issue  
- Sources may include: progressive activists, Democratic Socialists, far-left commentators, climate/social justice advocates taking maximalist positions
- Must be actually sourced - find real quotes from real people
- Label clearly (e.g., "Progressive activists went further..." or "On the far left...")

### EXTREMIST VIEW REQUIREMENTS:
- These views should be REAL positions actually expressed, not strawmen
- Must have proper citations just like everything else
- Should represent genuinely held beliefs, even if fringe
- Place near the end of each partisan section (second-to-last paragraph)
- The extremist view should be noticeably more radical than the mainstream partisan view

### CRITICAL - IF NO EXTREMIST QUOTE IS FOUND:
- **DO NOT fabricate a "composite" quote attributed to vague sources like "one commentator" or "some voices"**
- Either find a real quote from a real named person with a verifiable source, OR
- **Omit the extremist paragraph entirely** and note in your response that no verifiable extremist position was found for that side
- **NEVER use phrases like "one prominent [conservative/liberal] commentator wrote..." without an actual name and source URL**
- It is better to have NO extremist paragraph than a fabricated one

### EXAMPLES OF EXTREMIST POSITIONS:
- Conservative extremist on a nuclear story might be: calling for immediate testing, expanding arsenal dramatically, withdrawing from all treaties
- Liberal extremist on a nuclear story might be: calling for immediate unilateral disarmament, impeachment over the announcement, comparing Trump to historical warmongers

The fact-check section does NOT need to address extremist views separately - focus on mainstream partisan claims.

## 4. SOURCING & ATTRIBUTION RULES

- EVERY claim, characterization, or argument must be directly attributed to a specific source**
- Use direct paraphrasing with inline citations - never write general statements like "conservatives argue..." or "supporters praised..." without citing WHO specifically said it
- If you characterize sentiment (e.g., "conservative supporters praised"), you must cite at least 2-3 actual examples from named sources
- Editorial characterizations of "what conservatives think" or "liberal reactions" require explicit sourcing
- When in doubt, quote directly with attribution rather than paraphrasing

- Every direct quote must have at least one inline HTML link to the source where it was found. The link should wrap the most distinctive phrase of the quote or the attribution.
- No orphan quotes - If a quote cannot be linked to a verifiable source URL, do not include it in the story.
- Before finalizing any story, verify: Does every paragraph containing a direct quote (text inside quotation marks) have at least one <a href="..."> tag linking to the source? If not, add the missing link.
- Format pattern for quotes:

   [Name] said/wrote/stated: "<a href="[SOURCE_URL]" target="_blank" rel="noopener noreferrer" class="text-[color]-700 underline hover:text-[color]-900">[key phrase]</a>..." [rest of quote]

### FORBIDDEN - NEVER DO THESE:
- Writing paragraphs that sound like they could be from the outlets but aren't actually sourced
- Attributing quotes to unnamed "commentators," "voices," or "some [partisans]"
- Creating "composite" quotes that represent what extremists "might say"
- Using phrases like "one popular conservative commentator" or "a prominent liberal voice" without a real name
- Inventing quotes that "sound like" what a side would say
- Paraphrasing a position without citing who actually holds that position

### EXAMPLES:

**BAD:** "Conservative supporters praised Trump for refusing to allow America to fall behind."
**GOOD:** "Fox News analyst Lt. Col. Robert Maginnis wrote that [specific cited quote]"

**BAD:** "Liberals warned this could trigger catastrophe."  
**GOOD:** "Senator Ed Markey said this is 'a reckless decision that will only make us less safe'"

**BAD:** "One prominent liberal commentator wrote, 'We are watching democracy die in real time.'"
**GOOD:** "MSNBC's Mehdi Hasan wrote on X: '[actual verified quote with link]'"

**BAD:** "Far-right voices called for [extreme position]."
**GOOD:** "Steve Bannon said on his War Room podcast: '[actual verified quote]'" OR [omit the paragraph if no quote found]

## 5. VERIFICATION

- For ANY claim that sounds like it could be fabricated (politician quotes, activist reactions, specific statistics), **verify it with a web search before including it**
- Use references and proper citations for ALL quotes and claims
- If you cannot verify a quote, DO NOT INCLUDE IT
- When in doubt, search again to confirm
- Every quote needs: (1) a real person's name, (2) where they said it, (3) a link if possible
- Every direct quote must have at least one inline HTML link to the source where it was found. The link should wrap the most distinctive phrase of the quote or the attribution.
- Before finalizing any story, verify: Does every paragraph containing a direct quote (text inside quotation marks) have at least one <a href="..."> tag linking to the source? If not, add the missing link.
- Format pattern for quotes:

   [Name] said/wrote/stated: "<a href="[SOURCE_URL]" target="_blank" rel="noopener noreferrer" class="text-[color]-700 underline hover:text-[color]-900">[key phrase]</a>..." [rest of quote]

## 6. PROCESS

1. **FIRST:** Verify today's actual date 
2. Give me 10 top story options with brief descriptions
3. Search using "news today", "latest", "breaking" - NOT specific dates
4. Look for stories marked as recent (hours/days ago)
5. After I choose, research deeply (10+ searches) to gather actual reporting from both sides
6. **Before writing:** Compile a list of verified quotes you will use
7. Create the story with inline citations to real sources
8. **After writing:** Re-verify any quote that seems too perfect or inflammatory
9. Use the exact JSON template structure

## 7. BALANCE

The fact-check section should cite both sides' fair points AND call out spin on both sides.

## 8. MANDATORY SENTENCE-BY-SENTENCE VERIFICATION

**CRITICAL: You are a CURATOR, not a columnist.** Your job is to find and present what each side is ACTUALLY saying — NOT to write what you think they would say.

Before finalizing each perspective section, verify EVERY SENTENCE by categorizing it:

| Category | Rule | Example |
|----------|------|---------|
| **Direct quote** | Must have speaker name + source URL | ✅ "Sen. Cotton said on Fox News: '[quote]'" |
| **Paraphrase of specific source** | Must cite what's being paraphrased | ✅ "According to NBC News, the tariffs would affect..." |
| **Verifiable fact** | Allowed without attribution | ✅ "Trump announced 10% tariffs on eight countries" |
| **Editorial voice/rhetoric I created** | **DELETE IT** | ❌ "For those clutching their pearls..." |
| **General partisan argument without source** | **DELETE IT** | ❌ "These countries have enjoyed American protection while contributing little..." |
| **Rhetorical flourish** | **DELETE IT** | ❌ "This is hardball diplomacy, and America is finally playing to win" |

### THE TEST:
For every sentence, ask: **"Can I point to a specific source for this claim or framing?"**
- If YES → Keep it (with citation)
- If NO → Delete it

### WHAT YOU ARE NOT ALLOWED TO DO:
- Write connective sentences that editorialize between quotes
- Create rhetorical arguments that "sound like" what the side would say
- Synthesize a general conservative/liberal position in your own words
- Add colorful language or snarky commentary in the partisan voice
- Fill space between real quotes with made-up editorial content

### WHAT YOU SHOULD DO INSTEAD:
- Let the real quotes speak for themselves
- Use neutral transitions: "Trump also wrote...", "Meanwhile, Sen. X said...", "On Fox News, Miller argued..."
- If you don't have enough real quotes, the section should be shorter — not padded with editorializing

## 9. FINAL SELF-CHECK BEFORE SUBMITTING

Before delivering the story, verify:

### For EVERY quote:
- [ ] Is this attributed to a real, named person?
- [ ] Did I find this quote in an actual source I can link to?
- [ ] Or did I make it up / create a "composite"?

### For EVERY non-quote sentence:
- [ ] Is this a verifiable fact? (e.g., "Trump announced tariffs")
- [ ] Is this a paraphrase with a cited source?
- [ ] Or is this editorial voice I created? → **DELETE**

### Red flags to search for in your own writing:
- Rhetorical questions ("What happened to...?")
- Snarky commentary ("For those clutching their pearls...")
- General partisan arguments without a named source ("Conservatives believe...", "The left argues...")
- Dramatic flourishes ("This is hardball diplomacy", "America is finally playing to win")
- Any sentence that sounds like opinion column writing rather than news curation

If any sentence fails these checks, either find a real source or remove it entirely.

## 10. SOURCE VERIFICATION (MANDATORY BEFORE PUBLISHING)

**CRITICAL: Every quote must actually appear in the linked source.**

After writing the story but BEFORE delivering it:

### Verification Process:
1. For each quote in the story, confirm the linked URL actually contains that quote
2. If you cannot access a source to verify, search for the quote + speaker to find an accessible source
3. If a quote cannot be verified on any accessible source, REMOVE IT or REPLACE with a verifiable quote

### Common Errors to Catch:
- Quote attributed to Source A but actually appears in Source B → Fix the link
- Quote is a paraphrase but presented as a direct quote → Either find the exact quote or rephrase
- Quote is real but linked to wrong article from same outlet → Find the correct article URL
- Quote cannot be found anywhere → Remove it entirely

### Verification Checklist:
- [ ] Every quote links to an article that actually contains that quote
- [ ] No quote is linked to a different article that doesn't contain it
- [ ] If a source is inaccessible, an alternative verified source is used
- [ ] Any unverifiable quotes have been removed

**Do not deliver a story with unverified source links. It is better to have fewer quotes than wrong attributions.**

---

Look for stories that have been national news headlines as of today's date. The story in the JSON will be for tomorrow. Show me 10 story options.

### Provide Publish Command ###
After the new story is created in the proper JSON format, Provide me the terminal command to run in the format of "./rws_publish.sh yyyy-mm-dd-story-name.json".
