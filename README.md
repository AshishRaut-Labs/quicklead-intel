# QuickLead Intel

QuickLead Intel is an internal prospect-intelligence system for web, SEO and digital agencies. It turns a list of business websites into a ranked prospecting queue with identity, contactability, website/conversion signals, sales opportunity, recommended service, localized project value and outreach context.

**Current release:** v6.6.6 — Sales Freeze

## What it does

- Single-site and bulk scanning (up to 50 URLs per request)
- Business-name extraction with confidence and source tracking
- Phone/email/social extraction and contactability scoring
- Website health, SEO, conversion and technical signals
- Prospect score and `CONTACT` / `VERIFY` / `SKIP` decision
- Best sales angle, recommended service and project-value estimate
- Country/currency inference with confidence and conservative global-site handling
- CSV export for agency workflows
- Website-preview generation endpoint
- Buyer-friendly blocked-site classification for sites that refuse automated access

## Architecture

- **Frontend:** Next.js 16 + React 19 + TypeScript + Tailwind CSS
- **Backend:** FastAPI + httpx + BeautifulSoup
- **Production backend:** Render-compatible FastAPI service
- **Frontend API selection:** `NEXT_PUBLIC_API_BASE`, with the configured production fallback in `app/page.tsx`

## Project structure

```text
app/                         Next.js UI
backend/main.py              FastAPI scanner + intelligence engine
backend/test_v65_regressions.py
backend/test_v656_identity_regressions.py
backend/test_v660_buyer_ready.py
backend/test_v661_final_polish.py
backend/test_v662_trust_contact_quality.py
backend/test_v663_identity_guardrails.py
backend/test_v664_publisher_trust_guardrails.py
backend/test_v665_freeze_candidate.py
V64_CHANGES.md
V65_CHANGES.md
V656_CHANGES.md
V660_CHANGES.md
V661_CHANGES.md
V662_CHANGES.md
V663_CHANGES.md
V664_CHANGES.md
V665_CHANGES.md
QUICKLEAD_MASTER_HANDOFF.md
```

## Local setup

### Frontend

```bash
npm install
npm run dev
```

Production check:

```bash
npm run build
npm run lint
```

### Backend

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --reload
```

Run the regression suite:

```bash
python -m pytest \
  backend/test_v65_regressions.py \
  backend/test_v656_identity_regressions.py \
  backend/test_v660_buyer_ready.py \
  backend/test_v661_final_polish.py \
  backend/test_v662_trust_contact_quality.py \
  backend/test_v663_identity_guardrails.py \
  backend/test_v664_publisher_trust_guardrails.py \
  backend/test_v665_freeze_candidate.py \
  -q
```

## Environment

The frontend supports:

```text
NEXT_PUBLIC_API_BASE=https://your-backend.example.com
```

The backend supports an optional CORS allowlist for private deployments:

```text
QUICKLEAD_CORS_ORIGINS=https://your-dashboard.example.com
```

Use a comma-separated list for multiple trusted frontend origins. The default remains `*` for development/demo compatibility. Do not commit `.env.local` or production secrets.

## API

### Health

```text
GET /
```

Returns service status and release version.

### Single scan

```text
GET /api/scan?url=https://example.com
```

### Bulk scan

```text
POST /api/bulk-scan
Content-Type: application/json

[
  "https://example-one.com",
  "https://example-two.com"
]
```

Maximum: 50 unique URLs per request.

### Website preview

```text
POST /api/generate-website
```

## Interpreting outcomes

- `Success`: the page was fetched and analyzed.
- `Blocked` / `ACCESS_BLOCKED`: the site refused automated access; browser verification is required. This is not treated as a scanner crash.
- `Failed` / `TIMEOUT`: the site did not respond within the network timeout.
- `Failed` / `FETCH_FAILED`: another bounded fetch failure occurred.

QuickLead deliberately prefers `Unknown` or `VERIFY` over high-confidence guesses when country, identity or rendered conversion evidence is ambiguous.

## v6.6.3 identity guardrails

The final stabilization patch makes identity replacement conservative: domain-aligned/canonical brands are protected from unrelated customer, testimonial, staff or navigation text. It also rejects responsive-menu identity fragments, retina/media pseudo-emails and short date/ID-like phone noise when locale evidence is absent.

The regression suite includes the live failures found in the v6.6.2 acceptance batch, including Zoom/Capital One, Walker Glantz navigation text, a staff first-name false identity, Slack media pseudo-emails and Mailchimp numeric noise.

## Product positioning

QuickLead is intended to be sold as a **private agency prospect-intelligence system**, not as an “AI scanner.” The buyer outcome is faster prospect research and a clearer reason to contact each business.

For a private commercial deployment, add deployment-level access control (for example provider/private-network access, Cloudflare Access, or equivalent) rather than exposing an unrestricted internal tool publicly.

## Release discipline

`backend/main.py` is the core engine. Make targeted, regression-tested changes only. Do not rewrite it wholesale.


## v6.6.4 publisher trust guardrails

- Adds a final domain-aligned publisher guard so customer/case-study brands cannot replace the site owner.
- Separates publisher evidence (title/site metadata/header/logo) from ordinary H1/H2 content.
- Preserves canonical publisher spelling such as `Booking.com` when available.
- Rejects bare short numeric `tel:` IDs/dates before they enter the phone list.
- No scoring, UI, concurrency, or architecture changes.


## v6.6.5 freeze candidate

- Restores canonical `.com` brand spelling only when the page itself gives strong title/site/corporate evidence; this fixes `Booking` → `Booking.com` without globally appending `.com` to ordinary brands.
- Prevents bare 7–9 digit `tel:` values from being reintroduced during country-aware phone normalization after they were already rejected as ambiguous date/ID noise.
- Raises the generic rendered-verification `VERIFY` threshold from 35 to 40 opportunity points, so low-opportunity/no-email rows do not become review work solely because identity confidence is high.
- No UI, architecture, concurrency, pricing, or scoring-model redesign. This is the sales freeze candidate.


## v6.6.6 sales freeze

Final contact-sanitation hotfix. Ambiguous 7–9 digit values are rejected on Unknown/US/CA/IN locale paths even when punctuation let them bypass early extraction. This closes the Mailchimp-style date/ID leak without globally disabling legitimate short national numbers. No scoring, UI, architecture or identity changes.
