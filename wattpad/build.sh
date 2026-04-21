#!/usr/bin/env bash
# exit on error
set -o errexit

echo "Installing required Python packages..."
pip install -r requirements.txt

echo "Collecting static files for production..."
python manage.py collectstatic --no-input

echo "Applying database migrations..."
python manage.py migrate

echo "Seeding the database with premium story content (skips if already seeded)..."
python manage.py seed_data

echo "Assigning cover images to stories (safe to re-run)..."
python manage.py assign_covers
