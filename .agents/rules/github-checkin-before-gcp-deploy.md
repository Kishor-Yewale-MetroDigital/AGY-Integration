---
trigger: always_on
description: Enforce local testing and GitHub check-in (commit & push) before deploying any code changes to GCP.
---

# Mandatory Local Verification & GitHub Check-In Before GCP Deployment

Every change made to code **MUST** follow this strict sequence:

1. **Test Locally First**: Run local build and automated/browser tests to confirm the change works without regressions.
   a. **Mirror CI exactly** — run the same commands as `.github/workflows/ci.yml`, not a subset:
      - Backend (`backend/`): `ruff check app tests alembic` and `pytest`
      - Frontend (`frontend/`): `npx tsc --noEmit`, `npm test -- --run`, `npm run build`
   b. Never skip a failing local step. If `vite`/`vitest` fails with `EPERM ... realpath` (OneDrive + sandbox), re-run the same command outside the sandbox instead of skipping it.
   c. When changing UI text, update or verify the matching test assertions (e.g. `getByText`) in the same change.
   d. **Exercise interactive forms & CTAs, not just static navigation**: Frontend tests and browser verification must submit interactive forms and CTA buttons across every module (`+ Add Rule`, `+ Add User & Assign Rights`, `Grant Delegation`, `Create & Submit Request`, `Save as Draft`, role/status toggles) and verify `role="status"` confirmation banners with zero `role="alert"` errors.
   e. **Enforce idempotency on pre-populated default forms & `UNIQUE` constraints**: Any UI form pre-populated with default values that map to `UNIQUE` database columns must be idempotent on repeated submissions (and tested by submitting twice) so clicking submit with default values never triggers a `500 IntegrityError`.
   f. **Complete RBAC & admin lifecycle protection**: Administrative endpoints and UI state must prevent locking out the last active `ADMIN`, automatically switch the acting user if the active session user is suspended, and resolve actors by active role rather than hardcoded seed IDs.
2. **Check In to GitHub Before Deploying to GCP**: Before executing any GCP deployment (`gcloud run deploy`, `deploy-gcp.ps1`, Cloud Build, or Terraform apply), stage, commit, and push all tested changes to GitHub (`origin/main`) and confirm the working tree is clean (`git status --short`).
   a. **Atomic pushes** — push all interdependent files in a single commit so CI never runs on a half-pushed state.
   b. Prefer `git push origin main`. If files are pushed via the GitHub API/MCP instead, re-sync afterwards with `git fetch origin main` + `git reset --mixed origin/main`.
   c. **Never hand-edit `.git` refs** (e.g. `refs/remotes/origin/main`) or otherwise fake sync state. Local `HEAD` must genuinely equal `origin/main`.
3. **Deploy to GCP Only From Checked-In State**: Trigger GCP deployment only after the changes are pushed to GitHub.
   a. After pushing, confirm the GitHub Actions CI run for that commit is green before deploying.
