# QuickLead Intel — Master Handoff

## Current state

- Release: **v6.6.3 Identity Guardrails**
- Core backend: `backend/main.py`
- Frontend: `app/page.tsx`
- Bulk limit: 50 unique URLs
- Main workflow: Find leads -> scan -> rank -> verify -> outreach / demo -> close
- Product direction: sell QuickLead itself as a private agency prospect-intelligence system.

## Commercial positioning

Do not pitch “an AI scanner.” Pitch an internal sales system that helps an agency:

1. Analyze prospect websites in bulk.
2. Decide which businesses are worth contacting.
3. See why a prospect may have a website/conversion opportunity.
4. Find public contact routes when available.
5. Export a ranked sales queue with context.

The system is strongest as a **private deployment / agency license**. Source-code transfer and exclusive IP transfer are separate, higher-value deal structures.

## v6.6 buyer-readiness decisions

The 50-site production stress test established that the max batch path works end-to-end, but exposed four trust issues that v6.6 addresses:

- Generic/slogan business identities.
- HTML entities leaking into names.
- Global sites receiving overconfident local-country guesses.
- Access-blocked sites looking like generic scanner failures.

v6.6 intentionally prefers abstention (`Unknown`, `VERIFY`, `Blocked`) to confident bad data.

## Acceptance gates

Before a sales demo or deployment:

```text
python -m py_compile backend/main.py
python -m pytest backend/test_v65_regressions.py backend/test_v656_identity_regressions.py backend/test_v660_buyer_ready.py backend/test_v661_final_polish.py backend/test_v662_trust_contact_quality.py backend/test_v663_identity_guardrails.py -q
npm install
npm run lint
npm run build
```

Expected backend release:

```text
6.6.3
```

Then verify the deployed health endpoint and run a controlled 50-site batch.

## Real-world test strategy

Use two separate batches:

### 1. Stress / resilience batch
Mix protected large sites with ordinary sites to verify:
- 50 inputs accepted
- all inputs accounted for
- blocked sites classified as `Blocked`
- no crash / missing rows
- CSV export completes

### 2. Buyer-value batch
Use 50 real SMB prospects in agency-relevant niches:
- HVAC / home services
- dental / clinics
- law firms
- accounting / CPA
- contractors

Judge:
- identity accuracy
- country confidence
- contact accuracy
- opportunity ranking
- truthfulness of the sales angle
- usefulness of `CONTACT` / `VERIFY` / `SKIP`

Do not tune scoring around Microsoft/Nike/Stripe-style brands; the commercial acceptance batch must look like an agency's actual prospect list.

## Known operating principle

Raw HTTP scanning cannot reliably prove the absence of JavaScript-rendered CTAs/forms. QuickLead therefore uses render-verification states rather than asserting unverified conversion defects. Preserve this behavior.

## Deployment

Backend endpoints:

```text
GET  /
GET  /api/scan
POST /api/bulk-scan
POST /api/generate-website
```

Frontend reads `NEXT_PUBLIC_API_BASE` when supplied.

For a paid private deployment, do not rely on obscurity. Put the deployment behind appropriate access control at the hosting/network layer or add a server-side authentication layer before exposing it to an external team.

## Change policy

- Do not rewrite `backend/main.py` wholesale.
- Make minimum targeted edits.
- Add a regression test for every discovered false positive / false confidence pattern.
- Prefer `Unknown` over confident misinformation.
- Keep sales intelligence evidence-based; do not fabricate contact details, reviews, deficiencies or conversion failures.

## Next commercial steps after v6.6 deployment

1. Run the real 50-SMB buyer-value batch.
2. Manually verify the top 10.
3. Build a controlled five-minute demo using pre-tested prospects.
4. Prepare a one-page private-deployment offer.
5. Build a small list of qualified web/SEO/digital-agency owners.
6. Begin calls/demos only after the buyer-value batch passes.


## v6.6.2 trust/contact notes

- Reject punctuation-wrapped UI/pronoun identities such as `me.`.
- Reject multi-descriptor SEO identities such as `Austin CPA Accounting Firm`.
- Recover repeated/legal/professional business identities from visible body/footer copy before accepting weak domain guesses.
- Decode URL-encoded email candidates and filter retina/media asset pseudo-emails.
- Filter obvious date/ID/placeholder numeric noise from free-text phone extraction while preserving `tel:` and explicit international numbers.
- Acceptance target: same 50-site live batch with no regression in BLOCKED handling or batch stability.

## v6.6.3 identity-guardrail notes

- Protect domain-aligned/canonical identities from unrelated testimonial or customer-story names.
- Treat `.com` and bare forms of the same brand as equivalent for conflict resolution (for example, `Booking.com` vs `Booking`).
- Reject responsive-navigation concatenations such as `WG About Us Proven Process`.
- Penalize isolated single-word names that do not align with the domain when a stronger primary identity exists.
- Reject retina/media pseudo-email domains such as `@2x.webm`, `@2x.mp`, and related asset extensions.
- Reject short date/ID-like numeric `tel:` noise when locale evidence is absent while preserving explicit international and known-local phone formats.
- Regression suite: **51 tests** across v6.5 through v6.6.3.

## Engineering freeze gate

After v6.6.3 is deployed, run the same 50-site acceptance batch once. If the known identity/contact regressions are gone and no new severe regression appears, freeze engineering and move to the buyer demo and sales workflow. Do not add features before sales.
