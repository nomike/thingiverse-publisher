# Changelog

## [0.6.1](https://github.com/nomike/thingiverse-publisher/compare/v0.6.0...v0.6.1) (2026-11-23)


### Bug Fixes

* send a custom User-Agent to avoid Cloudflare 403 ([#7](https://github.com/nomike/thingiverse-publisher/issues/7)) ([bccad99](https://github.com/nomike/thingiverse-publisher/commit/bccad995e6b719129b9d0f04a7851312f72227d8))
* validate license codes and exit non-zero on API failure ([#8](https://github.com/nomike/thingiverse-publisher/issues/8)) ([2df1ac5](https://github.com/nomike/thingiverse-publisher/commit/2df1ac55950b9df608541d1b3112821d2156b839))


### Documentation

* fix OAuth instructions to use localhost callback ([#5](https://github.com/nomike/thingiverse-publisher/issues/5)) ([a84adc0](https://github.com/nomike/thingiverse-publisher/commit/a84adc0c4ad5f0fb01f5d3cf3a4d7bc7f43f0306))

## [0.6.0](https://github.com/nomike/thingiverse-publisher/compare/v0.5.1...v0.6.0) (2026-03-15)


### Features

* add GitHub Actions workflow for PyPI publishing and update CI ([#4](https://github.com/nomike/thingiverse-publisher/issues/4)) ([f4cf73a](https://github.com/nomike/thingiverse-publisher/commit/f4cf73a5388068819ee51902117354a11f2ca4fb))


### Bug Fixes

* **ci:** add pre-commit to dev deps, run via python -m ([dceede5](https://github.com/nomike/thingiverse-publisher/commit/dceede54a3182dde6d89a16647a09588175e6909))
* remove unused global config in load_config and update docstring ([6d45d92](https://github.com/nomike/thingiverse-publisher/commit/6d45d92e5fcec80a2bc68ff61dc6ad0e9d6732b0))
* single source of truth for version and release-please path ([50a270e](https://github.com/nomike/thingiverse-publisher/commit/50a270ed8e48b333b8d0a7b6a2e08daf3f391957))
* use stdlib json for config, add Python 3.13/3.14 ([3f498eb](https://github.com/nomike/thingiverse-publisher/commit/3f498eb9301535ad9c1acd1391012db33f11677f))
