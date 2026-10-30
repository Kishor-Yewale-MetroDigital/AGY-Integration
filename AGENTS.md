# Mandatory Local Verification & GitHub Check-In Before GCP Deployment Rule

Every code change made in this repository **MUST** follow this strict release lifecycle before any deployment to Google Cloud Platform (GCP):

1. **Local Testing & Verification First**
   - All backend and frontend changes must be built and tested locally (`pytest`, `npm run build`, and end-to-end verification against the local server) before initiating any cloud deployment.
   - Do not proceed to GitHub check-in or GCP deployment if local tests or builds fail.
   - **Mirror CI exactly** — run the same commands as `.github/workflows/ci.yml`, not a subset:
     - Backend (`backend/`): `ruff check app tests alembic` and `pytest`
     - Frontend (`frontend/`): `npx tsc --noEmit`, `npm test -- --run`, `npm run build`
   - Never skip a failing local step. If `vite`/`vitest` fails with `EPERM ... realpath` (OneDrive + sandbox), re-run the same command outside the sandbox instead of skipping it.
   - When changing UI text, update or verify the matching test assertions (e.g. `getByText`) in the same change.

2. **Mandatory GitHub Check-In Before GCP Deployment**
   - Once changes are verified locally, every modified or newly created source file **MUST** be committed and pushed to the GitHub repository (`https://github.com/Kishor-Yewale-MetroDigital/AGY-Integration.git`, branch `main`) **before** running `gcloud run deploy` or `deploy-gcp.ps1`.
   - Verify that `git status --porcelain` is clean and `git push origin main` has succeeded prior to triggering a GCP deployment.
   - Never deploy uncommitted or unpushed local code directly to GCP.
   - **Atomic pushes** — push all interdependent files in a single commit so CI never runs on a half-pushed state.
   - Prefer `git push origin main`. If files are pushed via the GitHub API/MCP instead, re-sync afterwards with `git fetch origin main` + `git reset --mixed origin/main`.
   - **Never hand-edit `.git` refs** (e.g. `refs/remotes/origin/main`) or otherwise fake sync state. Local `HEAD` must genuinely equal `origin/main`.

3. **Deploy Only After CI Is Green**
   - After pushing, confirm the GitHub Actions CI run for that commit is green before deploying.
