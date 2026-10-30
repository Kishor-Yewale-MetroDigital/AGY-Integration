---
trigger: always_on
description: Enforce local testing and GitHub check-in (commit & push) before deploying any code changes to GCP.
---

# Mandatory Local Verification & GitHub Check-In Before GCP Deployment

Every change made to code **MUST** follow this strict sequence:

1. **Test Locally First**: Run local build and automated/browser tests to confirm the change works without regressions.
2. **Check In to GitHub Before Deploying to GCP**: Before executing any GCP deployment (`gcloud run deploy`, `deploy-gcp.ps1`, Cloud Build, or Terraform apply), stage, commit, and push all tested changes to GitHub (`origin/main`) and confirm the working tree is clean (`git status --short`).
3. **Deploy to GCP Only From Checked-In State**: Trigger GCP deployment only after the changes are pushed to GitHub.
