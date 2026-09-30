# QuickLead Intel v6.5 changes

## Goal
v6.5 is a reliability patch focused on the real failures found in the 5-site v6.4 regression batch. It does not add a new product surface or rewrite the backend architecture.

## Phone and country reliability
- Bare local numbers no longer infer an international country merely because their first digits resemble a dial code.
  - `404...` no longer becomes Romania (`+40`).
  - `704...` no longer becomes Russia (`+7`).
  - `817...` no longer becomes an international number by prefix guessing.
- International-country inference now requires an explicit `+` or `00` prefix.
- Bare `91xxxxxxxxxx` strings are no longer treated as explicit India phone evidence.
- Explicit `+91` India numbers continue to work.
- Added strong US address evidence from state abbreviations + ZIP codes and city/state patterns.
- US/Canada phone normalization now requires a plausible 10-digit NANP number (or 11 digits beginning with `1`).
- Long unprefixed digit strings are rejected to avoid phone/address merges such as `40487244552166`.

## Business identity reliability
- Added a visible/title/domain/email consensus guard for structured metadata conflicts.
- If JSON-LD/meta identifies a web agency/platform but the visible site identity disagrees, QuickLead can now prefer the actual site business.
- Regression cases covered:
  - `Sparrow Strategy LLC` -> `Hughes Mechanical and Electrical Contractors`
  - `Mindstorm` -> `Carolina Dental Arts`
- Page-title identity now avoids location-only fragments such as `Arlington, TX`.

## Email quality
- Telemetry/platform implementation addresses are filtered from prospect emails.
- Long hexadecimal Sentry/Wix addresses such as `...@sentry-next.wixpress.com` are no longer considered outreach contacts.

## Regression tests
Added `backend/test_v65_regressions.py` using Python's built-in `unittest`.
The included regression suite covers:
- explicit-vs-bare phone country inference
- US address inference
- US phone normalization
- phone/address merge rejection
- telemetry email filtering
- Hughes agency-name conflict
- Ballantyne agency-name conflict

## Version
Backend API version bumped to `6.5.0`.
