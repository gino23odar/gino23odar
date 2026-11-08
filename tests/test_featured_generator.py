"""Unit tests for project-card generator. Python standard library only."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'scripts' / 'generate_featured.py'
spec = importlib.util.spec_from_file_location('generate_featured', MODULE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


class ProjectGalleryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((MODULE.parents[1] / 'config' / 'projects.json').read_text())

    def test_initial_config_is_valid(self):
        self.assertEqual(len(gen.validate(self.catalog)), 4)

    def test_reorder_and_replace(self):
        data = json.loads(json.dumps(self.catalog))
        data['featured'] = ['wardrove', 'queue', 'academia']
        items = gen.validate(data)
        out = gen.gallery(items)
        self.assertTrue(out.index('Wardrove Backend Foundation') < out.index('Queue Management Simulation'))
        self.assertNotIn('Ideal Function Data Pipeline', out)
        self.assertEqual(out.count('<td width="50%" valign="top">'), 3)
        self.assertEqual(out.count('assets/featured-'), 3)

    def test_reject_duplicates_and_missing_ids(self):
        data = json.loads(json.dumps(self.catalog))
        data['featured'] = ['queue', 'queue']
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            gen.validate(data)
        data['featured'] = ['queue', 'not-a-project']
        with self.assertRaisesRegex(ValueError, 'absent'):
            gen.validate(data)

    def test_svg_and_html_escaping(self):
        data = json.loads(json.dumps(self.catalog))
        data['catalog']['queue']['title'] = 'Queue & Test <Lab>'
        card = gen.svg_card(data['catalog']['queue'], 1)
        self.assertIn('Queue &amp; Test &lt;Lab&gt;', card)
        out = gen.gallery(gen.validate(data))
        self.assertIn('Queue &amp; Test &lt;Lab&gt;', out)

    def test_invalid_url_rejected(self):
        data = json.loads(json.dumps(self.catalog))
        data['catalog']['queue']['url'] = 'javascript:alert(1)'
        with self.assertRaisesRegex(ValueError, 'HTTPS'):
            gen.validate(data)

    def test_generated_only_inside_markers(self):
        original = gen.ROOT, gen.CONFIG, gen.README, gen.ASSETS
        try:
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / 'config').mkdir()
                (root / 'assets').mkdir()
                (root / 'config' / 'projects.json').write_text(json.dumps(self.catalog))
                (root / 'README.md').write_text('HEADER\n' + gen.START + '\nOLD\n' + gen.END + '\nFOOTER\n')
                gen.ROOT, gen.CONFIG, gen.README, gen.ASSETS = root, root / 'config' / 'projects.json', root / 'README.md', root / 'assets'
                self.assertTrue(gen.build())
                self.assertFalse(gen.build(check=True))
                before = gen.README.read_text()
                data = json.loads(gen.CONFIG.read_text())
                data['featured'] = ['wardrove', 'academia']
                gen.CONFIG.write_text(json.dumps(data))
                self.assertTrue(gen.build(check=True))
                gen.build()
                after = gen.README.read_text()
                self.assertTrue(after.startswith('HEADER\n'))
                self.assertTrue(after.endswith('\nFOOTER\n'))
                self.assertNotEqual(before, after)
                self.assertEqual(len(list(gen.ASSETS.glob('featured-*.svg'))), 2)
                self.assertFalse(gen.build(check=True))
        finally:
            gen.ROOT, gen.CONFIG, gen.README, gen.ASSETS = original


if __name__ == '__main__':
    unittest.main()
