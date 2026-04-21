"""
Import story body text from .txt or .pdf into Chapter rows.

Format (recommended): one header per chapter, then body until the next header.

  ## Chapter 1: Opening
  Paragraphs...

  ## Chapter 2: The crossing
  More text...

Also accepted (no ##): lines matching:
  Chapter 1 - Title
  Chapter 2: Another title

If no chapter headers are found, the entire file becomes a single chapter titled "Chapter 1".
"""

from __future__ import annotations

import re
from pathlib import Path

from django.core.files import File
from django.db import transaction

CHAPTER_HEADER = re.compile(
    r"^#{0,2}\s*Chapter\s+(\d+)\s*[:-–—]\s*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _read_pdf_text(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def extract_text_from_path(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return _read_text_file(path)
    if suffix == ".pdf":
        return _read_pdf_text(path)
    raise ValueError(f"Unsupported file type: {suffix}")


def split_into_chapters(text: str) -> list[dict]:
    text = text.strip()
    if not text:
        return []

    matches = list(CHAPTER_HEADER.finditer(text))
    if not matches:
        title = "Chapter 1"
        first_line = text.split("\n", 1)[0].strip()
        if first_line and len(first_line) <= 200 and len(text.split("\n")) > 1:
            title = first_line[:200]
            body = text.split("\n", 1)[1].strip()
        else:
            body = text
        return [{"chapter_number": 1, "title": title, "content": body}]

    chapters: list[dict] = []
    for i, m in enumerate(matches):
        title = m.group(2).strip()[:200]
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        chapters.append(
            {
                "chapter_number": i + 1,
                "title": title or f"Chapter {i + 1}",
                "content": body,
            }
        )

    return chapters


def ensure_polls_for_story(story) -> int:
    """Mirror seed_polls logic for one story; returns number of polls created."""
    from .models import Chapter, Poll, PollOption

    created = 0
    for chapter in story.chapters.order_by("chapter_number"):
        has_next = story.chapters.filter(
            chapter_number=chapter.chapter_number + 1
        ).exists()
        if not has_next:
            continue
        if Poll.objects.filter(chapter=chapter).exists():
            continue

        poll = Poll.objects.create(
            chapter=chapter,
            chapter_label=f"CHAPTER {chapter.chapter_number}",
            prompt_heading=(
                f'Will you cross the threshold after "{chapter.title}"? '
                "The Salon waits for your echo."
            ),
            souls_footer_note="Souls have stood at this threshold.",
            disclaimer=(
                "Decisions are permanent. Your echo will ripple through the chapters "
                "of those who follow."
            ),
        )
        PollOption.objects.create(
            poll=poll,
            label="THE RADIANT PATH",
            title="Accept the Void",
            description=(
                "Walk through the veil. Some secrets are only whispered in the "
                "absolute absence of light."
            ),
            theme="lavender",
            sort_order=0,
        )
        PollOption.objects.create(
            poll=poll,
            label="THE SAFE ECHO",
            title="Turn Back Now",
            description=(
                "The warmth of the known is a seductive trap. Survival is its own "
                "form of storytelling."
            ),
            theme="peach",
            sort_order=1,
        )
        created += 1
    return created


@transaction.atomic
def replace_chapters_from_parsed(story, parsed: list[dict]) -> tuple[int, int]:
    """Replace all chapters from parsed blocks; create polls. Returns (n_chapters, n_polls)."""
    from .models import Chapter

    if not parsed:
        return 0, 0

    story.chapters.all().delete()

    for block in parsed:
        Chapter.objects.create(
            story=story,
            chapter_number=block["chapter_number"],
            title=block["title"],
            content=block["content"],
        )

    polls = ensure_polls_for_story(story)
    return len(parsed), polls


def import_story_from_path(story, path: Path) -> tuple[int, int]:
    """Parse file at path into this story's chapters (replaces existing)."""
    text = extract_text_from_path(path)
    parsed = split_into_chapters(text)
    return replace_chapters_from_parsed(story, parsed)


def import_story_from_file(story) -> tuple[int, int]:
    """
    Read story.import_file from disk, replace all chapters, add polls where needed.

    Returns (chapters_created, polls_created).
    """
    if not story.import_file:
        return 0, 0
    path = Path(story.import_file.path)
    return import_story_from_path(story, path)


def story_title_from_filename(path: Path) -> str:
    stem = path.stem
    stem = re.sub(r"[_\-]+", " ", stem).strip()
    return (stem[:200] if stem else "Untitled import")


def get_or_create_drop_genre():
    from .models import Genre

    genre, _ = Genre.objects.get_or_create(
        name="Imported",
        defaults={"description": "Stories ingested from the drop folder or bulk import."},
    )
    return genre


def create_story_from_dropped_path(source_path: Path) -> tuple[object, tuple[int, int]]:
    """
    Create a new Story, attach file copy under media/story_imports/, import chapters.

    Returns (story, (chapters, polls)).
    """
    from .models import Story

    source_path = source_path.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)

    genre = get_or_create_drop_genre()
    title = story_title_from_filename(source_path)

    story = Story.objects.create(
        title=title,
        description=f"Ingested from drop folder: {source_path.name}",
        genre=genre,
    )

    with source_path.open("rb") as f:
        story.import_file.save(source_path.name, File(f), save=True)

    story.refresh_from_db()
    counts = import_story_from_path(story, Path(story.import_file.path))
    return story, counts
