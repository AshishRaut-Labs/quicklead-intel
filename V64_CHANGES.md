# QuickLead Intel v6.4 changes

Targeted patch only; no wholesale rewrite of `backend/main.py`.

## Identity
- Added explicit page-title identity as a stronger signal than domain guessing.
- Added an SEO-title guard so generic titles like "Best HVAC Services in Dallas" do not beat domain fallback.
- Added title/domain matching logic for compact domains such as `vipairheat.com` vs `VIP Air Conditioning & Heating`.

## Conversion evidence
- Added `conversion_evidence` with:
  - `CONFIRMED_PRESENT` / `RENDER_VERIFY`
  - confirmed-present signals
  - unverified-missing signals
  - render-verification flag
- Missing CTA/form/contact/booking signals from raw HTTP are now treated as unverified rather than confirmed defects.
- Reduced opportunity-score inflation from raw-only negative findings.
- Best sales angle no longer asserts a conversion failure when JavaScript rendering still needs verification.

## Contactability
- Added `static_score` and `verification_required`.
- When no static contact route is found, QuickLead returns `UNVERIFIED` with a neutral score baseline instead of treating the business as unreachable with score 0.
- Prospect decisions stay `VERIFY` when identity/opportunity are meaningful but contact routes need rendered verification.

## Frontend / export
- `NEXT_PUBLIC_API_BASE` is now supported, with the Render URL as production fallback.
- CSV export now includes Contactability Status and Conversion Evidence.

## Version
- Backend API version bumped to `6.4.0` including the health-check endpoint.
