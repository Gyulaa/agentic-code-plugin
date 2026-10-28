---
name: security-check
description: Use only when a change touches security-relevant code - authentication, roles and membership, access rules (database rules, row-level policies), seat limits or subscriptions, invitations, endpoints and their payloads, exports, payments, uploads, secrets, rate limits - when risk_level.py reports a critical change, or when the user asks whether something is safe. A short, technology-independent checklist built on one idea: never trust the client. Reports only real flaws, ranked, each with what an attacker can do and the fix. Not for ordinary UI, copy or refactoring changes.
---

# Security check

One idea carries the whole list: **never trust the client.** A price, an id, a role, a subscription state, a limit or a counter that lives only in the client or in the request body is in the attacker's hands. A check in the client is a convenience for the honest user, not a defence.

## When
- The diff touches authentication, roles or membership, an access rule, a seat or plan limit, an invitation, an endpoint or its payload, an export, a payment, an upload, a secret or a rate limit.
- `risk_level.py` (or your own reading, see `quality-gate`) calls the change critical.
- The user asks "is this safe?".
Skip it for ordinary screens, copy and refactors. If the change also collects new personal data, run `privacy-check` too.

## How
1. **Name the surface:** which of the items below does the diff touch? Check those and nothing else.
2. **Load the matching reference only:** `references/access-control.md` (rules, roles, tenants, limits), `references/server-and-secrets.md` (endpoints, payments, secrets, deployment, input), `references/client-and-mobile.md` (what the client may hold).
3. **Read the code as an attacker would:** for each item, find the place that enforces it, on the server or in the rules, and ask what happens if the request is forged.
4. **Report** (below). Fix nothing until the user picks.
5. **Every rule change gets a test** against an emulator or a test database: one case that must be allowed and, more important, one that must be denied.

## The list
1. **Access rules** (database rules, row-level policies): no rule that is open or only checks "signed in"; ownership and tenant checks; **field-level write protection** so a user cannot rewrite their own role, permissions or subscription fields; child collections and tables have their own rules; the role comes from a signed token or the server, never from a document the user can write.
2. **Roles and membership:** who may invite, remove or change whom; the last owner cannot be removed; a role change takes effect on the server.
3. **Seat limits and subscription** are decided on the server.
4. **Multi-tenant data:** the tenant id is in every document and every query filters on it.
5. **Invitations and bearer tokens** never reach a client that should not hold them.
6. **Endpoints and exports:** authenticate every call; check the caller's right to the resource; do not trust ids, prices or roles in the body; a server-side request to a user-supplied URL is forbidden or filtered (SSRF).
7. **Limits on costly or abusable endpoints** (export, e-mail, an AI call), enforced on the server, with a daily cap; an AI service key never sits in the client.
8. **Secrets** are not in the code or the commit; one that leaked must be **rotated**, deleting the commit is not enough.
9. **Payments:** the server computes the price; a webhook's signature is verified; the subscription state is read fresh where it matters.
10. **Tokens** live in secure storage, not in plain `localStorage` or a settings file.
11. **Input and output:** no string-built queries, output is encoded for where it lands, an upload is checked for type and size.
12. **Deployment:** debug off, CORS narrow, no secret in a source map, security headers set.
13. **Personal data:** a change that collects new data also runs `privacy-check`.

## The report
Real flaws only, ranked **critical, high, medium, low**, the critical first. For each: the file and line, **what an attacker can do with it, concretely** ("any signed-in user can set their own `role` to `owner` by writing to `members/{id}`"), and the fix. No style remarks, no "it would be even better if". If nothing is wrong, say what you checked ("security: access rules and the export endpoint checked, no flaw found"), not that the code is safe.

## Where this comes from
Inspired by the nine categories of `raroque/vibe-security-skill` (MIT: secrets, database security, auth, rate limiting, payments, mobile, AI, deployment, data access) and by the OWASP Top 10 (2025), where broken access control is first and server-side request forgery is now part of it. The wording and the structure here are our own.
