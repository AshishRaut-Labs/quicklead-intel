# QuickLead Intel v6.6.1 — Final Buyer-Ready Polish

## Why this patch exists
The live 50-site v6.6.0 acceptance test completed all 50 inputs in about 5m56s and correctly classified seven access-blocked sites, but it exposed a few remaining trust issues in identity and global-country handling.

## Identity reliability
- Reject browser/runtime messages such as `JavaScript is disabled`.
- Reject standalone pronouns such as `She` / `He` as business identities.
- Reject generic professional-role titles such as `Tax Consultant` and service/location titles such as `CPA Firm in Austin, TX`.
- Recover explicit legal business names from conservative meta-description prefixes (for example `Meck Noonan & Co., LLC. is ...`).
- Preserve valid names such as Arrowood Dental, Reeves Snyder LLP and Greg Copp & Company, Inc.

## Country confidence
- Structured addresses from `Organization` on globally localized sites no longer automatically create a high-confidence country.
- Local-business structured schemas remain strong country evidence.
- On global product surfaces, QuickLead prefers `Unknown` unless there is genuinely local evidence such as a country-code TLD or local-business schema.

## Regression coverage
- Added v6.6.1 tests for runtime-message identity noise, pronouns, generic professional titles, meta-description legal-name recovery, Arrowood-style title recovery and conservative global-country inference.
- Full backend regression suite: 29 tests passing locally.

## Version
- Backend API and health-check version: `6.6.1`.
- Frontend package version should be bumped with `npm version 6.6.1 --no-git-tag-version` in the existing repo so the already-upgraded Next.js 16.4.0 dependency is preserved.
