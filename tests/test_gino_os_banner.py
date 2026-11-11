import unittest
from pathlib import Path
from PIL import Image
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = {'whoami','experience','projects','stack','ai','architecture','contact','ask'}

class SummaryParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.inside=False; self.cards=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if tag=='summary': self.inside=True
        elif tag=='img' and self.inside and 'terminal-accordions/' in a.get('src',''):
            self.cards.append(a)
    def handle_endtag(self, tag):
        if tag=='summary': self.inside=False

class BannerTests(unittest.TestCase):
    def test_portrait_is_actual_animation(self):
        with Image.open(ROOT / 'assets/ascii-thumbs-up.gif') as gif:
            self.assertEqual(gif.format, 'GIF')
            self.assertGreaterEqual(gif.n_frames, 8)
    def test_banner_contains_independent_gif_and_static_image(self):
        s=(ROOT/'README.md').read_text()
        self.assertIn('<table align="center">', s)
        self.assertIn('src="./assets/ascii-thumbs-up.gif"', s)
        self.assertIn('src="./assets/gino-os-terminal-text.png"', s)
        with Image.open(ROOT / "assets/gino-os-terminal-text.png") as panel:
            self.assertEqual(panel.format, "PNG")
            self.assertEqual(panel.size, (720, 358))
        self.assertIn('visitor@github:~$ help',s)
        self.assertNotIn('<img src="./assets/gino-os-command-header-animated.gif"',s)
    def test_whole_command_cards_inside_summary(self):
        parser=SummaryParser(); parser.feed((ROOT/'README.md').read_text())
        self.assertEqual(len(parser.cards),8)
        names={Path(a['src']).stem for a in parser.cards}
        self.assertEqual(names, COMMANDS)
        self.assertTrue(all(a.get('width')=='94%' for a in parser.cards))
    def test_custom_chevrons_removed(self):
        for name in COMMANDS:
            self.assertNotIn('M789 51 l10 9 10-9', (ROOT/'assets/terminal-accordions'/f'{name}.svg').read_text())
    def test_existing_data_and_features_remain(self):
        s=(ROOT/'README.md').read_text()
        for name in ['FEATURED_PROJECTS:START', 'Playwright', 'Claude Code', 'OpenSearch', 'terminal-status.gif', 'ask-gino-os.yml']:
            self.assertIn(name,s)

if __name__ == '__main__': unittest.main()
