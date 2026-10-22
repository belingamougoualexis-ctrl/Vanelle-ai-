# VANELLE OMNIGRID AI — local-first Android

## Local AI runtime
- Native on-device text generation through llama.cpp Android AAR (dev.ffmpegkit-maintained:llama-android:0.1.1).
- Default model: Qwen2.5-0.5B-Instruct GGUF Q4_0 (about 429 MB), Apache-2.0 model license.
- Initial download uses Android DownloadManager. Model is checked for GGUF magic and the published SHA-256 before it is trusted.
- After model download, prompt inference is local: no provider URL, API key, or prompt upload is used by the app.
- Model load uses a 2,048-token context and 2–4 CPU threads; inference releases native model memory after each request.
- A built-in self-test performs real inference and shows the model's actual response.

## Build / tests
- Android SDK 35, Java 17, Kotlin 2.0.21, Gradle 8.10.2.
- GitHub Actions builds debug and release APKs, then runs the Android emulator UI smoke test.
- CI build proves compilation; it does not prove a model was downloaded or real local inference succeeded on a physical phone. The in-app self-test is the real inference test to run after download.
- The bundled llama-android AAR documents arm64-v8a support. A device/emulator must support that ABI; 429 MB download plus model/cache memory are required.

## Not yet implemented
This is local on-device language-model inference and planning, not a finished universal autonomous computer grid. It does not execute actions on remote Windows/Linux/macOS computers, include a secure multi-user backend, or ship every model. Models are too large and diverse to bundle all AI models; this app currently downloads one small model locally.
