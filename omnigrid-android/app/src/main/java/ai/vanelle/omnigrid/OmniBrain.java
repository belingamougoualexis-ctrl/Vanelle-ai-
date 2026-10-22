package ai.vanelle.omnigrid;

import org.json.JSONArray;
import org.json.JSONObject;
import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

/** Real HTTPS adapter for OpenAI-compatible inference providers. */
public final class OmniBrain {
    private OmniBrain() {}
    public static String generate(String baseUrl, String model, String apiKey, String prompt) throws Exception {
        if (baseUrl == null || !baseUrl.trim().startsWith("https://"))
            throw new IllegalArgumentException("Le fournisseur doit utiliser HTTPS.");
        if (model == null || model.trim().isEmpty()) throw new IllegalArgumentException("Identifiant de modèle requis.");
        if (apiKey == null || apiKey.trim().isEmpty()) throw new IllegalArgumentException("Clé API manquante : ouvre Paramètres IA.");
        String root = baseUrl.trim().replaceAll("/+$", "");
        if (root.endsWith("/chat/completions")) root = root.substring(0, root.length() - "/chat/completions".length());
        HttpURLConnection c = (HttpURLConnection) new URL(root + "/chat/completions").openConnection();
        c.setRequestMethod("POST"); c.setConnectTimeout(15000); c.setReadTimeout(90000); c.setDoOutput(true);
        c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
        c.setRequestProperty("Authorization", "Bearer " + apiKey.trim());
        JSONObject body = new JSONObject();
        body.put("model", model.trim());
        body.put("messages", new JSONArray()
            .put(new JSONObject().put("role", "system").put("content", "Tu es VANELLE OMNIGRID AI. Sois exact. Décris les étapes, risques et limites. N'affirme jamais avoir exécuté une action externe sans preuve. Demande confirmation avant toute action irréversible."))
            .put(new JSONObject().put("role", "user").put("content", prompt)));
        body.put("temperature", 0.3);
        try (OutputStream out = c.getOutputStream()) { out.write(body.toString().getBytes(StandardCharsets.UTF_8)); }
        int code = c.getResponseCode();
        InputStream stream = code >= 200 && code < 300 ? c.getInputStream() : c.getErrorStream();
        StringBuilder raw = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream, StandardCharsets.UTF_8))) {
            String line; while ((line = reader.readLine()) != null) raw.append(line);
        } finally { c.disconnect(); }
        JSONObject json = new JSONObject(raw.toString());
        if (code < 200 || code >= 300) {
            JSONObject err = json.optJSONObject("error");
            throw new Exception("Erreur fournisseur HTTP " + code + " : " + (err == null ? raw : err.optString("message", raw.toString())));
        }
        JSONArray choices = json.optJSONArray("choices");
        if (choices == null || choices.length() == 0) throw new Exception("Aucune réponse du modèle.");
        JSONObject message = choices.getJSONObject(0).optJSONObject("message");
        String answer = message == null ? "" : message.optString("content", "");
        if (answer.trim().isEmpty()) throw new Exception("Le modèle a renvoyé une réponse vide.");
        return answer;
    }
}
