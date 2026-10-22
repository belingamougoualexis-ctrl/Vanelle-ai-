package ai.vanelle.omnigrid

import android.content.Context
import dev.ffmpegkit.llama.Llama
import dev.ffmpegkit.llama.LlamaConfig
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runBlocking
import java.io.File

/** All generation happens on-device through llama.cpp. No prompt is sent over the network. */
object LocalInference {
    const val MODEL_FILE = "qwen2.5-0.5b-instruct-q4_0.gguf"
    @JvmStatic
    fun generate(context: Context, prompt: String): String = runBlocking(Dispatchers.IO) {
        val directory = context.getExternalFilesDir("models") ?: File(context.filesDir, "models")
        val file = File(directory, MODEL_FILE)
        require(file.isFile && file.length() > 300_000_000L) {
            "Modèle local absent ou incomplet. Télécharge-le depuis les paramètres IA."
        }
        val threads = Runtime.getRuntime().availableProcessors().coerceIn(2, 4)
        val loaded = Llama.loadModel(modelPath = file.absolutePath, config = LlamaConfig(contextSize = 2048, threads = threads))
        try {
            val result = Llama.complete(
                loaded,
                prompt = prompt,
                systemPrompt = "Tu es VANELLE OMNIGRID AI, un assistant local. Tu fonctionnes hors ligne. Analyse la demande, propose un plan clair, signale les risques et ne prétends jamais avoir exécuté une action externe. Demande une confirmation explicite avant toute action irréversible.",
                maxTokens = 256
            )
            result.text.trim().ifEmpty { "Le modèle local n'a produit aucun texte. Réessaie avec une demande plus courte." }
        } finally { Llama.releaseModel(loaded) }
    }
}
