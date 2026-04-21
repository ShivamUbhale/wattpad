from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .models import Chapter, Poll, PollOption, Story, UserProgress, Vote


def _next_chapter(story, chapter_number):
    return Chapter.objects.filter(
        story=story,
        chapter_number=chapter_number + 1,
    ).first()


def _highest_unlocked(user, story):
    if not user.is_authenticated:
        return 1
    progress, _ = UserProgress.objects.get_or_create(user=user, story=story)
    return progress.highest_unlocked_chapter_number


def _sync_completion(progress):
    story = progress.story
    total = story.chapters.count()
    if total <= 0:
        return
    pct = ((progress.highest_unlocked_chapter_number - 1) / total) * 100
    progress.completion_percentage = min(100.0, pct)
    progress.save(update_fields=['completion_percentage'])


def _advance_after_vote(user, poll):
    """Unlock the chapter after this poll's chapter when a vote is cast."""
    chapter = poll.chapter
    story = chapter.story
    nxt = chapter.chapter_number + 1
    if not Chapter.objects.filter(story=story, chapter_number=nxt).exists():
        return
    progress, _ = UserProgress.objects.get_or_create(user=user, story=story)
    if progress.highest_unlocked_chapter_number <= chapter.chapter_number:
        progress.highest_unlocked_chapter_number = nxt
        progress.save(update_fields=['highest_unlocked_chapter_number'])
    _sync_completion(progress)


def homepage_view(request):
    stories = Story.objects.select_related('genre').prefetch_related('chapters')
    featured = stories.filter(is_featured=True).first() or stories.first()

    story_rows = []
    for story in stories:
        total_ch = story.chapters.count()
        item = {'story': story, 'total_chapters': total_ch}
        if request.user.is_authenticated:
            progress, _ = UserProgress.objects.get_or_create(
                user=request.user,
                story=story,
            )
            _sync_completion(progress)
            item['progress'] = progress
            item['percentage'] = progress.completion_percentage
        else:
            item['progress'] = None
            item['percentage'] = 0.0
        story_rows.append(item)

    trending = list(stories[:8])
    vote_count = Vote.objects.count()
    author_count = get_user_model().objects.filter(is_active=True).count()

    return render(
        request,
        'stories/home.html',
        {
            'featured_story': featured,
            'story_rows': story_rows,
            'trending_stories': trending,
            'vote_count': vote_count,
            'author_count': author_count,
            'nav_active': 'home',
        },
    )


def chapter_view(request, story_id, chapter_number):
    story = get_object_or_404(Story.objects.select_related('genre'), id=story_id)
    chapter = get_object_or_404(
        Chapter.objects.select_related('story'),
        story=story,
        chapter_number=chapter_number,
    )

    unlocked = _highest_unlocked(request.user, story)

    if not request.user.is_authenticated:
        if chapter_number > 1:
            messages.info(request, 'Sign in to continue past the first chapter.')
            login_url = reverse('login')
            qs = urlencode({'next': request.get_full_path()})
            return redirect(f'{login_url}?{qs}')
        # Anonymous may read chapter 1 only
    elif chapter_number > unlocked:
        prev = get_object_or_404(Chapter, story=story, chapter_number=chapter_number - 1)
        if Poll.objects.filter(chapter=prev).exists():
            messages.warning(
                request,
                'The Salon requires your voice on the previous threshold before you may continue.',
            )
            return redirect('poll_view', story_id=story.id, chapter_number=prev.chapter_number)
        messages.error(request, 'This chapter is still locked.')
        return redirect('home')

    total = story.chapters.count()
    next_ch = _next_chapter(story, chapter_number)
    poll = Poll.objects.filter(chapter=chapter).first()
    user_vote = None
    if request.user.is_authenticated and poll:
        user_vote = Vote.objects.filter(user=request.user, poll=poll).select_related('option').first()

    # Offer poll whenever it exists and the user has not voted (including final chapter).
    needs_vote = bool(
        request.user.is_authenticated
        and poll
        and not user_vote
    )
    can_read_next = bool(
        request.user.is_authenticated
        and next_ch
        and next_ch.chapter_number <= unlocked
    )

    return render(
        request,
        'stories/chapter_detail.html',
        {
            'story': story,
            'chapter': chapter,
            'total_chapters': total,
            'next_chapter': next_ch,
            'poll': poll,
            'user_vote': user_vote,
            'unlocked_up_to': unlocked,
            'needs_vote': needs_vote,
            'can_read_next': can_read_next,
            'nav_active': 'library',
        },
    )


@login_required
@require_http_methods(['GET', 'POST'])
def poll_view(request, story_id, chapter_number):
    story = get_object_or_404(Story, id=story_id)
    chapter = get_object_or_404(Chapter, story=story, chapter_number=chapter_number)
    poll = get_object_or_404(Poll, chapter=chapter)

    unlocked = _highest_unlocked(request.user, story)
    if chapter.chapter_number > unlocked:
        messages.error(request, 'You have not reached this chapter yet.')
        return redirect('home')

    existing = Vote.objects.filter(user=request.user, poll=poll).first()
    if existing:
        return redirect('poll_results', story_id=story.id, chapter_number=chapter.chapter_number)

    options = list(poll.options.all())

    if request.method == 'POST':
        opt_id = request.POST.get('option_id')
        option = get_object_or_404(PollOption, id=opt_id, poll=poll)
        try:
            Vote.objects.create(user=request.user, poll=poll, option=option)
        except IntegrityError:
            messages.info(request, 'Your echo was already recorded.')
            return redirect('poll_results', story_id=story.id, chapter_number=chapter.chapter_number)

        _advance_after_vote(request.user, poll)
        messages.success(request, 'The Salon heard you. Here is how the collective decided.')
        return redirect('poll_results', story_id=story.id, chapter_number=chapter.chapter_number)

    return render(
        request,
        'stories/poll.html',
        {
            'story': story,
            'chapter': chapter,
            'poll': poll,
            'options': options,
            'nav_active': 'ritual',
        },
    )


@login_required
def poll_results_view(request, story_id, chapter_number):
    story = get_object_or_404(Story, id=story_id)
    chapter = get_object_or_404(Chapter, story=story, chapter_number=chapter_number)
    poll = get_object_or_404(Poll, chapter=chapter)

    if not Vote.objects.filter(user=request.user, poll=poll).exists():
        messages.info(request, 'Cast your vote to see how the collective chose.')
        return redirect('poll_view', story_id=story.id, chapter_number=chapter.chapter_number)

    totals = (
        Vote.objects.filter(poll=poll)
        .values('option_id')
        .annotate(c=Count('id'))
    )
    count_by_option = {row['option_id']: row['c'] for row in totals}
    total_votes = sum(count_by_option.values()) or 0

    option_rows = []
    winning_id = None
    max_votes = -1
    for opt in poll.options.all():
        c = count_by_option.get(opt.id, 0)
        pct = round((100.0 * c / total_votes), 1) if total_votes else 0.0
        option_rows.append({'option': opt, 'count': c, 'percent': pct})
        if c > max_votes:
            max_votes = c
            winning_id = opt.id

    user_vote = Vote.objects.filter(user=request.user, poll=poll).select_related('option').first()
    next_ch = _next_chapter(story, chapter.chapter_number)

    history = []
    for ch in (
        story.chapters.filter(chapter_number__lt=chapter.chapter_number)
        .order_by('-chapter_number')
    ):
        p = Poll.objects.filter(chapter=ch).first()
        if not p:
            continue
        tv = Vote.objects.filter(poll=p).count()
        if tv == 0:
            continue
        top = (
            PollOption.objects.filter(poll=p)
            .annotate(vc=Count('votes'))
            .order_by('-vc')
            .first()
        )
        if top:
            tvotes = Vote.objects.filter(poll=p, option=top).count()
            history.append(
                {
                    'poll': p,
                    'label': top.title,
                    'percent': round(100.0 * tvotes / tv, 1) if tv else 0,
                }
            )

    return render(
        request,
        'stories/poll_results.html',
        {
            'story': story,
            'chapter': chapter,
            'poll': poll,
            'option_rows': option_rows,
            'total_votes': total_votes,
            'user_vote': user_vote,
            'winning_option_id': winning_id,
            'next_chapter': next_ch,
            'history': history[:5],
            'nav_active': 'ritual',
        },
    )


def dashboard_redirect(request):
    """Backward-compatible name used in older templates."""
    return redirect('home')
