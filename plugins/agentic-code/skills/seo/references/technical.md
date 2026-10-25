# Technical SEO

## Contents
- Rendering per framework
- Crawl and index controls
- robots.txt and AI crawlers
- URLs, canonicals and redirects
- Sitemaps and change signals
- Multilingual sites
- Links, images and video
- Core Web Vitals

## Rendering per framework
Googlebot renders JavaScript; the major AI crawlers (OpenAI's, Anthropic's, Perplexity's and others) fetch it but do not run it. Content, links and metadata must be in the server's HTML.
| Stack | What to do |
|---|---|
| Next.js (App Router) | server components by default; keep content out of `"use client"` components; `generateMetadata` or `metadata` per route; `app/sitemap.ts` and `app/robots.ts` |
| Nuxt | server rendering by default; `useSeoMeta` per page; prerender static routes |
| SvelteKit | server rendering by default; `export const prerender = true` for static pages; `<svelte:head>` for metadata |
| Astro | static by default, ideal for content; islands only for interactive parts |
| Remix / React Router (framework mode) | server rendering; `meta` export per route |
| Angular | `@angular/ssr` for server rendering or prerendering |
| Vite or other client-only single-page apps | the HTML is empty until JavaScript runs: prerender the public routes, or move content pages to a static or server-rendered site |
| Flutter web | output is not indexable text: build public content in HTML (or a DOM-based Dart framework) and keep the app in Flutter |
| WordPress and other CMSs | server-rendered; check that the theme or page builder emits real headings and text, and that the SEO plugin's sitemap and canonicals are right |
Check: `curl -sL <url> | grep -c "<a word from the page body>"`; zero means crawlers that do not run JavaScript see nothing.

## Crawl and index controls
- `<meta name="robots" content="noindex">` (or the `X-Robots-Tag: noindex` header for PDFs and other files) removes a page from the index. The page must stay crawlable for the tag to be seen.
- `robots.txt` `Disallow` stops crawling, not indexing: a disallowed URL can still appear, without a snippet.
- Limit what search and AI answers show: `nosnippet`, `max-snippet:<n>`, `data-nosnippet` on an element.
- Never block the CSS and JavaScript Googlebot needs to render.
- Status codes: 404 or 410 for gone pages (not a 200 "not found" page, a soft 404); 301 for moved; 503 with `Retry-After` for maintenance.
- Staging and previews: password or IP protection; `noindex` alone leaks.

## robots.txt and AI crawlers
Search and training are separate crawlers. Blocking a search crawler removes the site from that engine's answers; blocking a training crawler does not.
| Company | Search or answers | Training | User-triggered fetches |
|---|---|---|---|
| Google | `Googlebot` (Search, including AI Overviews and AI Mode) | `Google-Extended` (Gemini training and grounding outside Search) | |
| Microsoft | `Bingbot` (Bing and Copilot) | | |
| OpenAI | `OAI-SearchBot` (ChatGPT search) | `GPTBot` | `ChatGPT-User` (robots.txt may not apply) |
| Anthropic | `Claude-SearchBot` | `ClaudeBot` | `Claude-User` |
| Perplexity | `PerplexityBot` | | `Perplexity-User` |
| Apple | `Applebot` | `Applebot-Extended` | |
A starting point when the owner wants to be found but not used for training (the owner decides):
```
User-agent: GPTBot
User-agent: ClaudeBot
User-agent: Google-Extended
User-agent: Applebot-Extended
Disallow: /

User-agent: *
Disallow: /admin/
Allow: /

Sitemap: https://example.com/sitemap.xml
```
Then check the CDN or firewall: some providers (Cloudflare among them) block AI crawlers by default on new sites, so the bots never reach `robots.txt`. Changes take from about a day (OpenAI) to weeks.

## URLs, canonicals and redirects
- Short, readable, lowercase, hyphenated URLs in the page's language; no session IDs or tracking parameters in internal links.
- `<link rel="canonical" href="<absolute URL>">` on every indexable page, pointing to itself or to the original of a duplicate; one host form (with or without `www`), https, a consistent trailing slash.
- **Migrations and domain changes:** map every old URL to its new one, 301 redirect each (no redirect chains, no mass redirect to the home page), keep the redirects at least a year, update internal links, canonicals, hreflang and the sitemap, and use Search Console's change of address tool for a new domain. Compare indexed pages and traffic before and after.

## Sitemaps and change signals
- An XML sitemap with only canonical, indexable URLs and an accurate `lastmod` (Google ignores `priority` and `changefreq`). Reference it in `robots.txt` and submit it in Search Console and Bing Webmaster Tools.
- IndexNow (Bing, Yandex and others) notifies engines of changes at once; Microsoft recommends it for freshness. Many CMSs and CDNs offer it built in.

## Multilingual sites
- One URL per language version (`/hu/`, `/en/`, or subdomains); never switch language by cookie or IP on the same URL.
- `hreflang` annotations on every version, listing every version including itself, reciprocal, plus `x-default`; language codes such as `hu`, `en`, `de-AT`.
- Translate the slugs, the metadata and the alt text too, and localise rather than translate: people search with different words in each language.

## Links, images and video
- Crawlable links are `<a href="...">` with descriptive anchor text; a link only in an `onclick` handler does not count. Every important page is reachable through links, ideally within three clicks of the home page; breadcrumbs help.
- Images: descriptive file names and `alt`, `width` and `height`, modern formats, `srcset`; the hero image not lazy-loaded.
- Video: a page per important video with a title, description and transcript; `VideoObject` structured data.

## Core Web Vitals
Good at the 75th percentile of real users: LCP at most 2.5 s, INP at most 200 ms, CLS at most 0.1. They are a ranking signal of modest weight and matter more to users than to rankings. The usual levers: a fast server response and caching, the LCP image prioritised (`fetchpriority="high"`) and properly sized, fonts self-hosted with `font-display: swap`, less JavaScript on the main thread (split long tasks, defer third-party scripts), and reserved space for images, ads and embeds.
