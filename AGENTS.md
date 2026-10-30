# Mandatory Local Verification & GitHub Check-In Before GCP Deployment Rule

Every code change made in this repository **MUST** follow this strict release lifecycle before any deployment to Google Cloud Platform (GCP):

1. **Local Testing & Verification First**
   - All backend and frontend changes must be built and tested locally (`pytest`, `npm run build`, and end-to-end verification against the local server) before initiating any cloud deployment.
   - Do not proceed to GitHub check-in or GCP deployment if local tests or builds fail.

2. **Mandatory GitHub Check-In Before GCP Deployment**
   - Once changes are verified locally, every modified or newly created source file **MUST** be committed and pushed to the GitHub repository (`https://github.com/Kishor-Yewale-MetroDigital/AGY-Integration.git`, branch `main`) **before** running `gcloud run deploy` or `deploy-gcp.ps1`.
   - Verify that `git status --porcelain` is clean and `git push origin main` has succeeded prior to triggering a GCP deployment.
   - Never deploy uncommitted or unpushed local code directly to GCP.
