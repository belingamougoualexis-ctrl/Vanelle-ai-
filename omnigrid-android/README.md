# VANELLE OMNIGRID AI — Android

Standalone Android app module added to the existing Vanelle-ai- repository; existing projects and files are preserved.

## Build and verification
- Android application ID: ai.vanelle.omnigrid (debug builds use ai.vanelle.omnigrid.debug)
- minSdk 26, target/compile SDK 35, Java 17, Gradle 8.10.2
- CI builds debug and release APKs and launches the app in an Android 35 emulator using an Espresso smoke test.
- APKs are uploaded as workflow artifacts after all preceding build/test steps succeed.

## Included
- Native Android task submission and in-session task journal
- Approval dialog for a list of sensitive-action keywords
- Configurable HTTPS endpoint and exact model ID for OpenAI-compatible chat-completions providers
- API key encrypted with Android Keystore AES-GCM
- Real provider connection test and visible HTTP/provider errors
- Prompting that requires the model to distinguish proposed steps from actions actually performed

## Explicit limits
This is an AI-assisted planner, not a universal autonomous computer grid yet. It does not ship every AI model, contain local GGUF inference, install model weights, operate remote Windows/macOS/Linux agents, execute shell commands on other computers, or include a production multi-user backend. The approval detector is a basic keyword gate, not a complete safety system. Provider use requires a valid key and access to the selected model. Emulator smoke tests do not replace testing on the user's specific physical phone. Release APK is unsigned; distribution-grade signing requires a separately configured signing key.
