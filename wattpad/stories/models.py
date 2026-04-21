from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Story(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name='stories')
    cover_image = models.ImageField(upload_to='story_covers/', blank=True, null=True)
    import_file = models.FileField(
        upload_to='story_imports/',
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['txt', 'pdf'])],
        help_text='Upload .txt or .pdf to generate chapters on save (replaces existing chapters).',
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Chapter(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='chapters')
    chapter_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    content = models.TextField()

    class Meta:
        unique_together = ('story', 'chapter_number')
        ordering = ['chapter_number']

    def __str__(self):
        return f"{self.story.title} - Chapter {self.chapter_number}: {self.title}"

class Question(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='questions')
    question_text = models.CharField(max_length=500)

    def __str__(self):
        return self.question_text

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.answer_text

class UserProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress')
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='progress')
    highest_unlocked_chapter_number = models.PositiveIntegerField(default=1)
    completion_percentage = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('user', 'story')

    def __str__(self):
        return f"{self.user.username}'s progress on {self.story.title}"


class Poll(models.Model):
    """Community choice at the end of a chapter; voting unlocks the next chapter."""

    chapter = models.OneToOneField(
        Chapter,
        on_delete=models.CASCADE,
        related_name='poll',
    )
    chapter_label = models.CharField(
        max_length=120,
        blank=True,
        help_text="e.g. CHAPTER IV: THE THRESHOLD",
    )
    prompt_heading = models.CharField(max_length=500)
    souls_footer_note = models.CharField(
        max_length=200,
        blank=True,
        default='',
    )
    disclaimer = models.TextField(blank=True)

    def __str__(self):
        return f"Poll — {self.chapter}"


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='options')
    label = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    theme = models.CharField(
        max_length=32,
        default='lavender',
        help_text="lavender | peach | crimson",
    )
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.poll_id}: {self.title}"


class Vote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='story_votes',
    )
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='votes')
    option = models.ForeignKey(
        PollOption,
        on_delete=models.CASCADE,
        related_name='votes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'poll'],
                name='unique_user_vote_per_poll',
            ),
        ]

    def __str__(self):
        return f"{self.user_id} → {self.poll_id}"
