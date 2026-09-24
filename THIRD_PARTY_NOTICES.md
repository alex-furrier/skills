# Third-party notices

## Google Vale rules

`packages/writing-check/src/writing_check/vale/styles/GoogleDocs/` contains reviewed rules from [vale-cli/Google](https://github.com/vale-cli/Google) v0.7.1, commit `56b01fed2532273121abcee1e7359483c879628f`. They are distributed under the MIT License; the required license is at `vale/vendor/Google-LICENSE`. The shipped `vale/vendor/Google-NOTICE.md` attributes the upstream implementation's source, the [Google Developer Documentation Style Guide](https://developers.google.com/style) ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)), for any reused or adapted guide text. CC BY does not replace the rules' MIT license or cover Google trademarks. Neither Writing Check nor the upstream rules are maintained or endorsed by Google. `upstream-lock.json` records source and vendored digests and advisory-level normalization. Of the 34 vendored YAML rules, 9 are byte-identical and 25 differ only in severity; Google word-list rules are intentionally excluded.

Writing Check pins the PyPI `vale` dependency, which downloads its executable on first use. See `provenance.json` for every shipped file's origin decision.
