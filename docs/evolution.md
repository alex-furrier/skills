# Catalog evolution

The repository began as a portable engineering-skills catalog on 2026-08-28. [Commit `215df31ace7523d0a22ebe9caf7c777d6645a6ba`](https://github.com/safurrier/skills/commit/215df31ace7523d0a22ebe9caf7c777d6645a6ba) introduced the initial catalog, validation scripts, Context source, and Writing source.

On 2026-09-10, [PR #3](https://github.com/safurrier/skills/pull/3), merged as [`2a186eec714e57e390582f8c9e9d6aa0fe18c56d`](https://github.com/safurrier/skills/commit/2a186eec714e57e390582f8c9e9d6aa0fe18c56d), packaged Context Engineering as a self-contained Claude plugin and removed Writing Check's duplicate package tree.

On 2026-09-22, [PR #7](https://github.com/safurrier/skills/pull/7), merged as [`4c46e8ca6637471f7bf1cc4a1091d0c0149b3e35`](https://github.com/safurrier/skills/commit/4c46e8ca6637471f7bf1cc4a1091d0c0149b3e35), added independently installable Context Engineering and Writing Check packages. It added canonical root Context skills and the projection script that checks the Context plugin against those sources. This established the current release boundary: root skills are canonical, the Context plugin is checked projection output, and packaged commands provide deterministic analysis without another checkout.

This history records only retained boundaries. Current behavior belongs in `SPEC.md` at the repository root and [architecture](architecture.md).
