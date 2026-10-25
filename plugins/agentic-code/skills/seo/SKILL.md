---
name: seo
description: Use when building, changing or reviewing a public website that should be found through search - pages, blog posts, landing pages, routes, metadata, sitemaps, robots.txt, structured data, site migrations or domain changes - for classic search (Google, Bing) and AI search (Google AI Overviews and AI Mode, ChatGPT search, Perplexity, Claude, Copilot). Covers indexable server-rendered HTML, AI crawler access, people-first content an answer engine can quote, metadata, schema.org, multilingual and local search, and honest measurement. Not for app screens or pages behind a login.
argument-hint: "[page, site or URL]"
---

# SEO for classic and AI search

There is no separate "AI SEO". Google states that AI Overviews and AI Mode need nothing beyond normal SEO: no special markup, no extra file. Other AI search engines read the same pages, with two technical differences: most AI crawlers do not run JavaScript, and each has its own name in `robots.txt`. So the work is: content written for the reader and structured so a machine can lift an answer from it, behind technical gates that are open. No tricks: since May 2026 Google's spam policies also cover attempts to manipulate AI answers.

Skip this skill for app screens, admin areas, pages behind a login, and staging (staging gets authentication, not just `noindex`).

Files next to this SKILL.md, read when the step needs them:
- `references/technical.md`: rendering per framework, crawl and index controls, the `robots.txt` pattern for AI crawlers, canonicals, migrations, sitemaps, hreflang, Core Web Vitals.
- `references/content.md`: people-first content, structure that answer engines can quote, trust signals, local and multilingual search, AI-written text, what the evidence on AI citations says.
- `references/structured-data.md`: which schema.org types Google still uses, JSON-LD patterns, validation.
- `scripts/seo_check.py`: a check of built pages, run on request.

## 1. Who should find this page, through which search
- The page's job: which searches or questions should bring which visitor, in their words (the awareness level in `${CLAUDE_PLUGIN_ROOT}/skills/design/references/copy.md`).
- One main topic per page. If a page for the topic exists, improve it rather than adding a competitor to it.
- Should it be indexed at all? Thin, duplicate, internal or utility pages (filters, internal search, thank-you pages) get `noindex`.

## 2. Technical gates (`references/technical.md`)
- The content, the links and the metadata are in the HTML the server sends (server rendering, static generation or prerendering). Check with `curl`, not in a browser: what `curl` cannot see, most AI crawlers cannot either.
- One canonical URL per page (https, one host form, consistent trailing slash), `lang` on `<html>`, a unique `<title>` and meta description, one `h1`, `hreflang` when there are languages, a sitemap with accurate `lastmod`, a `robots.txt` that does not block what should be found.
- **Crawler access is the owner's decision; ask.** The sensible default: search crawlers in (Googlebot, Bingbot, `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`), training crawlers (`GPTBot`, `ClaudeBot`, `Google-Extended`, `Applebot-Extended`) as the owner chooses. Check the CDN or firewall too: some block AI crawlers by default whatever `robots.txt` says.
- Performance budget: LCP at most 2.5 s, INP at most 200 ms, CLS at most 0.1.
- `Disallow` in `robots.txt` does not remove a page from the index; `noindex` does, and only if the page can be crawled.

## 3. Content (`references/content.md`)
- **Answer first:** under each heading, the first sentence or two answer the heading's question; the detail follows.
- Headings that match what people actually ask; one topic covered well on one page, not a page per phrasing.
- **Specific and verifiable:** numbers, names, dates, prices, sources, first-hand experience (own photos, own data, how the work is done). This is what both readers and answer engines quote.
- **Who, how, why:** a visible author or publisher with background, an About page and contact details, published and updated dates (updated only when the content really changed).
- Copy follows `${CLAUDE_PLUGIN_ROOT}/skills/design/references/copy.md`: no inflated vocabulary, no empty generalities.
- **AI-written text is fact-checked by a person** before it ships, including the title, description, alt text and structured data. Never mass-produce pages (city by city, keyword by keyword) without real content for each.
- Off-site reputation matters, most of all for AI search, which leans on independent sources: suggest (don't fake) reviews, directory listings, a complete business profile and coverage by others.

## 4. Metadata and structured data (`references/structured-data.md`)
- Title: unique, the topic first, the brand last, about 50 to 60 characters. Meta description: a true summary of the page, about 120 to 160 characters. An Open Graph title, description and image for sharing.
- JSON-LD only for what is visible on the page, and only types that do something (Organization, LocalBusiness, Product, Article, BreadcrumbList, Event and the others in the reference). FAQ and HowTo rich results no longer show. Structured data does not buy AI citations: controlled tests found no effect.
- No `llms.txt` by default: no major AI system has said it uses one. If the user wants it, write it without promising an effect.

## 5. Check
- `python3 "${CLAUDE_SKILL_DIR}/scripts/seo_check.py" <build folder, HTML files or URLs>`: per page the title, description, `lang`, canonical, `h1`, robots meta, `hreflang`, JSON-LD validity, images without `alt` or size, and how much text is in the HTML; across pages duplicate titles and descriptions; `robots.txt` per known crawler; the sitemap. Run it on request or before a release; it checks what is machine-checkable, not whether the content is good.
- Then what needs the user's accounts: Google Search Console (URL inspection, indexing), the Rich Results Test, PageSpeed Insights for real-user data, Bing Webmaster Tools (including its AI performance report).
- Say what was checked and what can only be measured after release.

## 6. Measurement and honest expectations
- Google reports AI Overviews and AI Mode traffic inside the normal Search Console "Web" numbers; Bing Webmaster Tools shows Copilot citations. Clicks from AI answers often arrive without a referrer and show as "Direct": an analytics channel group with a regex for the AI hosts catches part of them. Analytics and cookies go through `privacy-check`.
- AI summaries reduce clicks (Pew, 2025: 8% of visits clicked a result with a summary present, 15% without). Being named and cited is part of the value; give the visitor a reason to come through (a tool, a calculator, own data, a way to get in touch).
- Results take weeks to months; nobody can guarantee a ranking or a citation.

## Never
Hidden text, cloaking, keyword stuffing, doorway pages, mass-produced pages without value, structured data for content that is not on the page, invented reviews or ratings, bought links, AI personas presented as authors.
