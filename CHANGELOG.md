# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [0.1.0] — 2026-06-29

### Added

- `AGEC` core data model with intent, execution path, data permissions, and lifecycle state machine.
- `AGECStatus` enum with guarded transitions (`AGECTransitionError` raised on illegal moves).
- `Policy` dataclass with allowlist checks for intents, tools, purposes, legal bases, and blocked data categories.
- `DEFAULT_LEGAL_BASES` — GDPR Article 6 vocabulary built-in.
- `AGECValidator` — deterministic, ordered validation pipeline with full audit recording.
- `AuditLog` — append-only in-memory log with `save_json` / `load_json` for persistence and replay.
- `@guard(...)` decorator — one-line governance enforcement; `Policy` and `AGECValidator` built once at decoration time.
- `AGECBlockedError` — `PermissionError` subclass carrying the denial reason and AGEC context.
- `validate()` — convenience function for one-shot validation.
- `ExecutionPath.deterministic_hash()` — SHA-256 hash for replay verification.
- Comprehensive test suite covering all validator checks, state machine, audit persistence, and guard decorator.
- Full docstrings across all public classes and methods.

[Unreleased]: https://github.com/onur-esmercan/agec/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/onur-esmercan/agec/releases/tag/v0.1.0
