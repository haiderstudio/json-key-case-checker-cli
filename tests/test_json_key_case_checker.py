#!/usr/bin/env python3
"""Tests for json_key_case_checker — stdlib unittest only."""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import json_key_case_checker as checker

REPO = Path(__file__).resolve().parent.parent


def run_cli(argv):
    """Run main(argv), capture stdout/stderr, return (code, out, err)."""
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = checker.main(argv)
        except SystemExit as exc:
            code = exc.code
    return code, out.getvalue(), err.getvalue()


def write(tmp, name, text, encoding="utf-8"):
    path = Path(tmp) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text, encoding=encoding)
    return str(path)


def findings_of(text, style="snake_case"):
    return checker.check_text(text, style)


class TestKeys(unittest.TestCase):
    def test_clean_file_passes(self):
        bad, error = findings_of(
            '{\n  "user_id": 1,\n  "first_name": "Ada"\n}\n')
        self.assertEqual(bad, [])
        self.assertIsNone(error)

    def test_plain_bad_key_flagged(self):
        bad, _ = findings_of('{\n  "userId": 1\n}\n')
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["line"], 2)
        self.assertEqual(bad[0]["key"], "userId")
        self.assertIn("not snake_case", bad[0]["reason"])

    def test_several_bad_keys_in_order(self):
        bad, _ = findings_of(
            '{\n  "userId": 1,\n  "first_name": "Ada",\n'
            '  "OrderTotal": 9.5\n}\n')
        self.assertEqual(len(bad), 2)
        self.assertEqual([item["key"] for item in bad],
                         ["userId", "OrderTotal"])
        self.assertEqual([item["line"] for item in bad], [2, 4])

    def test_uppercase_key_flagged(self):
        bad, _ = findings_of('{\n  "Name": "Ada"\n}\n')
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["key"], "Name")

    def test_key_with_underscore_fails_camel_case(self):
        bad, _ = findings_of(
            '{\n  "user_id": 1\n}\n', style="camelCase")
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["key"], "user_id")
        self.assertIn("not camelCase", bad[0]["reason"])

    def test_camel_case_key_passes_camel_case(self):
        bad, _ = findings_of(
            '{\n  "userId": 1,\n  "orderTotal": 9.5\n}\n',
            style="camelCase")
        self.assertEqual(bad, [])

    def test_snake_case_key_passes_snake_case(self):
        bad, _ = findings_of(
            '{\n  "user_id": 1,\n  "order_total": 9.5\n}\n')
        self.assertEqual(bad, [])

    def test_key_starting_with_digit_flagged(self):
        bad, _ = findings_of('{\n  "2fa_code": 1\n}\n')
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["key"], "2fa_code")

    def test_key_starting_with_underscore_flagged(self):
        bad, _ = findings_of('{\n  "_user_id": 1\n}\n')
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["key"], "_user_id")

    def test_empty_key_flagged(self):
        bad, _ = findings_of('{\n  "": 1\n}\n')
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["key"], "")

    def test_key_with_hyphen_flagged(self):
        bad, _ = findings_of('{\n  "user-id": 1\n}\n')
        self.assertEqual(len(bad), 1)

    def test_key_with_space_flagged(self):
        bad, _ = findings_of('{\n  "user id": 1\n}\n')
        self.assertEqual(len(bad), 1)

    def test_single_letter_key_passes(self):
        bad, _ = findings_of('{\n  "a": 1\n}\n')
        self.assertEqual(bad, [])

    def test_key_with_digits_passes(self):
        bad, _ = findings_of('{\n  "retry_count_2": 3\n}\n')
        self.assertEqual(bad, [])

    def test_nested_object_key_flagged(self):
        bad, _ = findings_of(
            '{\n  "address": {\n    "StreetName": "Main St"\n  }\n}\n')
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["line"], 3)
        self.assertEqual(bad[0]["key"], "StreetName")

    def test_key_inside_array_of_objects_flagged(self):
        bad, _ = findings_of(
            '{\n  "tags": [\n    {\n      "tagName": "history"\n'
            '    }\n  ]\n}\n')
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["line"], 4)
        self.assertEqual(bad[0]["key"], "tagName")

    def test_deeply_nested_key_flagged(self):
        bad, _ = findings_of(
            '{\n  "a": {\n    "b": {\n      "BadKey": 1\n    }\n  }\n}\n')
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["line"], 4)

    def test_key_with_unicode_escape_checked_by_real_name(self):
        bad, _ = findings_of(
            '{\n  "user\\u005fid": 1\n}\n')
        self.assertEqual(bad, [])

    def test_key_with_escaped_quote_flagged(self):
        bad, _ = findings_of(
            '{\n  "ke\\"y": 1\n}\n')
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["key"], 'ke"y')

    def test_string_value_that_looks_like_a_key_not_checked(self):
        bad, _ = findings_of(
            '{\n  "note": "UserID wrote this"\n}\n')
        self.assertEqual(bad, [])

    def test_colon_inside_string_value_not_a_key(self):
        bad, _ = findings_of(
            '{\n  "url": "http://example.com"\n}\n')
        self.assertEqual(bad, [])

    def test_duplicate_keys_both_reported(self):
        bad, _ = findings_of(
            '{\n  "userId": 1,\n  "userId": 2\n}\n')
        self.assertEqual(len(bad), 2)
        self.assertEqual([item["line"] for item in bad], [2, 3])

    def test_empty_object_passes(self):
        bad, error = findings_of('{}\n')
        self.assertEqual(bad, [])
        self.assertIsNone(error)

    def test_empty_array_passes(self):
        bad, error = findings_of('[]\n')
        self.assertEqual(bad, [])
        self.assertIsNone(error)

    def test_top_level_array_checked(self):
        bad, _ = findings_of('[\n  {\n    "BadKey": 1\n  }\n]\n')
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["line"], 3)

    def test_top_level_scalar_passes(self):
        bad, error = findings_of('42\n')
        self.assertEqual(bad, [])
        self.assertIsNone(error)

    def test_invalid_json_is_an_error(self):
        bad, error = findings_of('not json at all\n')
        self.assertEqual(bad, [])
        self.assertIsNotNone(error)
        self.assertIn("not valid JSON", error)

    def test_key_on_last_line_reported(self):
        bad, _ = findings_of('{\n  "user_id": 1,\n  "BadKey": 2\n}')
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["line"], 3)

    def test_key_after_multiline_string_value(self):
        bad, _ = findings_of(
            '{\n  "note": "line one\\nline two",\n'
            '  "BadKey": 1\n}\n')
        self.assertEqual(len(bad), 1)
        self.assertEqual(bad[0]["line"], 3)

    def test_unknown_style_rejected(self):
        code, _, err = run_cli(
            ["--style", "PascalCase", "x.json"])
        self.assertEqual(code, 2)


class TestCli(unittest.TestCase):
    def test_clean_file_exit_0(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "ok.json", '{\n  "user_id": 1\n}\n')
            code, out, _ = run_cli([path])
            self.assertEqual(code, 0)
            self.assertIn("OK", out)
            self.assertIn("every key is snake_case", out)

    def test_flagged_file_exit_1(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "bad.json", '{\n  "userId": 1\n}\n')
            code, out, _ = run_cli([path])
            self.assertEqual(code, 1)
            self.assertIn(
                'FAIL %s: line 2: key "userId" is not snake_case'
                % path, out)
            self.assertIn("1 key(s) not snake_case", out)

    def test_folder_walk(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "a.json", '{\n  "user_id": 1\n}\n')
            write(tmp, "b.json", '{\n  "userId": 1\n}\n')
            write(tmp, "notes.txt", '{\n  "userId": 1\n}\n')
            code, out, _ = run_cli([tmp])
            self.assertEqual(code, 1)
            self.assertIn("Checked 2 file(s)", out)
            self.assertNotIn("notes.txt", out)

    def test_nested_folders(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "sub/deep.json", '{\n  "userId": 1\n}\n')
            code, out, _ = run_cli([tmp])
            self.assertEqual(code, 1)
            self.assertIn("deep.json", out)

    def test_no_recursive(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "top.json", '{\n  "user_id": 1\n}\n')
            write(tmp, "sub/deep.json", '{\n  "userId": 1\n}\n')
            code, out, _ = run_cli(["--no-recursive", tmp])
            self.assertEqual(code, 0)
            self.assertIn("OK — 1 file(s) checked", out)

    def test_exclude_skips_a_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, "a.json", '{\n  "userId": 1\n}\n')
            write(tmp, "skip.json", '{\n  "userId": 1\n}\n')
            code, out, _ = run_cli(["--exclude", "skip.json", tmp])
            self.assertEqual(code, 1)
            self.assertIn("Checked 1 file(s)", out)
            self.assertNotIn("skip.json", out)

    def test_git_folder_skipped_in_walk(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(tmp, ".git/hooks/bad.json", '{\n  "userId": 1\n}\n')
            write(tmp, "a.json", '{\n  "user_id": 1\n}\n')
            code, out, _ = run_cli([tmp])
            self.assertEqual(code, 0)
            self.assertIn("OK — 1 file(s) checked", out)

    def test_direct_file_checked_whatever_its_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "data.txt", '{\n  "userId": 1\n}\n')
            code, out, _ = run_cli([path])
            self.assertEqual(code, 1)
            self.assertIn("data.txt", out)

    def test_duplicate_paths_checked_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "a.json", '{\n  "userId": 1\n}\n')
            code, out, _ = run_cli([path, path])
            self.assertEqual(code, 1)
            self.assertIn("Checked 1 file(s)", out)

    def test_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "bad.json", '{\n  "userId": 1\n}\n')
            code, out, _ = run_cli(["--json", path])
            self.assertEqual(code, 1)
            data = json.loads(out)
            self.assertEqual(data["checked"], 1)
            self.assertEqual(data["findings"], 1)
            self.assertEqual(data["style"], "snake_case")
            self.assertEqual(
                data["files"][0]["findings"][0]["line"], 2)
            self.assertEqual(
                data["files"][0]["findings"][0]["key"], "userId")
            self.assertIsNone(data["files"][0]["error"])

    def test_stdin_clean(self):
        old_stdin = sys.stdin
        sys.stdin = io.StringIO('{\n  "user_id": 1\n}\n')
        try:
            code, out, _ = run_cli(["--stdin"])
        finally:
            sys.stdin = old_stdin
        self.assertEqual(code, 0)
        self.assertIn("every key is snake_case", out)

    def test_stdin_dirty(self):
        old_stdin = sys.stdin
        sys.stdin = io.StringIO('{\n  "userId": 1\n}\n')
        try:
            code, out, _ = run_cli(["--stdin"])
        finally:
            sys.stdin = old_stdin
        self.assertEqual(code, 1)
        self.assertIn('FAIL <stdin>: line 2: key "userId" is not '
                      "snake_case", out)

    def test_stdin_with_paths_is_usage_error(self):
        code, _, err = run_cli(["--stdin", "a.json"])
        self.assertEqual(code, 2)

    def test_style_with_stdin(self):
        old_stdin = sys.stdin
        sys.stdin = io.StringIO('{\n  "user_id": 1\n}\n')
        try:
            code, out, _ = run_cli(["--style", "camelCase", "--stdin"])
        finally:
            sys.stdin = old_stdin
        self.assertEqual(code, 1)
        self.assertIn("not camelCase", out)

    def test_style_with_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "a.json", '{\n  "user_id": 1\n}\n')
            code, out, _ = run_cli(
                ["--style", "camelCase", "--json", path])
            self.assertEqual(code, 1)
            data = json.loads(out)
            self.assertEqual(data["style"], "camelCase")
            self.assertEqual(data["findings"], 1)

    def test_no_paths_is_usage_error(self):
        code, _, err = run_cli([])
        self.assertEqual(code, 2)

    def test_missing_path_exit_2(self):
        code, _, err = run_cli(["/no/such/file.json"])
        self.assertEqual(code, 2)
        self.assertIn("no such file or folder", err)

    def test_empty_folder_exit_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, _, err = run_cli([tmp])
            self.assertEqual(code, 2)
            self.assertIn("no JSON files found", err)

    def test_bad_flag_exit_2(self):
        code, _, _ = run_cli(["--nope", "a.json"])
        self.assertEqual(code, 2)

    def test_version(self):
        code, out, _ = run_cli(["--version"])
        self.assertEqual(code, 0)
        self.assertIn("json_key_case_checker", out)

    def test_non_utf8_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "bad.json", b"\xff\xfe{}")
            code, out, _ = run_cli([path])
            self.assertEqual(code, 1)
            self.assertIn("not valid UTF-8", out)

    def test_invalid_json_file_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "bad.json", "not json at all\n")
            code, out, _ = run_cli([path])
            self.assertEqual(code, 1)
            self.assertIn("not valid JSON", out)

    def test_input_files_left_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = '{\n  "userId": 1\n}\n'
            path = write(tmp, "bad.json", text)
            run_cli([path])
            self.assertEqual(Path(path).read_text(), text)

    def test_cli_runs_from_another_folder(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "bad.json", '{\n  "userId": 1\n}\n')
            result = subprocess.run(
                [sys.executable,
                 str(REPO / "src" / "json_key_case_checker.py"), path],
                capture_output=True, text=True, cwd="/")
            self.assertEqual(result.returncode, 1)
            self.assertIn('key "userId" is not snake_case',
                          result.stdout)

    def test_cli_runs_under_fake_home(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = write(tmp, "bad.json", '{\n  "userId": 1\n}\n')
            env = dict(os.environ, HOME=tmp)
            result = subprocess.run(
                [sys.executable,
                 str(REPO / "src" / "json_key_case_checker.py"), path],
                capture_output=True, text=True, cwd=tmp, env=env)
            self.assertEqual(result.returncode, 1)

    def test_run_example_output_matches_sample(self):
        sample = (REPO / "examples" / "sample-output.md").read_text()
        result = subprocess.run(
            ["sh", str(REPO / "examples" / "run-example.sh")],
            capture_output=True, text=True, cwd=str(REPO))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), sample.strip())

    def test_readme_quotes_match_real_runs(self):
        readme = (REPO / "README.md").read_text()
        flagged = (REPO / "examples" / "flagged.json").read_text()
        bad, _ = checker.check_text(flagged)
        for item in bad:
            line = ("FAIL examples/flagged.json: line %d: %s"
                    % (item["line"], item["reason"]))
            self.assertIn(line, readme)
        self.assertIn(
            "OK — 1 file(s) checked, every key is snake_case.",
            readme)


class TestExamples(unittest.TestCase):
    def test_clean_example_passes(self):
        code, _, _ = run_cli([str(REPO / "examples" / "clean.json")])
        self.assertEqual(code, 0)

    def test_flagged_example_fails_with_three(self):
        bad, _ = checker.check_text(
            (REPO / "examples" / "flagged.json").read_text())
        self.assertEqual(len(bad), 3)
        self.assertEqual([item["line"] for item in bad], [2, 4, 6])
        self.assertEqual(bad[0]["key"], "userId")
        self.assertEqual(bad[1]["key"], "OrderTotal")
        self.assertEqual(bad[2]["key"], "StreetName")

    def test_flagged_example_under_camel_case(self):
        bad, _ = checker.check_text(
            (REPO / "examples" / "flagged.json").read_text(),
            style="camelCase")
        self.assertEqual(len(bad), 3)
        self.assertEqual([item["key"] for item in bad],
                         ["first_name", "OrderTotal", "StreetName"])

    def test_edge_example_passes(self):
        code, _, _ = run_cli([str(REPO / "examples" / "edge.json")])
        self.assertEqual(code, 0)


class TestHygiene(unittest.TestCase):
    def _repo_files(self, skip_tests=True):
        """Every file in the repo, minus .git and caches."""
        for path in REPO.rglob("*"):
            if path.is_dir():
                continue
            if ".git" in path.parts or "__pycache__" in path.parts:
                continue
            if path.suffix == ".pyc":
                continue
            if skip_tests and "tests" in path.parts:
                continue
            yield path

    def test_no_placeholder_text(self):
        banned = ["TODO", "coming soon", "lorem", "FIXME", "XXX"]
        hits = []
        for path in self._repo_files(skip_tests=True):
            text = path.read_text(errors="ignore")
            for word in banned:
                if word in text:
                    hits.append("%s: %s" % (path.name, word))
        self.assertEqual(hits, [])

    def test_no_absolute_paths(self):
        hits = []
        for path in self._repo_files(skip_tests=True):
            text = path.read_text(errors="ignore")
            for marker in ("/home/", "/Users/", "C:\\", "/tmp/"):
                if marker in text:
                    hits.append("%s: %s" % (path.name, marker))
        self.assertEqual(hits, [])

    def test_stdlib_imports_only(self):
        import ast
        stdlib = set(sys.stdlib_module_names)
        for target in (REPO / "src" / "json_key_case_checker.py",
                       REPO / "tests" / "test_json_key_case_checker.py"):
            tree = ast.parse(target.read_text())
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(a.name.split(".")[0]
                                    for a in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
            self.assertFalse(
                imported - stdlib - {"json_key_case_checker"},
                (target.name, imported))
            self.assertNotIn("yaml", imported)

    def test_no_network_use_in_src(self):
        src = (REPO / "src" / "json_key_case_checker.py").read_text()
        for marker in ("urllib.request", "requests", "socket",
                       "http.client", "urlopen", "urlretrieve"):
            self.assertNotIn(marker, src, marker)

    def test_gitignore_lists_env_first(self):
        lines = (REPO / ".gitignore").read_text().splitlines()
        self.assertTrue(lines, ".gitignore is empty")
        self.assertEqual(lines[0], ".env")

    def test_ci_runs_the_test_suite(self):
        ci = (REPO / ".github" / "workflows" / "ci.yml").read_text()
        self.assertIn("python3 -m unittest discover -s tests", ci)
        self.assertIn("ubuntu-latest", ci)
        self.assertIn("3.12", ci)
        self.assertIn("actions/checkout", ci)
        self.assertIn("setup-python", ci)
        self.assertIn("push", ci)
        self.assertIn("pull_request", ci)

    def test_readme_names_the_neighbouring_repos(self):
        readme = (REPO / "README.md").read_text()
        for name in ("json-key-sort-checker-cli",
                     "json-required-key-checker-cli",
                     "json-duplicate-key-checker-cli"):
            self.assertIn(name, readme)


if __name__ == "__main__":
    unittest.main(verbosity=2)
