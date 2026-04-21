"""Create Poll + PollOption rows for chapters that gate a following chapter (idempotent)."""

from django.core.management.base import BaseCommand
from django.db import transaction

from stories.models import Chapter, Poll, PollOption, Story


class Command(BaseCommand):
    help = 'Ensures each non-final chapter has a poll with two options (safe to re-run).'

    @transaction.atomic
    def handle(self, *args, **options):
        created_polls = 0
        for chapter in Chapter.objects.select_related('story').order_by('story_id', 'chapter_number'):
            has_next = Chapter.objects.filter(
                story=chapter.story,
                chapter_number=chapter.chapter_number + 1,
            ).exists()
            if not has_next:
                continue
            if Poll.objects.filter(chapter=chapter).exists():
                continue

            poll = Poll.objects.create(
                chapter=chapter,
                chapter_label=f'CHAPTER {chapter.chapter_number}',
                prompt_heading=(
                    f'Will you cross the threshold after “{chapter.title}”? '
                    'The Salon waits for your echo.'
                ),
                souls_footer_note='Souls have stood at this threshold.',
                disclaimer=(
                    'Decisions are permanent. Your echo will ripple through the chapters '
                    'of those who follow.'
                ),
            )
            PollOption.objects.create(
                poll=poll,
                label='THE RADIANT PATH',
                title='Accept the Void',
                description=(
                    'Walk through the veil. Some secrets are only whispered in the '
                    'absolute absence of light.'
                ),
                theme='lavender',
                sort_order=0,
            )
            PollOption.objects.create(
                poll=poll,
                label='THE SAFE ECHO',
                title='Turn Back Now',
                description=(
                    'The warmth of the known is a seductive trap. Survival is its own '
                    'form of storytelling.'
                ),
                theme='peach',
                sort_order=1,
            )
            created_polls += 1

        featured = Story.objects.order_by('id').first()
        if featured and not featured.is_featured:
            featured.is_featured = True
            featured.save(update_fields=['is_featured'])

        self.stdout.write(
            self.style.SUCCESS(f'Done. Created {created_polls} new poll(s).'),
        )
