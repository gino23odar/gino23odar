"""Regression checks for native GitHub README command accordions.

Runs with the Python standard library, just like the existing portfolio tests.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / 'README.md').read_text(encoding='utf-8')
COMMANDS = ['whoami','experience','projects','stack','ai','architecture','contact','ask']


class TerminalAccordionTests(unittest.TestCase):
    def test_every_original_command_is_present_once(self):
        for cmd in COMMANDS:
            self.assertEqual(README.count(f'<details id="gino-{cmd}">'), 1, cmd)
            self.assertEqual(README.count(f'./assets/terminal-accordions/{cmd}.svg'), 1, cmd)
        self.assertEqual(README.count('<details id="gino-'), 8)

    def test_all_commands_start_closed(self):
        for cmd in COMMANDS:
            self.assertNotIn(f'<details id="gino-{cmd}" open', README)
        self.assertEqual(README.count('<summary><img src="./assets/terminal-accordions/'), 8)

    def test_original_content_is_retained(self):
        for snippet in (
            'Playwright', 'Semaphore CI', 'OpenSearch', 'ClickHouse',
            'New Relic', 'Amazon CloudWatch', 'Jenkins', 'Kafka',
            'Claude Code', 'OpenAI Codex', 'Model Context Protocol (MCP)',
            'AcademIA de Profesores', 'Verdant Mythic Vault',
            'Queue Management Simulation', 'Ideal Function Data Pipeline',
            'What I\'m building toward', 'English / German / Spanish',
            'field-engineering-loop.gif', 'ai-reference-architecture.gif',
            'GINO.OS question form',
        ):
            self.assertIn(snippet, README, snippet)

    def test_hot_swappable_gallery_markers_stay_inside_projects(self):
        projects_start = README.index('<details id="gino-projects">')
        projects_end = README.index('</details>', projects_start)
        markers = ('<!-- FEATURED_PROJECTS:START -->','<!-- FEATURED_PROJECTS:END -->')
        for marker in markers:
            self.assertEqual(README.count(marker), 1)
            self.assertTrue(projects_start < README.index(marker) < projects_end)

    def test_links_and_assets_exist(self):
        for rel in re.findall(r'(?:src|href)="(\./(?:assets|config|docs)/[^"#?]+)"', README):
            self.assertTrue((ROOT / rel).exists(), rel)
        for cmd in COMMANDS:
            art = ROOT/'assets'/'terminal-accordions'/f'{cmd}.svg'
            self.assertIn('viewBox="0 0 840 86"', art.read_text())

    def test_config_links_point_at_existing_disclosures(self):
        import json
        facts = json.loads((ROOT/'config'/'profile_knowledge.json').read_text())
        src = (ROOT/'config'/'profile_knowledge.json').read_text()
        for target in re.findall(r'https://github\.com/gino23odar/gino23odar#([a-z-]+)', src):
            self.assertTrue(target == 'ginoos' or f'id="{target}"' in README, target)

    def test_ask_still_opens_real_issue_form(self):
        body=README.split('<details id="gino-ask">',1)[1].split('</details>',1)[0]
        self.assertIn('issues/new?template=ask-gino-os.yml',body)
        self.assertTrue((ROOT/'.github/ISSUE_TEMPLATE/ask-gino-os.yml').exists())
        self.assertTrue((ROOT/'.github/workflows/gino-os.yml').exists())

    def test_anonymous_employer_copy(self):
        self.assertNotIn('Ensolvers', README)
        self.assertNotIn('Hyros', README)


if __name__ == '__main__':
    unittest.main()
