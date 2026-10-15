import csv
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class WorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'toolkit'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('__pycache__', '.git', '.venv'))

    def tearDown(self):
        self.temp.cleanup()

    def run_script(self, name, *args):
        return subprocess.run([sys.executable, str(self.root / 'scripts' / name), *map(str, args)],
                              cwd=self.temp.name, capture_output=True, text=True)

    def evidence(self, change=None, *, headers=None, rows=None):
        with (self.root / 'examples/synthetic/evidence.csv').open(newline='') as stream:
            reader = csv.DictReader(stream)
            columns, data = reader.fieldnames, list(reader)
        if change: data[0].update(change)
        target = Path(self.temp.name) / 'evidence.csv'
        with target.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=headers or columns, extrasaction='ignore')
            writer.writeheader(); writer.writerows(data if rows is None else rows)
        return target

    def create(self, slug='synthetic-review'):
        return self.run_script('bootstrap_project.py', '--name', 'Synthetic review', '--slug', slug, '--language', 'en')

    def test_workspace_structure(self):
        result = self.run_script('validate_workspace.py')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('skills=11 custom_agents=8', result.stdout)

    def test_synthetic_evidence_strict(self):
        result = self.run_script('validate_evidence.py', self.root / 'examples/synthetic/evidence.csv', '--strict')
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_interpretation_cannot_be_author_claim(self):
        for level in ['E3', 'E4']:
            result = self.run_script('validate_evidence.py', self.evidence({'evidence_level': level, 'authors_claim': 'invented attribution'}))
            self.assertEqual(result.returncode, 1)

    def test_invalid_evidence_level(self):
        self.assertEqual(self.run_script('validate_evidence.py', self.evidence({'evidence_level': 'E9'})).returncode, 1)

    def test_direct_claim_requires_locator_in_strict_mode(self):
        result = self.run_script('validate_evidence.py', self.evidence({'evidence_level': 'E0', 'source_locator': ''}), '--strict')
        self.assertEqual(result.returncode, 1)

    def test_warning_is_not_silent_pass(self):
        result = self.run_script('validate_evidence.py', self.evidence({'evidence_level': 'E1', 'source_locator': ''}))
        self.assertEqual(result.returncode, 0)
        self.assertIn('STATUS=PASS_WITH_WARNINGS', result.stdout)

    def test_empty_template_not_completed_evidence(self):
        self.assertEqual(self.run_script('validate_evidence.py', self.evidence(rows=[]), '--strict').returncode, 1)

    def test_missing_columns(self):
        self.assertEqual(self.run_script('validate_evidence.py', self.evidence(headers=['paper_id'])).returncode, 1)

    def test_missing_paper_id(self):
        self.assertEqual(self.run_script('validate_evidence.py', self.evidence({'paper_id': ''})).returncode, 1)

    def test_duplicate_paper_id(self):
        path = self.evidence()
        text = path.read_text(); path.write_text(text + text.splitlines()[1] + '\n')
        self.assertEqual(self.run_script('validate_evidence.py', path).returncode, 1)

    def test_malformed_row(self):
        path = self.evidence(); path.write_text(path.read_text() + 'short,row\n')
        self.assertEqual(self.run_script('validate_evidence.py', path).returncode, 1)

    def test_project_bootstrap_and_summary(self):
        result = self.create()
        self.assertEqual(result.returncode, 0, result.stderr)
        project = self.root / 'projects/synthetic-review'
        self.assertEqual(len([p for p in project.iterdir() if p.is_dir()]), 13)
        self.assertIn('Synthetic review', (project / '00_protocol/project_brief.md').read_text())
        self.assertNotIn('{{', (project / '00_protocol/project_brief.md').read_text())
        summary = self.run_script('summarize_project.py', project)
        self.assertEqual(summary.returncode, 0)
        self.assertRegex(summary.stdout, r'evidence\s+0')

    def test_existing_project_preserved(self):
        self.assertEqual(self.create().returncode, 0)
        brief = self.root / 'projects/synthetic-review/00_protocol/project_brief.md'
        brief.write_text('User-owned note')
        self.assertNotEqual(self.create().returncode, 0)
        self.assertEqual(brief.read_text(), 'User-owned note')

    def test_force_cannot_overwrite(self):
        self.assertEqual(self.create().returncode, 0)
        result = self.run_script('bootstrap_project.py', '--name', 'Overwrite', '--slug', 'synthetic-review', '--force')
        self.assertNotEqual(result.returncode, 0)

    def test_path_traversal_and_absolute_slug_blocked(self):
        for slug in ['../outside', '/outside', 'a/b', 'bad space']:
            self.assertNotEqual(self.create(slug).returncode, 0)

    def test_symlinked_project_root_blocked(self):
        shutil.rmtree(self.root / 'projects')
        outside = Path(self.temp.name) / 'outside'; outside.mkdir()
        (self.root / 'projects').symlink_to(outside, target_is_directory=True)
        self.assertNotEqual(self.create().returncode, 0)
        self.assertFalse(list(outside.iterdir()))

    def test_all_role_configs_are_advisory_not_fake_sandboxes(self):
        paths = list((self.root / '.codex/agents').glob('*.toml'))
        self.assertEqual(len(paths), 8)
        names = set()
        for path in paths:
            role = tomllib.loads(path.read_text())
            self.assertTrue(all(role.get(key) for key in ['name', 'description', 'developer_instructions']))
            self.assertNotIn('sandbox_mode', role)
            self.assertIn('permissions are inherited', role['developer_instructions'])
            names.add(role['name'])
        self.assertEqual(len(names), 8)

    def test_skill_shared_paths_resolve(self):
        for skill in (self.root / '.agents/skills').glob('*/SKILL.md'):
            self.assertEqual(skill.parent.parents[2], self.root)
            text = skill.read_text()
            self.assertIn('relative to that root', text)
            for path in re.findall(r'`(references/[a-z-]+\.md)`', text):
                self.assertTrue((self.root / path).is_file(), path)

    def test_no_model_or_concurrency_override(self):
        config = tomllib.loads((self.root / '.codex/config.toml').read_text())
        self.assertEqual(config, {'agents': {}})

    def test_release_scanner_clean(self):
        result = self.run_script('release_check.py')
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_release_scanner_rejects_runtime_database(self):
        (self.root / 'unexpected.sqlite').write_text('synthetic fixture')
        self.assertNotEqual(self.run_script('release_check.py').returncode, 0)


if __name__ == '__main__':
    unittest.main()
