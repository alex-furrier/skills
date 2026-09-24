# Google Vale policy attribution

The GoogleDocs Vale rules in this package are adapted from [vale-cli/Google v0.7.1](https://github.com/vale-cli/Google/tree/v0.7.1) (commit `56b01fed2532273121abcee1e7359483c879628f`). The upstream rules are distributed under the MIT License; see [Google-LICENSE](Google-LICENSE), copyright Joseph Kato.

The upstream project describes its rules as an implementation of the [Google Developer Documentation Style Guide](https://developers.google.com/style), whose text is available under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This attribution identifies the source guide for any reused or adapted guide text; it does not replace the upstream rules' MIT license or apply CC BY to the entire policy. Google trademarks are not covered by the guide's CC BY terms.

This package omits upstream WordList.yml and WordListCase.yml, renames the rule namespace to GoogleDocs, and normalizes rule severity levels to suggestions. Of the 34 vendored YAML rules, 9 are byte-identical to upstream and 25 differ only by severity normalization. This package is not maintained or endorsed by Google.
