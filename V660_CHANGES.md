# QuickLead Intel v6.6.0 — Buyer Ready

## Goal
v6.6.0 is the buyer-readiness release built from the v6.5.6 production baseline and the 50-site stress test. It keeps the existing architecture and scoring model, but hardens the places that could damage buyer trust during an agency demo.

## Business identity trust
- HTML entities are decoded before names are returned (`&amp;` -> `&`).
- Generic page labels such as `Home Page` and `Landing Page` are rejected as business identities.
- Generic service/location fragments such as `CPA Austin` and `Dentist Matthews` are rejected.
- Sentence/slogan fragments such as `only way we make money` and `Find out what's possible when work connects` are rejected.
- Brand + marketing-title forms such as `Ahrefs—AI Marketing Platform` are normalized back to the brand.
- Existing v6.5/v6.5.6 identity protections remain in place.

## Country and locale confidence
- Added structured JSON-LD `addressCountry` as strong country evidence.
- Multi-region/global sites are detected from mixed hreflang, currency, country and phone signals.
- A single regional support phone no longer makes a global `.com` site look like a high-confidence local business.
- Ambiguous global sites now prefer `Unknown` over a confidently wrong country.
- Strong local US address evidence and strong India evidence continue to work.

## Prospect prioritization
- Global/multi-region sites are deprioritized in the local-SMB prospecting queue.
- They remain visible for research, but cannot casually outrank actionable local businesses because of contactability alone.

## Fetch outcomes and 50-site UX
- Repeated 401/403 responses are classified as `Blocked` / `ACCESS_BLOCKED`, not as a generic scanner failure.
- Obvious access-blocked sites stop retrying sooner when most URL variants refuse automated access.
- Timeout, rate-limit and generic fetch failures receive distinct failure types.
- Bulk CSV includes `Failure Type`.
- Bulk UI shows a `Browser Verify` count and distinguishes blocked sites from true failures.

## Deployment hardening
- Added optional `QUICKLEAD_CORS_ORIGINS` configuration so private deployments can restrict trusted frontend origins without editing source code.

## Buyer-facing polish
- Product metadata and package identity use `QuickLead Intel` / `6.6.0`.
- Replaced the default framework favicon with a QuickLead icon.
- Replaced the generic create-next-app README with product/setup/deployment documentation.
- Added `QUICKLEAD_MASTER_HANDOFF.md` for continuity, testing, deployment and sales handoff.

## Regression coverage
- v6.5 tests retained.
- v6.5.6 tests retained.
- v6.6.0 adds regressions for identity cleanup, HTML entity decoding, global-locale abstention, structured-country evidence, India evidence, blocked-site classification and release version.

## Version
- Backend API and health-check version: `6.6.0`.
- Frontend package version: `6.6.0`.
