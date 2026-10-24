# Vanelle AirCore Zero

This directory is an isolated integration area for AirCore Zero. It deliberately does not replace the repository's ProofRail or Vanelle Academy projects.

## Current deliverable status

The current prototype supplied for this project is a Progressive Web App (PWA): HTML, a web manifest, and a service worker. It is not an Android APK and does not establish the proposed physical information-persistence effect.

## Scientific boundary

AirCore Zero's central claim—recovering an arbitrary message bit-for-bit after the transmitter has been off for a year without conventional storage—has not been demonstrated. Software simulation and unit tests cannot establish that physical claim. A valid experiment needs a specified physical mechanism, blinded random messages, controls against hidden copies or leakage, preregistered decoding criteria, long-duration measurements, and independent replication.

## Integration rules

- Keep this app isolated under `aircore-zero/`.
- Do not change root ProofRail Gradle configuration or `lucky-languages/android/`.
- Preserve the PWA as the source reference.
- A native Android wrapper must package the actual PWA source, not a placeholder.
- Publish an APK only after a dedicated build has succeeded and the artifact has been checked.
- Report software tests separately from physical experiments.

## Source status

The PWA source archive currently available in the working session has not yet been committed into this repository. Until its contents are committed and the Android build is run, no AirCore Zero APK should be described as available.
