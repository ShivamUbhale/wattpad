from django.contrib import admin
from django.contrib import messages

from .importers import import_story_from_file
from .models import (
    Answer,
    Chapter,
    Genre,
    Poll,
    PollOption,
    Question,
    Story,
    UserProgress,
    Vote,
)


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0


class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerInline]


class PollOptionInline(admin.TabularInline):
    model = PollOption
    extra = 0


@admin.register(Poll)
class PollAdmin(admin.ModelAdmin):
    list_display = ('chapter', 'prompt_heading')
    inlines = [PollOptionInline]
    search_fields = ('prompt_heading', 'chapter__title', 'chapter__story__title')


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('user', 'poll', 'option', 'created_at')
    list_filter = ('poll',)


class StoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'is_featured', 'created_at')
    list_filter = ('genre', 'is_featured')
    readonly_fields = ('created_at',)
    fieldsets = (
        (
            None,
            {
                'fields': ('title', 'description', 'genre', 'cover_image', 'is_featured'),
            },
        ),
        (
            'Import from file',
            {
                'description': (
                    'Upload a .txt or .pdf file. On save, existing chapters are replaced. '
                    'Start each chapter with a line like "## Chapter 1: Title" or '
                    '"Chapter 1 - Title". Order in the file is chapter 1, 2, 3… '
                    'With no headers, the entire file becomes a single chapter.'
                ),
                'fields': ('import_file',),
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        uploaded = bool(request.FILES.get('import_file'))
        super().save_model(request, obj, form, change)
        if uploaded and obj.import_file:
            try:
                n_ch, n_po = import_story_from_file(obj)
            except Exception as exc:
                messages.error(
                    request,
                    f'Could not import story file: {exc}',
                )
                return
            messages.success(
                request,
                f'Imported {n_ch} chapter(s); created {n_po} new poll(s) where needed.',
            )


admin.site.register(Genre)
admin.site.register(Story, StoryAdmin)
@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ('story', 'chapter_number', 'title')
    list_filter = ('story',)
    search_fields = ('title', 'story__title')
    ordering = ('story', 'chapter_number')
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer)
admin.site.register(UserProgress)
