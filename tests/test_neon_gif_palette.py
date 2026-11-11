"""Verify terminal-only neon green; preserve original lettering in other GIFs."""
import unittest
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
REGIONS = {
    'hero-ai-systems.gif': (55, 125, 540, 193),
    'ai-reference-architecture.gif': (43, 40, 800, 75),
    'field-engineering-loop.gif': (49, 112, 319, 139),
    'terminal-status.gif': (87, 70, 650, 115),
}

class TerminalOnlyGreenTests(unittest.TestCase):
    def test_terminal_green_other_gifs_original_typography(self):
        for name, bbox in REGIONS.items():
            with self.subTest(animation=name):
                with Image.open(ROOT / 'assets' / name) as gif:
                    self.assertGreater(gif.n_frames, 1)
                    self.assertEqual(gif.info.get('loop'), 0)
                    gif.seek(gif.n_frames // 2)
                    colors = list(gif.convert('RGB').crop(bbox).getdata())
                green = sum(g > 140 and r < 120 and b < 145 for r, g, b in colors)
                white = sum(r > 155 and g > 155 and b > 155 for r, g, b in colors)
                if name == 'terminal-status.gif':
                    self.assertGreater(green, 300)
                    self.assertLess(white, 35)
                else:
                    self.assertLess(green, 50)
                    self.assertGreater(white, 100)

    def test_only_change_or_manual_workflow(self):
        workflow = (ROOT / '.github' / 'workflows' / 'terminal-display.yml').read_text()
        self.assertIn('workflow_dispatch:', workflow)
        self.assertIn('push:', workflow)
        self.assertNotIn('  schedule:', workflow)

if __name__ == '__main__':
    unittest.main()
