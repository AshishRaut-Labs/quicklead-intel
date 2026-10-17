# QuickLead Intel v6.6.6 — Sales Freeze

## Goal
Close the final live contact-sanitation leak without changing product behavior elsewhere.

## Contact quality
- Added a locale-aware guard for ambiguous 7–9 digit phone-like values.
- Unknown/global and US/CA/IN paths reject short formatted IDs/dates even when punctuation bypassed the earlier digit-only noise test.
- Countries that legitimately use short national numbers are not globally disabled.
- Prevents Mailchimp-style `20-01-2026` / `05-005-011` values from becoming exported prospect phones while preserving real +1 support numbers.

## Scope
No scoring, identity, UI, architecture, or performance changes.

## Version
Backend and package version: `6.6.6`.
