# Changelog

## 2026-04-07

### Changed
- Switched production deployment from local Docker build to CI-built images.
- Updated production compose to use prebuilt registry image via `SERVER_IMAGE`.
- Updated `deploy.sh` to pull latest image instead of rebuilding locally.
- Ensured Docker publish workflow runs automatically on every push to `main`.
