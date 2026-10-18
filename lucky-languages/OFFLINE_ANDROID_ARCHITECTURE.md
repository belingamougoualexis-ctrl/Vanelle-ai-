# LinguaBloom Academy — Android offline architecture

## Product requirement

The Android app must launch and teach without a server, account, network request, or cloud AI. Course content, quiz scoring, saved progress, and settings live on-device. AI responses must come from a model running locally; no remote fallback is permitted in offline mode.

## Existing state (do not confuse with the target)

The current Android APK is a WebView client that asks for a server URL. The FastAPI backend and its Ollama/Qwen 2.5 1.5B service are separate processes. That APK is **not** the offline app described here.

## Target architecture

- **Android host:** native Java/Kotlin app, minimum Android 8/API 26 as the intended baseline; keep the UI independent of remote web assets.
- **Course pack:** versioned JSON lesson catalogue packaged under Android assets. Each lesson contains language, level, objective, explanation, examples, exercises, answer key and correction. A local SQLite database stores completion, quiz scores, bookmarks and tutor conversations.
- **Local AI runtime:** llama.cpp Android NDK/JNI, pinned to a tested commit. The Java layer must call the JNI runtime on a background executor, cap context/output, expose cancellation and release native resources on lifecycle changes.
- **Model:** Qwen2.5-0.5B-Instruct GGUF Q4_K_M, approximately 380–400 MiB, is the conservative first candidate for mobile. It is a compact tutor, not equivalent to a large cloud model; quality and speed must be measured on the actual target device. Apache-2.0 model distribution terms and upstream attribution must ship with the app.
- **Offline speech:** Android TextToSpeech using installed offline voices. Voice recognition is optional and only advertised when an installed on-device recognizer is available; never promise offline speech recognition universally.
- **No network dependency:** Android app must not make HTTP calls in offline mode. Online update/model-download code, if ever added, must be explicitly opt-in and separate from the offline install.

## Distribution size and device requirements

Embedding the GGUF model makes the APK hundreds of MiB larger than the existing ~15 KB WebView wrapper. The exact final size depends on native ABIs and packaging. Reserve at least 1.5–2 GB free storage for installation/build and model operation. A 0.5B Q4 model may still be slow or unavailable on devices with low free RAM; benchmark before declaring device compatibility.

## Acceptance gates

1. Install APK on a clean Android device and launch with airplane mode enabled.
2. Open a lesson, complete a quiz, force-stop/relaunch, and verify progress remains.
3. Ask the local tutor a question; verify a real model-generated answer and confirm no network requests.
4. Run 20 consecutive tutor prompts without crash or unbounded memory growth.
5. Verify a French and English prompt; test other advertised languages individually before listing them as supported.
6. Verify model license/attribution and checksum; reject incomplete/corrupt model files.
7. Run unit tests and assemble APK in GitHub Actions. CI success is not a substitute for device testing.

## Release rule

Do not call the product fully offline until gates 1–6 pass. Do not silently replace local inference with canned answers when the model fails. Show an actionable error instead.
