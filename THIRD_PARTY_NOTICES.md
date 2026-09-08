# Third-party notices

## Google Vale rules

`packages/writing-check/vale/styles/GoogleDocs/` and the matching
`skills/writing/writing-check/vale/styles/GoogleDocs/` copy reviewed rules from
[vale-cli/Google](https://github.com/vale-cli/Google) v0.7.1, commit
`56b01fed2532273121abcee1e7359483c879628f`. They are distributed under the
MIT License; each copy includes the required license at `vale/vendor/Google-LICENSE`.
The matching `upstream-lock.json` records the source archive digest, source and
vendored rule digests, and advisory-level normalization. Google word-list rules
are intentionally excluded because their contextual product substitutions are
not part of this catalog.

Vale itself is a required external dependency for Writing Check and is not
bundled. See `provenance.json` for every shipped file's origin decision.
