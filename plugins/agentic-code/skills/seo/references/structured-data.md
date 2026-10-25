# Structured data

## Contents
- Rules
- Types Google uses, and retired ones
- JSON-LD patterns
- Validation

## Rules
- JSON-LD in a `<script type="application/ld+json">`, server-rendered. Several entities can share one `@graph`.
- Mark up only what the page shows. Prices, ratings, opening hours and authors must match the visible text.
- Ratings and reviews only from real reviews shown on the page; a business may not mark up reviews of itself as rich results.
- What it is for: rich results in Google, and an unambiguous description of the entity (who the organisation is, which profiles are its own). It is not a lever for AI citations.

## Types Google uses, and retired ones
- **In Google's search gallery:** Article, Breadcrumb, Carousel, Course list, Dataset, Discussion forum, Education Q&A, Employer aggregate rating, Event, Image metadata, Job posting, Local business, Math solver, Movie, Organization, Product (including merchant listings), Profile page, Q&A, Recipe, Review snippet, Software app, Speakable, Subscription and paywalled content, Vacation rental, Video.
- **Retired as rich results:** HowTo; FAQ (no longer shown since May 2026); Course Info, Claim Review, Estimated Salary, Learning Video, Special Announcement, Vehicle Listing (2025); Practice problem. Existing markup does no harm but shows nothing. Other engines may still read it.
- Check the current gallery before adding a type; the list changes.

## JSON-LD patterns
Organization and WebSite (home page; `WebSite` gives Google the site name):
```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "Organization",
      "@id": "https://example.com/#org",
      "name": "Example Ltd",
      "url": "https://example.com/",
      "logo": "https://example.com/logo.png",
      "sameAs": ["https://www.linkedin.com/company/example"]
    },
    {
      "@type": "WebSite",
      "@id": "https://example.com/#website",
      "name": "Example",
      "url": "https://example.com/",
      "publisher": {"@id": "https://example.com/#org"}
    }
  ]
}
```
LocalBusiness (use the most specific subtype, for example `Plumber`, `Dentist`, `Restaurant`):
```json
{
  "@context": "https://schema.org",
  "@type": "Plumber",
  "name": "Example Plumbing",
  "url": "https://example.com/",
  "telephone": "+36 1 234 5678",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Example utca 1.",
    "addressLocality": "Budapest",
    "postalCode": "1011",
    "addressCountry": "HU"
  },
  "openingHoursSpecification": [{
    "@type": "OpeningHoursSpecification",
    "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "opens": "08:00",
    "closes": "17:00"
  }]
}
```
Product with an offer:
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Example trail running shoe",
  "image": "https://example.com/shoe.jpg",
  "description": "A cushioned trail running shoe with a 6 mm drop.",
  "offers": {
    "@type": "Offer",
    "price": "39990",
    "priceCurrency": "HUF",
    "availability": "https://schema.org/InStock",
    "url": "https://example.com/shoe"
  }
}
```
Article:
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "How to descale a kettle",
  "image": "https://example.com/kettle.jpg",
  "datePublished": "2026-06-01",
  "dateModified": "2026-07-15",
  "author": {"@type": "Person", "name": "[author name]", "url": "https://example.com/team/author"}
}
```
BreadcrumbList:
```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {"@type": "ListItem", "position": 1, "name": "Guides", "item": "https://example.com/guides"},
    {"@type": "ListItem", "position": 2, "name": "Kitchen", "item": "https://example.com/guides/kitchen"}
  ]
}
```

## Validation
- `seo_check.py` checks that every JSON-LD block parses and names a `@type`.
- Google's Rich Results Test (what Google can show) and the Schema Markup Validator at validator.schema.org (the vocabulary), then Search Console's enhancement reports after release.
