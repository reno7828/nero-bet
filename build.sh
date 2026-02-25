#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate

# Création du superuser sécurisée
if [ "$ADMIN_USERNAME" ]; then
  python manage.py createsuperuser \
    --no-input \
    --username "$ADMIN_USERNAME" \
    --email "$ADMIN_EMAIL" || true
fi