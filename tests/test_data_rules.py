import sys
from pathlib import Path
import unittest
from tempfile import TemporaryDirectory
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from update_github import count_files, personal_commit, event_summary, unique_events
from update_contributions import CalendarParser
from build_profile import render_music


class CountingRules(unittest.TestCase):
    def test_line_counts_exclude_other_projects_and_lockfiles(self):
        files = [
            {'filename': 'shop/src/app.js', 'additions': 12, 'deletions': 4},
            {'filename': 'shop/package-lock.json', 'additions': 1000, 'deletions': 900},
            {'filename': 'other/src/app.js', 'additions': 500, 'deletions': 100},
            {'filename': 'shop/docs/notes.md', 'additions': 5, 'deletions': 2},
        ]
        self.assertEqual(count_files(files, 'shop/', ['package-lock.json']), {'added': 17, 'deleted': 6})

    def test_unlinked_authors_other_people_and_merges_are_not_personal_commits(self):
        self.assertFalse(personal_commit({'author': None, 'parents': [{}]}, 'John'))
        self.assertFalse(personal_commit({'author': {'login': 'someone'}, 'parents': [{}]}, 'John'))
        self.assertFalse(personal_commit({'author': {'login': 'John'}, 'parents': [{}, {}]}, 'John'))
        self.assertTrue(personal_commit({'author': {'login': 'john'}, 'parents': [{}]}, 'John'))

    def test_profile_bot_updates_are_not_recycled_into_the_activity_feed(self):
        event = {'type': 'PushEvent', 'repo': {'name': 'John/John'}, 'payload': {}, 'created_at': '2026-10-30T00:00:00Z'}
        self.assertIsNone(event_summary(event, 'John'))

    def test_calendar_reads_real_dates_and_rejects_unknown_intensity_levels(self):
        parser = CalendarParser()
        parser.feed('<td data-date="2026-10-30" data-level="3"></td>')
        self.assertEqual(parser.days, {'2026-10-30': 3})
        with self.assertRaises(ValueError):
            parser.feed('<td data-date="2026-10-29" data-level="8"></td>')

    def test_activity_repeated_pushes_on_the_same_day_are_one_update(self):
        item = {'date': '2026-10-30', 'title': 'Pushed changes', 'url': 'https://github.com/John/repo'}
        older = {**item, 'date': '2026-10-29'}
        self.assertEqual(unique_events([None, item, item, older]), [item, older])

    def test_music_metadata_cannot_insert_svg_elements(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'assets').mkdir()
            snapshot = {'provider': 'Spotify', 'playing': True, 'period': 'LAST 4 WEEKS', 'track': '<script>bad</script>', 'artist': 'A & B', 'top_artists': [], 'updated_at': '2026-10-30T12:00:00Z'}
            with patch('build_profile.ROOT', root):
                render_music(snapshot, 'dark')
            svg = ET.parse(root/'assets/music-dark.svg').getroot()
            self.assertFalse(any(item.tag.endswith('}script') for item in svg.iter()))
            self.assertIn('<script>bad</script>', ''.join(svg.itertext()))


if __name__ == '__main__':
    unittest.main()
