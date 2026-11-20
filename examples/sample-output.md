== examples/clean.json ==
OK — 1 file(s) checked, every key is snake_case.

== examples/flagged.json ==
FAIL examples/flagged.json: line 2: key "userId" is not snake_case
FAIL examples/flagged.json: line 4: key "OrderTotal" is not snake_case
FAIL examples/flagged.json: line 6: key "StreetName" is not snake_case
Checked 1 file(s), 3 key(s) not snake_case in 1 file(s).

== examples/edge.json ==
OK — 1 file(s) checked, every key is snake_case.

== examples/ : the whole folder ==
FAIL examples/flagged.json: line 2: key "userId" is not snake_case
FAIL examples/flagged.json: line 4: key "OrderTotal" is not snake_case
FAIL examples/flagged.json: line 6: key "StreetName" is not snake_case
Checked 3 file(s), 3 key(s) not snake_case in 1 file(s).

== examples/flagged.json with --style camelCase ==
FAIL examples/flagged.json: line 3: key "first_name" is not camelCase
FAIL examples/flagged.json: line 4: key "OrderTotal" is not camelCase
FAIL examples/flagged.json: line 6: key "StreetName" is not camelCase
Checked 1 file(s), 3 key(s) not camelCase in 1 file(s).
