package com.linguabloom.academy

import android.content.Context
import com.google.ai.edge.litertlm.Backend
import com.google.ai.edge.litertlm.Contents
import com.google.ai.edge.litertlm.ConversationConfig
import com.google.ai.edge.litertlm.Engine
import com.google.ai.edge.litertlm.EngineConfig
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.runBlocking

/**
 * Local-only educational tutor. It never sends prompts to a server.
 * The model file is downloaded and checksum-verified by MainActivity.
 */
class LocalTutor(context: Context) : AutoCloseable {
    private val modelPath = context.filesDir.resolve("models/Gemma3-1B-IT_multi-prefill-seq_q4_ekv4096.litertlm").absolutePath
    private val engine = Engine(EngineConfig(modelPath = modelPath, backend = Backend.CPU()))
    private var conversation: com.google.ai.edge.litertlm.Conversation? = null

    @Synchronized
    fun initialize() {
        if (conversation != null) return
        engine.initialize()
        conversation = engine.createConversation(
            ConversationConfig(
                systemInstruction = Contents.of(
                    """Tu es Vanelle, un professeur de langues patient et rigoureux. Tu enseignes principalement en français et aides l'élève à apprendre l'anglais et les langues disponibles dans l'application. Explique simplement, corrige avec bienveillance, donne des exemples courts et demande parfois à l'élève d'essayer lui-même. Pour une traduction, donne le sens naturel, la prononciation approximative si utile, puis un exemple. N'invente pas une certitude quand tu ne sais pas. Reste adapté à un public scolaire."""
                )
            )
        )
    }

    fun ask(prompt: String, onChunk: (String) -> Unit) {
        require(prompt.isNotBlank()) { "Écris une question avant d'envoyer." }
        require(prompt.length <= 2000) { "La question est trop longue (maximum 2 000 caractères)." }
        initialize()
        val active = conversation ?: error("Le professeur IA n'est pas initialisé.")
        runBlocking {
            active.sendMessageAsync(prompt).collect { chunk -> onChunk(chunk) }
        }
    }

    override fun close() {
        synchronized(this) {
            try { conversation?.close() } catch (_: Exception) {}
            conversation = null
            try { engine.close() } catch (_: Exception) {}
        }
    }
}
