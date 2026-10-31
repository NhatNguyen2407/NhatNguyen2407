import contextlib
from datetime import datetime, timezone
import io
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import build_profile
import update_github


class StatsPeriod(unittest.TestCase):
    def test_all_time_includes_old_history_and_rolling_window_still_filters(self):
        for days, expected in [(None, 2), (30, 1)]:
            with self.subTest(days=days):
                config = {'username': 'John', 'stats_days': days,
                          'code_repositories': [{'name': 'demo', 'path': ''}],
                          'language_repositories': ['demo'], 'excluded_paths': []}
                written = {}
                queries = []

                def request(path, params=None):
                    if path == 'repos/John/demo':
                        return {'private': False, 'fork': False, 'default_branch': 'main', 'stargazers_count': 2}, ''
                    if path == 'repos/John/demo/languages':
                        return {'Python': 120}, ''
                    if path == 'search/issues':
                        queries.append(params['q'])
                        return {'incomplete_results': False, 'total_count': 8 if days is None else 1}, ''
                    if path == 'repos/John/demo/commits':
                        self.assertEqual(params.get('until'), '2026-10-31T00:00:00Z')
                        self.assertEqual('since' in params, days is not None)
                        shas = ['recent', 'old'] if 'since' not in params else ['recent']
                        return [{'sha': sha, 'author': {'login': 'John'}, 'parents': [{}]} for sha in shas], ''
                    if path.startswith('repos/John/demo/commits/'):
                        return {'files': [{'filename': 'app.py', 'additions': 10, 'deletions': 2}]}, ''
                    self.fail('Unexpected GitHub endpoint: ' + path)

                with patch.object(update_github, 'datetime') as clock, \
                     patch.object(update_github, 'read_json', side_effect=lambda path, default=None: config if path == 'config/profile.json' else {}), \
                     patch.object(update_github, 'request', request), \
                     patch.object(update_github, 'write_json', side_effect=lambda path, value: written.update({path: value})), \
                     contextlib.redirect_stdout(io.StringIO()):
                    clock.now.return_value = datetime(2026, 10, 31, tzinfo=timezone.utc)
                    update_github.collect()

                data = written['data/github.json']
                self.assertEqual(data['days'], days)
                self.assertEqual(data['since'], None if days is None else '2026-10-01T00:00:00Z')
                self.assertEqual(data['stats']['commits'], expected)
                self.assertEqual(data['stats']['added'], expected * 10)
                self.assertEqual(data['stats']['deleted'], expected * 2)
                self.assertEqual(data['stats']['pull_requests'], 8 if days is None else 1)
                self.assertEqual(data['stats']['issues'], 8 if days is None else 1)
                self.assertTrue(all(('created:>=' in query) == (days is not None) for query in queries))

    def test_stats_cards_use_the_snapshot_period_in_both_themes(self):
        for days, label in [(None, 'GITHUB / ALL TIME'), (30, 'GITHUB / LAST 30 DAYS')]:
            with self.subTest(days=days), TemporaryDirectory() as directory:
                root = Path(directory)
                (root / 'assets').mkdir()
                data = {'days': days, 'updated_at': '2026-10-31T00:00:00Z',
                        'stats': {'stars': 2, 'commits': 3, 'pull_requests': 4,
                                  'issues': 5, 'added': 100, 'deleted': 20}}
                with patch.object(build_profile, 'ROOT', root):
                    for theme in build_profile.PALETTES:
                        build_profile.render_stats(data, theme)
                        svg = ET.parse(root / f'assets/github-stats-{theme}.svg').getroot()
                        self.assertIn(label, ''.join(svg.itertext()))


if __name__ == '__main__':
    unittest.main()
