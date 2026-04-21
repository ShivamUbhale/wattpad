"""
Watch a filesystem folder for .txt / .pdf files and create Story + chapters.

Configure paths in settings (STORY_DROP_*). Run once, or with --watch for a loop.

  python manage.py process_story_drop
  python manage.py process_story_drop --watch 120
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from stories.importers import create_story_from_dropped_path


def _ensure_dirs(*paths: Path) -> None:
    for p in paths:
        p.mkdir(parents=True, exist_ok=True)


def _unique_dest(folder: Path, name: str) -> Path:
    dest = folder / name
    if not dest.exists():
        return dest
    stem = Path(name).stem
    suf = Path(name).suffix
    ts = timezone.now().strftime("%Y%m%d_%H%M%S")
    return folder / f"{stem}_{ts}{suf}"


def process_incoming(incoming: Path, processed: Path, failed: Path) -> tuple[int, int]:
    """Returns (success_count, failure_count)."""
    ok = 0
    bad = 0
    _ensure_dirs(incoming, processed, failed)

    candidates = sorted(
        p
        for p in incoming.iterdir()
        if p.is_file() and p.suffix.lower() in {".txt", ".pdf"}
    )

    for src in candidates:
        try:
            story, (n_ch, n_po) = create_story_from_dropped_path(src)
            dest = _unique_dest(processed, src.name)
            shutil.move(str(src), str(dest))
            ok += 1
            print(f"OK  {src.name} -> Story #{story.pk} ({story.title!r}), {n_ch} ch, {n_po} polls -> {dest.name}")
        except Exception as exc:
            bad += 1
            dest = _unique_dest(failed, src.name)
            try:
                shutil.move(str(src), str(dest))
            except OSError as move_exc:
                print(f"ERR {src.name}: {exc}; could not move to failed: {move_exc}")
            else:
                print(f"ERR {src.name}: {exc} -> moved to failed/{dest.name}")
    return ok, bad


class Command(BaseCommand):
    help = "Import .txt/.pdf files from STORY_DROP_INCOMING_DIR into new stories."

    def add_arguments(self, parser):
        parser.add_argument(
            "--watch",
            type=int,
            default=0,
            metavar="SECONDS",
            help="Re-scan every SECONDS until interrupted (0 = run once).",
        )

    def handle(self, *args, **options):
        incoming = Path(getattr(settings, "STORY_DROP_INCOMING_DIR"))
        processed = Path(getattr(settings, "STORY_DROP_PROCESSED_DIR"))
        failed = Path(getattr(settings, "STORY_DROP_FAILED_DIR"))

        watch = max(0, int(options["watch"]))

        self.stdout.write(
            f"Incoming:  {incoming}\n"
            f"Processed: {processed}\n"
            f"Failed:    {failed}\n"
        )

        while True:
            ok, bad = process_incoming(incoming, processed, failed)
            if ok or bad:
                self.stdout.write(self.style.SUCCESS(f"Batch: {ok} imported, {bad} failed."))
            elif watch > 0:
                self.stdout.write("No files to process.")

            if watch <= 0:
                break
            time.sleep(watch)
