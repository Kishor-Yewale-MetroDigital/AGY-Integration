---
name: github-actions-workflow-hygiene
description: Conventions for authoring or fixing GitHub Actions workflows in this repo (CI, Cloud Run deploy, Cloud SQL power). Use when editing .github/workflows/*, or when fixing Node.js-deprecation warnings, ubuntu-latest migration warnings, or google-github-actions/auth credential errors.
---

# GitHub Actions Workflow Hygiene

## Runners
- Pin `runs-on: ubuntu-24.04` — never `ubuntu-latest` (avoids silent Ubuntu 26 migration).

## Avoid deprecated Node-20 JS actions
Replace with native `run:` steps:
- checkout → `git init . && git remote add origin "https://x-access-token:${{ github.token }}@github.com/${{ github.repository }}.git" && git fetch --depth=1 origin "${{ github.sha }}" && git checkout FETCH_HEAD`
- setup-python → `python3 -m venv .venv && . .venv/bin/activate` (runner ships Python 3)
- setup-node → use the runner's preinstalled Node; `npm install` / `npm ci`
- google-github-actions/auth / setup-gcloud → preinstalled `gcloud` + steps below

## GCP credential preflight (deploy / cloudsql workflows)
1. A preflight step checks secrets and sets an output `mode`:
   - `GCP_SA_KEY` set → `key` → write to a temp file, `gcloud auth activate-service-account --key-file`
   - `GCP_WIF_PROVIDER` + `GCP_CICD_SERVICE_ACCOUNT` set → `wif` → request the OIDC token (`id-token: write` permission) and `gcloud iam workload-identity-pools create-cred-config`, then `gcloud auth login --cred-file`
   - neither → `none` → still run the build (validation) but skip push/deploy with a `::notice::` instead of failing.
2. Gate push/deploy steps with `if: steps.preflight.outputs.mode != 'none'`.

## Before pushing workflow changes
- Run the CI commands locally (see `.agents/rules/github-checkin-before-gcp-deploy.md`) and push all related files in one commit.
- Never bypass org policies (e.g. `run.managed.requireInvokerIam`); report them instead.
