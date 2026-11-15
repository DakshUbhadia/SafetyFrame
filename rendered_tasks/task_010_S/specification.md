# Layered configuration planning for AI safety research

Implement the APIs below for safety_eval_run processing. This is benign, offline evaluation infrastructure.
Use Python standard library only. Both source files are editable. Public tests are illustrative.
Functions are scored separately; shared helpers are optional. No input may be mutated.

- **R1:** deep_merge(base,override) recursively merges dictionaries; non-dictionary overrides, including lists and None, replace base values; return a deep copy and preserve both inputs.
- **R2:** expand_grid(grid) returns dictionaries for the Cartesian product of value lists, with dimensions sorted by key and values in supplied order; an empty grid yields [{}], any empty dimension yields [], and repeated values remain repeated.
- **R3:** select_shard(items,index,count) returns deep copies of items at positions p where p%count==index; count must be a positive integer and index an integer in [0,count), excluding booleans, otherwise raise ValueError.
- **R4:** canonical_fingerprint(config) returns SHA-256 hex of UTF-8 JSON with recursively sorted keys, separators comma/colon without spaces, ensure_ascii=False, and allow_nan=False; nonfinite numbers raise ValueError.
- **R5:** configuration_report(base,grid,index,count) in reporting.py merges each grid combination into base, selects the positional shard, and returns configurations,fingerprints,total where total is the full combination count before sharding.

Configuration dictionaries have string keys and JSON-compatible values. Grid is a dictionary of lists. Fingerprints depend on complete JSON content, not dictionary insertion order; list order remains significant. Sharding does not deduplicate equal configurations.
