# json-key-case-checker-cli

Check JSON object keys all use one case style, fail CI when one does not.

[![CI](https://github.com/haiderstudio/json-key-case-checker-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/haiderstudio/json-key-case-checker-cli/actions/workflows/ci.yml) [![Licence: MIT](https://img.shields.io/badge/Licence-MIT-yellow.svg)](LICENSE)

## What it does

`json_key_case_checker` reads each JSON file,
checks the keys of every object — at every nesting
level — all use one case style (snake_case by
default, or camelCase with `--style camelCase`),
and reports each key that does not match, with the
file and the line number. It exits 1 when any key
fails, so it can fail a CI run. A file whose keys
all match exits 0.

- A config or API payload mixing `userId` and
  `user_id` forces every consumer to guess per key
  — the failure is a silent missing key at runtime,
  far from the file that caused it. A gate that
  names the exact key and line turns it into a
  rename before the file ships.
- snake_case means lowercase letters, digits and
  underscores, starting with a letter: `user_id`,
  `order_total`, `retry_count`. camelCase means
  starting with a lowercase letter, letters and
  digits only, no underscores: `userId`,
  `orderTotal`, `retryCount`. A single lowercase
  word (`name`, `id`) is valid in both styles.
- Keys inside arrays are checked too — an object
  inside an array is still an object, and its keys
  still have to match. A key written with a Unicode
  escape, such as `"user\u005fid"`, is checked by
  its real name, `user_id`, and passes.
- A file given directly on the command line is
  always checked, whatever its name. A folder is
  walked for files ending in `.json` only,
  recursively by default (`--no-recursive` stops
  at the top level). `.git` folders are never
  walked, and directory links are never followed.
- `--json` prints the result as JSON, and `--stdin`
  checks one JSON document read from standard input.
- A file that is not valid JSON is reported, not
  passed: case is meaningless when the file does
  not parse. A file that cannot be read — a file
  that is not valid UTF-8 — is reported as an error
  and fails the check the same way a finding does.

## Who it is for

Anyone who keeps JSON configs or API payloads —
which is every project with a config file. One
mixed-case key hides in a file copied from another
project, and the consumer fails silently for a
reason no one traces back to a key name. This is
the gate that names it at the pull request, before
it ships.

## What it does NOT do

- It does not check whether keys are sorted. That
  is repo #109, json-key-sort-checker-cli, which
  checks key SORT order — the case convention of
  the keys is a different check on the same keys: a
  file can be sorted and still mix cases, and a file
  can be one case throughout and still be unsorted.
- It does not check whether a required key is
  present. That is repo #126,
  json-required-key-checker-cli — a missing key is
  a different check on the same files.
- It does not check duplicate keys. That is repo
  #48, json-duplicate-key-checker-cli — a duplicated
  key is a different check on the same files.
- It does not rewrite a key into the chosen style
  or remove it. It reports, you rename the key.
- It never touches the network, and it only reads
  the files and folders you point it at.

## How this differs

- A fresh search of GitHub on Nov 18, 2026 found 0
  results for `"json-key-case-checker-cli"` and 0
  results for `json key case checker`. The field is
  empty for this job.
- So the narrow slice stands: the case convention
  of JSON object keys only, per-key reporting with
  line numbers, a CI exit code, and a report-only
  tool that never edits a file.

## Install

```sh
git clone https://github.com/haiderstudio/json-key-case-checker-cli.git
cd json-key-case-checker-cli
```

There is nothing else to install: Python 3.10 or newer,
standard library only, no dependencies.

## Usage

Check one JSON file:

```sh
python3 src/json_key_case_checker.py config.json
```

A file whose keys are all snake_case passes:

```sh
$ python3 src/json_key_case_checker.py examples/clean.json
OK — 1 file(s) checked, every key is snake_case.
```

A file with keys in the wrong case fails, with the
line for each one:

```sh
$ python3 src/json_key_case_checker.py examples/flagged.json
FAIL examples/flagged.json: line 2: key "userId" is not snake_case
FAIL examples/flagged.json: line 4: key "OrderTotal" is not snake_case
FAIL examples/flagged.json: line 6: key "StreetName" is not snake_case
Checked 1 file(s), 3 key(s) not snake_case in 1 file(s).
```

Check with the camelCase style instead:

```sh
$ python3 src/json_key_case_checker.py --style camelCase examples/flagged.json
FAIL examples/flagged.json: line 3: key "first_name" is not camelCase
FAIL examples/flagged.json: line 4: key "OrderTotal" is not camelCase
FAIL examples/flagged.json: line 6: key "StreetName" is not camelCase
Checked 1 file(s), 3 key(s) not camelCase in 1 file(s).
```

Check a whole folder (`.json` files only):

```sh
$ python3 src/json_key_case_checker.py examples/
FAIL examples/flagged.json: line 2: key "userId" is not snake_case
FAIL examples/flagged.json: line 4: key "OrderTotal" is not snake_case
FAIL examples/flagged.json: line 6: key "StreetName" is not snake_case
Checked 3 file(s), 3 key(s) not snake_case in 1 file(s).
```

Check one document from standard input:

```sh
$ printf '{\n  "userId": 1\n}\n' | python3 src/json_key_case_checker.py --stdin
FAIL <stdin>: line 2: key "userId" is not snake_case
Checked 1 file(s), 1 key(s) not snake_case in 1 file(s).
```

Machine-readable output:

```sh
$ python3 src/json_key_case_checker.py --json examples/flagged.json
{
  "files": [
    {
      "path": "examples/flagged.json",
      "findings": [
        {
          "line": 2,
          "key": "userId",
          "reason": "key \"userId\" is not snake_case"
        },
        {
          "line": 4,
          "key": "OrderTotal",
          "reason": "key \"OrderTotal\" is not snake_case"
        },
        {
          "line": 6,
          "key": "StreetName",
          "reason": "key \"StreetName\" is not snake_case"
        }
      ],
      "error": null
    }
  ],
  "checked": 1,
  "findings": 3,
  "style": "snake_case"
}
```

Exit codes: 0 when every key matches the style, 1
when any key or file error is found, 2 for a usage
error (a missing path, a bad flag, a bad `--style`,
or no `.json` files found).

## Examples

One key in the wrong case is caught with its line:

```sh
$ printf '{\n  "userId": 1,\n  "user_id": 2\n}\n' > two.json
$ python3 src/json_key_case_checker.py two.json
FAIL two.json: line 2: key "userId" is not snake_case
Checked 1 file(s), 1 key(s) not snake_case in 1 file(s).
```

The same file passes under camelCase — only the
snake_case key is now the odd one out:

```sh
$ python3 src/json_key_case_checker.py --style camelCase two.json
FAIL two.json: line 3: key "user_id" is not camelCase
Checked 1 file(s), 1 key(s) not camelCase in 1 file(s).
```

A key written with a Unicode escape is checked by
its real name, so `"user\u005fid"` is `user_id` and
passes:

```sh
$ printf '{\n  "user_id": 1,\n  "user\\u005fid": 2\n}\n' > esc.json
$ python3 src/json_key_case_checker.py esc.json
OK — 1 file(s) checked, every key is snake_case.
```

Single-word keys and keys with digits pass —
`examples/edge.json` holds both, and it passes:

```sh
$ python3 src/json_key_case_checker.py examples/edge.json
OK — 1 file(s) checked, every key is snake_case.
```

A file that is not valid JSON is reported, not passed:

```sh
$ printf 'not json at all\n' > bad.json
$ python3 src/json_key_case_checker.py bad.json
FAIL bad.json: not valid JSON: Expecting value: line 1 column 1 (char 0)
Checked 1 file(s), 1 key(s) not snake_case in 1 file(s).
```

Run every bundled example at once with `sh
examples/run-example.sh` — the output is saved in
[examples/sample-output.md](examples/sample-output.md).

## How it is tested

```sh
python3 -m unittest discover -s tests
```

The tests cover keys (a plain bad key, several bad
keys in order, an uppercase key, a key with an
underscore under camelCase, a key starting with a
digit, a key starting with an underscore, an empty
key, a key with a hyphen, a key with a space, a
single-letter key, a key with digits, a nested
object key, a key inside an array of objects, a
deeply nested key, a key with a Unicode escape, a
key with an escaped quote, a string value that
looks like a key, a colon inside a string value,
duplicate keys both reported, an empty object, an
empty array, a top-level array, a top-level scalar,
camelCase style passing and failing, an unknown
style rejected), line numbers (keys on the right
lines, a key on the last line, a key after a
multi-line string value), the CLI (exit 0/1/2,
folder walking for several JSON files, nested
folders, `--no-recursive`, `--exclude`, `.git`
skipped, a direct file checked whatever its name,
duplicate paths checked once, `--json` output,
`--stdin`, `--style` with `--json`, `--style`
with `--stdin`, bad flags, missing paths, empty
folders, `--version`, a non-UTF-8 file reported, an
invalid JSON file reported, input files left
unchanged, the tool run from `/` and under a fake
HOME), the bundled examples (sample output compared
against a fresh run, and the README-quoted outputs
checked against it), and hygiene checks (no
placeholder text, no absolute paths, stdlib imports
only, no network use in the source, `.env` first in
`.gitignore`, CI file runs the test suite, README
names the neighbouring repos).

## Contributing

Small, focused improvements are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

MIT — see [LICENSE](LICENSE).

## Original work

This tool was written from scratch for this repo. The
idea of checking a naming convention is not new, and
the snake_case and camelCase rules are common
conventions — but no existing tool does this one job,
checking local JSON object keys for one case style
as a tested command-line gate, as the search above
shows — and every line of code here is original,
built on nothing but Python's standard library. The
line-finding scan (a string followed by a colon is
an object key) is the same technique repo #109,
json-key-sort-checker-cli, uses for its own
different check, and is credited here.
