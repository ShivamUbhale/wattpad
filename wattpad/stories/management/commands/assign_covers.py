"""
Management command: assign_covers
Assigns cover images to stories that are missing them.
Safe to run at every deploy (idempotent).
"""
import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from stories.models import Story

COVER_MAP = {
    'Neon Horizon':                  'scifi.png',
    'Whispers of the Ancestor Tree': 'fantasy.png',
    'The Midnight Cipher':           'mystery.png',
    'Beyond the Golden Keep':        'adventure.png',
}

class Command(BaseCommand):
    help = 'Assigns cover images to stories that are missing them. Safe to re-run.'

    def handle(self, *args, **options):
        static_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'story_covers')
        updated = 0

        for title, filename in COVER_MAP.items():
            try:
                story = Story.objects.get(title=title)
            except Story.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Story not found: {title}'))
                continue

            if story.cover_image:
                self.stdout.write(f'  ✓ {title} already has a cover image.')
                continue

            src = os.path.join(static_dir, filename)
            if not os.path.exists(src):
                self.stdout.write(self.style.ERROR(f'  ✗ Source image not found: {src}'))
                continue

            with open(src, 'rb') as f:
                story.cover_image.save(filename, File(f), save=True)
            self.stdout.write(self.style.SUCCESS(f'  ✓ Assigned cover to: {title}'))
            updated += 1

        self.stdout.write(self.style.SUCCESS(f'Done. {updated} cover(s) assigned.'))
