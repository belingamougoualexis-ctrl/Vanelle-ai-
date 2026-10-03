# ProofRail

ProofRail is a local-first Android workspace for controls, evidence, human decision gates and a tamper-evident audit chain.

## Product principles

- No seeded business data, fake users or fabricated metrics.
- Critical state is stored locally in SQLite.
- Mutations append a SHA-256 chained audit event.
- Checks are deterministic: a control passes only when its evidence threshold is met.
- Decision requests require an explicit human approval or rejection.
- Workspace export and restore use a versioned JSON format and restore only after the audit chain verifies.
- The Android manifest does not request network permission in this release.

## Android

- Application ID: `com.proofrail.app`
- Version: `1.0.0`
- minSdk: 26 (Android 8.0)
- targetSdk: 35
- Compile SDK: 35
- Release build: R8 minification + resource shrinking.

## CI validation

GitHub Actions runs:
1. Kotlin/JUnit unit tests.
2. Debug compilation.
3. Instrumented tests on a real Android emulator image.
4. Release compilation.
5. APK package/version verification with Android `aapt`.

The CI artifact is intentionally an **unsigned release APK**. A persistent production signing key must be stored as a GitHub secret (or in an external secure signing service) before distributing updates through a public app store. Never commit the keystore or private key to this repository.

## Current scope

This public mobile release is a standalone local workspace. It does not pretend to provide cloud multi-tenancy, SSO, third-party connectors, automated external actions, billing or enterprise compliance certification. Those require server/integration infrastructure and are separate engineering work.

## Privacy and data

The current release does not upload workspace records. Export creates a JSON backup chosen by the user; erase permanently deletes the local SQLite database.

## Uptodown release checklist

Before publication, provide one signed APK for the exact version, a square app icon, accurate app/package/version metadata, a short description under 70 characters, a full description, screenshots and a featured image according to Uptodown's developer submission requirements. Do not submit the unsigned CI artifact.
