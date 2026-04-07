# Raise

## Deployment

Docker images are built by GitHub Actions on every push to `main` and published to GHCR.

- `./deploy.sh`: clean local changes, switch to `main`, pull latest remote code, pull latest prebuilt image, then deploy
- Set `SERVER_IMAGE` in `.env` to override the default image (`ghcr.io/ahricool/raise:latest`)

This avoids local rebuild drift and ensures production containers run the image built by CI.
