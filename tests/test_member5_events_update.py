import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from scripts.update_events import calendar, convert, update


def row(identity="1", name="角板山活動"):
    return dict(Id=identity, Name=name, Pending="false", Start="2026/10/01 00:00:00",
                End="2026/10/31 23:59:59",
                TYWebsite="travel.tycg.gov.tw/zh-tw/event/calendardetail/1")


def page(rows, count):
    return {"Infos": {"Declaration": {"Total": str(count)}, "Info": rows}}


class UpdateTests(unittest.TestCase):
    def test_pagination_and_singleton(self):
        pages = iter([page([row()], 2), page(row("2"), 2)])
        self.assertEqual(len(calendar(2026, lambda _: next(pages))), 2)

    def test_incomplete_and_repeated_page_rejected(self):
        for second in ([], [row()]):
            pages = iter([page([row()], 2), page(second, 2)])
            with self.assertRaises(ValueError):
                calendar(2026, lambda _: next(pages))

    def test_filter_pending_expired_and_unrelated(self):
        pending = dict(row("3"), Pending="true")
        expired = dict(row("4"), End="2026/10/02 23:59:59")
        rows = [row(), row("2", "復興路市集"), pending, expired]
        entries = convert(rows, date(2026, 10, 12))
        self.assertEqual([e["id"] for e in entries], ["tycg-1"])
        self.assertTrue(entries[0]["source_url"].startswith("https://"))

    def test_failure_preserves_old_file(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "events_auto.json"
            target.write_text("old", encoding="utf-8")
            def fail(_):
                raise TimeoutError()
            with self.assertRaises(TimeoutError):
                update(target, fetcher=fail, today=date(2026, 10, 12))
            self.assertEqual(target.read_text(), "old")

    def test_valid_empty_replaces_old(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "events_auto.json"
            target.write_text("old", encoding="utf-8")
            update(target, fetcher=lambda _: page(None, 0), today=date(2026, 10, 12))
            self.assertEqual(json.loads(target.read_text()), [])

    def test_invalid_url_and_dates_rejected(self):
        for bad in (dict(row(), TYWebsite="https://example.com"), dict(row(), End="oops")):
            with self.assertRaises(ValueError):
                convert([bad], date(2026, 10, 12))


if __name__ == "__main__":
    unittest.main()
