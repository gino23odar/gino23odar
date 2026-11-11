"""Regression tests for the scheduled dynamic GINO.OS display."""
import json
import re
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
README=(ROOT/'README.md').read_text(encoding='utf-8')


class TerminalAnimationTests(unittest.TestCase):
    def test_typing_svg_is_configured_with_requested_green(self):
        self.assertIn('readme-typing-svg.demolab.com/',README)
        self.assertIn('color=3BF74E',README)
        self.assertIn('color=136C29',README)
        self.assertIn('Fira+Code',README)
        self.assertIn('Playwright',README)

    def test_dynamic_gif_is_referenced_and_exists(self):
        self.assertIn('src="./assets/terminal-status.gif"',README)
        path=ROOT/'assets/terminal-status.gif'
        self.assertTrue(path.is_file())
        with Image.open(path) as im:
            self.assertEqual(im.format,'GIF')
            self.assertGreaterEqual(im.n_frames,15)
            self.assertEqual(im.info['loop'],0)
        self.assertLess(path.stat().st_size, 4_000_000)

    def test_all_eight_collapsible_commands_survive(self):
        for cmd in ('whoami','experience','projects','stack','ai','architecture','contact','ask'):
            self.assertIn(f'<details id="gino-{cmd}">',README)
            self.assertIn(f'assets/terminal-accordions/{cmd}.svg',README)
        self.assertEqual(README.count('<details id="gino-'),8)

    def test_generator_only_reads_public_owner_approved_data(self):
        source=(ROOT/'scripts/generate_terminal.py').read_text(encoding='utf-8')
        for filename in ('profile_knowledge.json','projects.json','terminal_display.json'):
            self.assertIn(filename,source)
        self.assertNotIn('requests.get(',source)
        self.assertNotIn('OPENAI_API_KEY',source)

    def test_slide_references_exist(self):
        data=json.loads((ROOT/'config/terminal_display.json').read_text())
        knowledge=json.loads((ROOT/'config/profile_knowledge.json').read_text())
        facts={x['id'] for x in knowledge['facts']}
        for slide in data['slides']:
            if 'fact_id' in slide:
                self.assertIn(slide['fact_id'],facts)

    def test_two_non_competing_regeneration_paths(self):
        scheduled=(ROOT/'.github/workflows/terminal-display.yml').read_text()
        featured=(ROOT/'.github/workflows/featured-projects.yml').read_text()
        self.assertIn("- cron: '17 6 * * *'",scheduled)
        self.assertIn('group: portfolio-render',scheduled)
        self.assertIn('group: portfolio-render',featured)
        self.assertIn('scripts/generate_terminal.py',featured)
        self.assertIn('assets/terminal-status.gif',scheduled)
        self.assertIn('config/projects.json',featured)
        self.assertIn('config/profile_knowledge.json',scheduled)
        self.assertIn('python -m pip install "Pillow>=10,<12"',featured)

    def test_public_question_bot_unchanged(self):
        self.assertTrue((ROOT/'.github/workflows/gino-os.yml').is_file())
        self.assertTrue((ROOT/'.github/ISSUE_TEMPLATE/ask-gino-os.yml').is_file())
        self.assertIn('issues/new?template=ask-gino-os.yml',README)

    def test_no_employer_identity_or_live_claims(self):
        self.assertNotIn('Ensolvers',README)
        self.assertNotIn('Hyros',README)
        self.assertIn('not a live session',README.lower())


if __name__=='__main__':
    unittest.main()
