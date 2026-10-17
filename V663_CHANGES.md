# QuickLead Intel v6.6.3 — Identity Guardrails

## Goal
A surgical stabilization patch for the live v6.6.2 acceptance regressions. No scoring redesign, UI work, architecture rewrite or deliberate speed tuning.

## Identity guardrails
- Protect domain-aligned/canonical brands from being replaced by unrelated testimonial, customer-story or staff names.
- Treat `.com` and bare forms of the same brand as equivalent during identity conflict resolution.
- Reject responsive-menu/navigation concatenations such as `WG About Us Proven Process`.
- Penalize isolated single-word identities that do not align with the domain when stronger primary business evidence is available.
- Preserve legitimate one-word brands when they align with the domain.

## Contact guardrails
- Reject retina/media asset pseudo-emails based on pseudo-domains such as `@2x.mp` and `@2x.webm`, regardless of filename.
- Reject short date/ID-like numeric `tel:` noise when locale evidence is absent, while preserving explicit international and known-local phone formats.

## Regression coverage
Added `backend/test_v663_identity_guardrails.py` for the live failure classes discovered in the v6.6.2 50-site acceptance run, including Zoom/customer-story substitution, Walker Glantz navigation text, isolated staff-name identity, Slack media pseudo-emails, Mailchimp numeric phone noise and preservation of earlier Meck legal-name recovery.

Full backend regression suite: **51 tests passing**.

## Version
Backend/API and frontend package release: `6.6.3`.
