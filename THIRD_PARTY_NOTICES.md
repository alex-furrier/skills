# Third-party notices

## Google Vale rules

`packages/writing-check/src/writing_check/vale/styles/GoogleDocs/` contains reviewed rules from [vale-cli/Google](https://github.com/vale-cli/Google) v0.7.1, commit `56b01fed2532273121abcee1e7359483c879628f`. They are distributed under the MIT License; the required license is at `vale/vendor/Google-LICENSE`. `upstream-lock.json` records source and vendored digests and advisory-level normalization. Google word-list rules are intentionally excluded.

Writing Check pins the PyPI `vale` dependency, which downloads its executable on first use. See `provenance.json` for every shipped file's origin decision.
