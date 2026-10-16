# QuickLead Intel v6.6.2 — Trust & Contact Quality

## Goal
One final trust-focused reliability pass based on the live 50-site v6.6.1 acceptance batch. No architecture rewrite and no deliberate speed tuning.

## Business identity
- Reject punctuation-wrapped UI/pronoun fragments such as `me.`.
- Reject multi-descriptor SEO identities such as `Austin CPA Accounting Firm`.
- Added conservative visible-copy recovery for repeated/legal/professional business names.
- Strong repeated names can beat weak domain inference, helping older SMB sites with generic titles/H1s.

## Contact quality
- URL-decode email candidates before validation/deduplication.
- Reject retina/media filename artifacts that can look like emails (for example `video-name@2x.mp4`).
- Reject obvious placeholder sequences, short bare IDs/dates and repeated-digit noise from free-text phone extraction.
- Preserve strong `tel:` links and explicit international numbers.

## Regression coverage
Added `backend/test_v662_trust_contact_quality.py` covering identity recovery, SEO-title rejection, pseudo-email filtering, URL-encoded email deduplication, numeric phone noise and valid phone preservation.

## Version
Backend/API and frontend package release: `6.6.2`.
