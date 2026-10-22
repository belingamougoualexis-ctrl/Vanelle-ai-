# VANELLE OMNIGRID AI — local-first Android

## Local AI runtime
- Native on-device text generation through llama.cpp Android AAR (dev.ffmpegkit-maintained:llama-android:0.1.1).
- Default model: Qwen2.5-0.5B-Instruct GGUF Q4_0 (about 429 MB), Apache-2.0 model license.
- Initial download uses Android DownloadManager. Model is checked for GGUF magic and the published SHA-256 before it is trusted.
- After model download, prompt inference is local: no provider URL, API key, or prompt upload is used by the app.
- Model load uses a 2,048-token context and 2–4 CPU threads; inference releases native model memory after each request.
- A built-in self-test performs real inference and shows the model's actual response.
- Allow-listed offline device tools execute explicit `calc:`, `note:`, `notes:list`, `time:now`, `device:info`, and `tools:list` commands without requiring the model or internet. Arithmetic is parsed locally; notes are stored in the app-private directory.
- Instrumentation tests cover the actual calculator, note write/read, device metadata, and local clock commands.

## Build / tests
- Android SDK 35, Java 17, Kotlin 2.0.21, Gradle 8.10.2.
- GitHub Actions builds debug and release APKs, then runs the Android emulator UI smoke test.
- CI build proves compilation; it does not prove a model was downloaded or real local inference succeeded on a physical phone. The in-app self-test is the real inference test to run after download.
- The bundled llama-android AAR documents arm64-v8a support. A device/emulator must support that ABI; 429 MB download plus model/cache memory are required.

## Explicit capability boundary
This version provides real local text inference (once the model test passes), and a small allow-listed set of local Android tools. It is not yet a universal autonomous computer grid: it does not execute commands on remote Windows/Linux/macOS computers, coordinate distributed workers, or include a secure multi-user backend. Those capabilities require a separately installed signed worker agent for each desktop OS, authenticated pairing, encrypted transport, per-action permissions, revocation, audit logs, and dedicated integration tests. The app currently configures one model (Qwen2.5 0.5B Q4_0); a model catalogue can only be trusted when each model has a verified source, license, hash, compatible runtime/ABI, memory profile, and real inference tests.
