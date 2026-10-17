# QuickLead Intel v6.6.5 — Freeze Candidate

## Goal
Close the two remaining targeted trust issues from the v6.6.4 live check, then freeze engineering for sales. No feature expansion.

## Canonical brand trust
- Added a conservative canonical `.com` brand helper.
- It can restore `Brand.com` only when the current identity already matches the scanned `.com` host and the page itself presents that spelling in strong title/site/corporate evidence.
- Prevents generic `.com` appending to ordinary brands.

## Phone hygiene
- Bare 7–9 digit `tel:` values rejected as ambiguous date/ID noise are no longer re-added during the later country-aware normalization pass.
- Preserves explicit international and formatted phone values.

## Prospect queue noise
- Generic rendered-verification rows now require opportunity score >= 40 (previously >= 35) before identity confidence alone can keep them at `VERIFY`.
- This avoids low-opportunity/no-email rows becoming manual review work.

## Regression coverage
- Added `backend/test_v665_freeze_candidate.py`.
- Updated the v6.6.4 version assertion to allow later patch releases.
- Full regression suite: 64 tests.

## Version
- Backend/API version: 6.6.5
- Frontend package version: 6.6.5
