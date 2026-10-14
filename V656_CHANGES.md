# QuickLead Intel v6.5.6 changes

## Goal
v6.5.6 is a small identity-hygiene and shipping-quality patch on top of v6.5.5. It does not change the product architecture, scoring model, network behavior, or sales workflow.

## Business identity hygiene
- Rejects `JavaScript` as a standalone business identity.
- Rejects generic product/category labels such as `Website Builder`.
- Rejects marketing titles such as `Free DPDP Compliance Scanner for Indian Websites`.
- Rejects multi-sentence slogan/title combinations such as `Nike. Just Do It. Nike.com`.
- Preserves known legitimate names covered by regression tests.

## Frontend shipping cleanup
- Replaces the default Create Next App browser metadata with QuickLead Intel metadata.

## Regression tests
- Added `backend/test_v656_identity_regressions.py`.
- Existing v6.5 regression suite remains unchanged.

## Version
- Backend API and health-check version bumped to `6.5.6`.
