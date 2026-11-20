# Security Policy

This tool runs locally, collects no data, sends nothing anywhere, and needs no API key or secret. It only reads the JSON files you point it at, and it never rewrites a file and never changes anything. It writes nothing except the report on standard output (and usage errors on standard error). It never fetches a URL: remote addresses are skipped, not opened.

If you find a case where the tool edits a file, reports a pass for a JSON file holding a key in the wrong case, or flags a key that matches the chosen style, please open an issue describing the exact commands and input.
