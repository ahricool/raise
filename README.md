# Raise

## Deployment

Use `./deploy.sh` in production to pull the latest code from `main` and force a rebuild of the Docker image.

- `./deploy.sh`: clean local changes, switch to `main`, pull latest remote code, then rebuild and deploy

This avoids the previous behavior where containers could restart from an old image after `docker compose up -d`.
