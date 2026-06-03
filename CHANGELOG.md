# Changelog

## [4.2.0](https://github.com/trevor-nichols/agentrules-architect/compare/v4.1.0...v4.2.0) (2026-06-03)


### Features

* **models:** add current provider model presets ([9a5da4a](https://github.com/trevor-nichols/agentrules-architect/commit/9a5da4a11f465c34ed51aad9c019ca698eeec558))


### Bug Fixes

* **models:** add Gemini 3.5 and remap retired presets ([3726b03](https://github.com/trevor-nichols/agentrules-architect/commit/3726b0329d6ebb80fb3c935114f10dd1caacfb4e))
* **models:** harden codex and claude runtime selection ([c6d42cb](https://github.com/trevor-nichols/agentrules-architect/commit/c6d42cb56ce52e76e940a5ccb6cbe1b603bb32bf))
* **xai:** migrate Grok presets to canonical models ([6ba5c56](https://github.com/trevor-nichols/agentrules-architect/commit/6ba5c5673e520933c8c184ce861283ec66baa2c1))


### Documentation

* **readme:** refresh project overview ([309f2e7](https://github.com/trevor-nichols/agentrules-architect/commit/309f2e7539daf27936d4746c363e21deaf1c02ec))

## [4.1.0](https://github.com/trevor-nichols/agentrules-architect/compare/v4.0.0...v4.1.0) (2026-05-08)


### Features

* **agents:** add Claude Code SDK adapter ([5d1cf06](https://github.com/trevor-nichols/agentrules-architect/commit/5d1cf06e45f808043020ed59c563303c385a2ca7))
* **claude-code:** add Claude Agent SDK runtime integration ([9558f06](https://github.com/trevor-nichols/agentrules-architect/commit/9558f064ea3248a90abb48e9901f679456e0243e))
* **claude-code:** add runtime execution guardrails ([2543d4b](https://github.com/trevor-nichols/agentrules-architect/commit/2543d4bc527fb093abbe2f19d80f2f9e4280d714))
* **cli:** add Claude Code runtime settings ([dd24f18](https://github.com/trevor-nichols/agentrules-architect/commit/dd24f184a6c4bc744697b84fcaa31348d54e7307))
* **config:** add Claude Code runtime foundation ([0299fbb](https://github.com/trevor-nichols/agentrules-architect/commit/0299fbb87f1bbba2e7314cb2dfc17a6d90d3fae9))
* **models:** wire Claude Code runtime presets ([efecbcf](https://github.com/trevor-nichols/agentrules-architect/commit/efecbcf150c46cbff5e6b2ccb2c5f3ff4d20177d))


### Bug Fixes

* **analysis:** fail fast on final generation errors ([64c862c](https://github.com/trevor-nichols/agentrules-architect/commit/64c862c3255cd18e42fa67e03c6af120c7b5e2d3))
* **claude-code:** defer default CLI resolution to SDK ([27e87fe](https://github.com/trevor-nichols/agentrules-architect/commit/27e87feb7ef18e620bb3b94fd7d9879c500e55ad))
* **claude-code:** enforce streaming query timeouts ([3015191](https://github.com/trevor-nichols/agentrules-architect/commit/301519114082c456d8dda039c6424d6d7f05fd08))
* **claude-code:** keep token preflight local ([bb44987](https://github.com/trevor-nichols/agentrules-architect/commit/bb449870d7649b1922ca1f9d0f0f1b2964a7ad67))
* **claude-code:** resolve configured cli path ([b6dd91f](https://github.com/trevor-nichols/agentrules-architect/commit/b6dd91f03901033c59fa3d364b7a61e27f559f52))
* **claude-code:** scrub inherited API key env ([0841e06](https://github.com/trevor-nichols/agentrules-architect/commit/0841e067624ba6556d7be36b7985b3d1ae6fe844))
* **claude-code:** validate sdk default runtime ([7f9deca](https://github.com/trevor-nichols/agentrules-architect/commit/7f9deca23e92d7f901e0bf9180b6258faa68af73))


### Documentation

* **claude-code:** document runtime rollout ([44cf0d3](https://github.com/trevor-nichols/agentrules-architect/commit/44cf0d321bbeb6786ad72875334f3f5d3951f7cb))

## [4.0.0](https://github.com/trevor-nichols/agentrules-architect/compare/v3.8.0...v4.0.0) (2026-05-05)


### ⚠ BREAKING CHANGES

* **execplan:** deprecate archive in favor of complete

### Features

* **execplan:** deprecate archive in favor of complete ([8148fb0](https://github.com/trevor-nichols/agentrules-architect/commit/8148fb0de1dd49d6636fa3e882982d12f5429471))

## [3.8.0](https://github.com/trevor-nichols/agentrules-architect/compare/v3.7.0...v3.8.0) (2026-04-25)


### Features

* **models:** add GPT-5.5 presets and defaults ([72b7131](https://github.com/trevor-nichols/agentrules-architect/commit/72b71312d5ac3fd32858b2bac116fd7df968de52))
* **models:** add GPT-5.5 presets and defaults ([1ecf656](https://github.com/trevor-nichols/agentrules-architect/commit/1ecf65695d165c820e29f7034cc9cdc1de390a8c))

## [3.7.0](https://github.com/trevor-nichols/agentrules-architect/compare/v3.6.0...v3.7.0) (2026-04-05)


### Features

* **execplan:** make complete the canonical history layout ([abd52a8](https://github.com/trevor-nichols/agentrules-architect/commit/abd52a8862932b95f7e50068f34110da96e8d2ce))


### Bug Fixes

* **codex:** harden large phase transport handling ([bb17497](https://github.com/trevor-nichols/agentrules-architect/commit/bb174974c776c5888cc792f451b1227080236d81))
* **execplan:** allow read-only plan locks ([290fd67](https://github.com/trevor-nichols/agentrules-architect/commit/290fd673ff28617dd488ac0f1eb7bc93b84296e0))
* **execplan:** serialize milestone sequence allocation ([66e4d88](https://github.com/trevor-nichols/agentrules-architect/commit/66e4d88f02106a9739b7200263c07d6fcddf45a9))
* **snapshot:** simplify max-depth tree marker ([1c4f7d1](https://github.com/trevor-nichols/agentrules-architect/commit/1c4f7d19d6d0f369f99bcb80d1f04581cd482d7d))

## [3.6.0](https://github.com/trevor-nichols/agentrules-architect/compare/v3.5.0...v3.6.0) (2026-03-21)


### Features

* **openai:** add GPT-5.4 mini and nano presets ([269696a](https://github.com/trevor-nichols/agentrules-architect/commit/269696a324b7c9967ccb867ac2ee1a84fd98ee22))
* **openai:** add GPT-5.4 mini and nano presets ([e5a435d](https://github.com/trevor-nichols/agentrules-architect/commit/e5a435d52a2d4d0cf7d0d6d1284b86dd69c2f9b0))

## [3.4.3](https://github.com/trevor-nichols/agentrules-architect/compare/v3.4.2...v3.4.3) (2026-03-11)


### Bug Fixes

* **ci:** align release-please with vX.Y.Z tag history ([f2d48d6](https://github.com/trevor-nichols/agentrules-architect/commit/f2d48d690a12494080af4c623d438d1cf5f49762))
