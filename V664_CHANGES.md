# QuickLead Intel v6.6.4 — Publisher Trust Guardrails

## Goal
Final surgical trust patch for the remaining v6.6.3 acceptance-test regressions. No feature expansion.

## Identity
- Added publisher-level evidence separate from ordinary body headings.
- Domain-aligned title, `og:site_name`, application name, header/navigation/logo signals can protect the real site owner.
- Customer/case-study names such as `Capital One` on Zoom cannot replace the publisher when they lack publisher evidence.
- Campaign/content headings such as `BREAKTHROUGHS TO BUSINESS VALUE` cannot replace a domain-aligned publisher such as Wipro.
- Canonical publisher spelling such as `Booking.com` is retained when available.
- Legal/professional identities such as `Tanya L. Stokes, CPA` are protected from generic domain fallback.

## Contact quality
- Bare 7–9 digit `tel:` values that look like dates/IDs/placeholders are rejected before normalization.
- This targets remaining Mailchimp-style numeric noise without changing normal formatted/international phone handling.

## Regression coverage
- Added `backend/test_v664_publisher_trust_guardrails.py`.
- Full regression suite: 58 tests passing.

## Version
Backend/API and frontend package release: `6.6.4`.
