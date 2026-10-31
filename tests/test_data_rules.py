import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from update_github import count_files, personal_commit
from update_contributions import CalendarParser


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

    def test_calendar_reads_real_dates_and_rejects_unknown_intensity_levels(self):
        parser = CalendarParser()
        parser.feed('<td data-date="2026-10-30" data-level="3"></td>')
        self.assertEqual(parser.days, {'2026-10-30': 3})
        with self.assertRaises(ValueError):
            parser.feed('<td data-date="2026-10-29" data-level="8"></td>')


if __name__ == '__main__':
    unittest.main()
