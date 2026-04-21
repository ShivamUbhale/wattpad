import os
from django.core.management.base import BaseCommand
from django.core.files import File
from django.conf import settings
from stories.models import Genre, Story, Chapter, Question, Answer
from users.models import CustomUser

class Command(BaseCommand):
    help = 'Seeds the database with premium stories. Safe to re-run (idempotent).'

    def handle(self, *args, **options):
        # Only seed if no genres exist (avoid double-seeding in production)
        if Genre.objects.exists():
            self.stdout.write(self.style.WARNING('Database already seeded. Skipping.'))
            return

        self.stdout.write("Seeding genres...")
        scifi,     _ = Genre.objects.get_or_create(name="Science Fiction",  defaults={'description': "Neon-lit futures and cosmic frontiers."})
        fantasy,   _ = Genre.objects.get_or_create(name="Fantasy",          defaults={'description': "Ethereal magic, ancient myths, and noble quests."})
        mystery,   _ = Genre.objects.get_or_create(name="Mystery Noir",     defaults={'description': "Shadows, clues, and twisting narratives."})
        adventure, _ = Genre.objects.get_or_create(name="Epic Adventure",   defaults={'description': "Vast uncharted worlds and monumental journeys."})

        # Superuser
        user, created = CustomUser.objects.get_or_create(username="admin", email="admin@example.com")
        if created:
            user.set_password("password")
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write("Created Superuser: admin / password")

        def assign_cover(story, filename):
            """Assign a cover image from static source to the story if not already set."""
            if story.cover_image:
                return
            src = os.path.join(settings.BASE_DIR, 'static', 'images', 'story_covers', filename)
            if os.path.exists(src):
                with open(src, 'rb') as f:
                    story.cover_image.save(filename, File(f), save=True)

        # ------- STORY 1: SCI-FI -------
        story_scifi, _ = Story.objects.get_or_create(
            title="Neon Horizon",
            defaults={
                'description': "In the year 2142, the megacity of Neoterra thrives under corporate rule. When a rogue hacker discovers a hidden directive coded into the city's power grid, the race for survival begins.",
                'genre': scifi
            }
        )
        assign_cover(story_scifi, 'scifi.png')
        if not story_scifi.chapters.exists():
            c1 = Chapter.objects.create(story=story_scifi, chapter_number=1, title="The Glitch",
                content="The rain never stopped in Neoterra. It just washed the neon lights into a blurred smear on the pavement. I was jacking out of the core network when I saw it. A single line of anomalous code. A glitch that wasn't supposed to be there.")
            q1 = Question.objects.create(chapter=c1, question_text="What was the weather like in Neoterra?")
            Answer.objects.create(question=q1, answer_text="Constant rain.", is_correct=True)
            Answer.objects.create(question=q1, answer_text="Bright and sunny.", is_correct=False)
            Answer.objects.create(question=q1, answer_text="Snow storms.", is_correct=False)

            c2 = Chapter.objects.create(story=story_scifi, chapter_number=2, title="Alleyway Encounter",
                content="Footsteps echoed down the narrow corridor. The corporate agents were closing in. I drew my sidearm, pressed my back against the cold wall, and steadied my breath. One shot. One chance to get out of Neoterra alive.")
            q2 = Question.objects.create(chapter=c2, question_text="What did the protagonist draw in the alleyway?")
            Answer.objects.create(question=q2, answer_text="A sword.", is_correct=False)
            Answer.objects.create(question=q2, answer_text="A sidearm.", is_correct=True)
            Answer.objects.create(question=q2, answer_text="A detonator.", is_correct=False)

            c3 = Chapter.objects.create(story=story_scifi, chapter_number=3, title="The Core",
                content="The server room glowed electric-blue. Thousands of cooling fans hummed in unison. I plugged in and dove into the data stream. The hidden directive was there — a failsafe to wipe every human living in Sector 7.")
            q3 = Question.objects.create(chapter=c3, question_text="What was the hidden directive designed to do?")
            Answer.objects.create(question=q3, answer_text="Upgrade the power grid.", is_correct=False)
            Answer.objects.create(question=q3, answer_text="Wipe every human in Sector 7.", is_correct=True)
            Answer.objects.create(question=q3, answer_text="Shut down Neoterra.", is_correct=False)

        # ------- STORY 2: FANTASY -------
        story_fantasy, _ = Story.objects.get_or_create(
            title="Whispers of the Ancestor Tree",
            defaults={
                'description': "Deep within the Elderwood lies the Ancestor Tree, a massive entity of pure magical resonance. A young druid is summoned by its whispers to prevent a creeping darkness.",
                'genre': fantasy
            }
        )
        assign_cover(story_fantasy, 'fantasy.png')
        if not story_fantasy.chapters.exists():
            fc1 = Chapter.objects.create(story=story_fantasy, chapter_number=1, title="The Awakening",
                content="The roots hummed beneath her bare feet. Elara could feel the magic pulsing, a slow heartbeat within the earth itself. The Ancestor Tree was calling her name. She had no choice but to answer.")
            fq1 = Question.objects.create(chapter=fc1, question_text="What did Elara feel pulsing beneath her feet?")
            Answer.objects.create(question=fq1, answer_text="An earthquake.", is_correct=False)
            Answer.objects.create(question=fq1, answer_text="Magic.", is_correct=True)
            Answer.objects.create(question=fq1, answer_text="Water.", is_correct=False)

            fc2 = Chapter.objects.create(story=story_fantasy, chapter_number=2, title="The Darkening",
                content="The forest edge crumbled. Bark turned black and fell to dust where the corruption had spread. Elara placed her palms on the Ancestor Tree's roots and poured her life force into it, desperate to hold back the tide of shadow.")
            fq2 = Question.objects.create(chapter=fc2, question_text="What happened to the trees at the forest edge?")
            Answer.objects.create(question=fq2, answer_text="They grew taller.", is_correct=False)
            Answer.objects.create(question=fq2, answer_text="They turned black and crumbled to dust.", is_correct=True)
            Answer.objects.create(question=fq2, answer_text="They caught fire.", is_correct=False)

        # ------- STORY 3: MYSTERY -------
        story_mystery, _ = Story.objects.get_or_create(
            title="The Midnight Cipher",
            defaults={
                'description': "Detective Aris sits at his desk, analyzing a cryptic letter left at a crime scene. The deeper he digs, the more dangerous the conspiracy becomes.",
                'genre': mystery
            }
        )
        assign_cover(story_mystery, 'mystery.png')
        if not story_mystery.chapters.exists():
            mc1 = Chapter.objects.create(story=story_mystery, chapter_number=1, title="The Desk",
                content="Smoke hung in the air of the cramped office. My magnifying glass hovered over the ancient map. The markings didn't align with the murder weapon. Something was deeply wrong with this crime scene.")
            mq1 = Question.objects.create(chapter=mc1, question_text="What tool was the detective using to examine the map?")
            Answer.objects.create(question=mq1, answer_text="A magnifying glass.", is_correct=True)
            Answer.objects.create(question=mq1, answer_text="A flashlight.", is_correct=False)
            Answer.objects.create(question=mq1, answer_text="A camera.", is_correct=False)

        # ------- STORY 4: ADVENTURE -------
        story_adv, _ = Story.objects.get_or_create(
            title="Beyond the Golden Keep",
            defaults={
                'description': "An epic journey across the shattered mountains to find the legendary Golden Keep before the sunset claims the horizon.",
                'genre': adventure
            }
        )
        assign_cover(story_adv, 'adventure.png')
        if not story_adv.chapters.exists():
            ac1 = Chapter.objects.create(story=story_adv, chapter_number=1, title="The Horizon",
                content="The wind howled through the stone archway. We had been walking for three suns, and finally, the peaks parted to reveal the path. The Golden Keep shimmered in the distance like a mirage.")
            aq1 = Question.objects.create(chapter=ac1, question_text="How long had the adventurers been walking?")
            Answer.objects.create(question=aq1, answer_text="Three suns.", is_correct=True)
            Answer.objects.create(question=aq1, answer_text="Ten days.", is_correct=False)
            Answer.objects.create(question=aq1, answer_text="One moon.", is_correct=False)

        self.stdout.write(self.style.SUCCESS('Successfully seeded the database with 4 premium stories!'))
