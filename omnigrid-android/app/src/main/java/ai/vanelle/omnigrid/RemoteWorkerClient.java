package ai.vanelle.omnigrid;

import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URL;
import javax.net.ssl.HttpsURLConnection;

/** Authenticated HTTPS client for the explicitly allow-listed desktop worker API. */
public final class RemoteWorkerClient {
    private RemoteWorkerClient() {}

    public static String execute(String endpoint, String token, JSONObject payload, boolean approved) throws Exception {
        if (endpoint == null || !endpoint.startsWith("https://")) {
            throw new IllegalArgumentException("Le worker distant exige une URL HTTPS avec certificat reconnu.");
        }
        if (token == null || token.trim().length() < 32) {
            throw new IllegalArgumentException("Jeton worker invalide : 32 caractères minimum.");
        }
        URL url = new URL(endpoint);
        if (!"https".equalsIgnoreCase(url.getProtocol()) || url.getUserInfo() != null) {
            throw new IllegalArgumentException("URL HTTPS invalide.");
        }
        HttpsURLConnection conn = (HttpsURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setConnectTimeout(10000);
        conn.setReadTimeout(15000);
        conn.setInstanceFollowRedirects(false);
        conn.setDoOutput(true);
        conn.setRequestProperty("Authorization", "Bearer " + token.trim());
        conn.setRequestProperty("Content-Type", "application/json; charset=utf-8");
        conn.setRequestProperty("Accept", "application/json");
        if (approved) conn.setRequestProperty("X-Vanelle-Approval", "yes");
        byte[] body = payload.toString().getBytes("UTF-8");
        conn.setFixedLengthStreamingMode(body.length);
        try {
            try (OutputStream out = conn.getOutputStream()) { out.write(body); }
            int code = conn.getResponseCode();
            InputStream in = code >= 200 && code < 400 ? conn.getInputStream() : conn.getErrorStream();
            if (in == null) throw new IllegalStateException("Le worker n'a renvoyé aucune réponse (HTTP " + code + ").");
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            try (InputStream input = in) {
                byte[] buffer = new byte[4096];
                int n;
                while ((n = input.read(buffer)) != -1) {
                    if (bytes.size() + n > 65536) throw new IllegalStateException("Réponse du worker trop volumineuse.");
                    bytes.write(buffer, 0, n);
                }
            }
            String response = new String(bytes.toByteArray(), "UTF-8");
            if (code < 200 || code >= 300) throw new IllegalStateException("Worker HTTP " + code + " : " + response);
            return response;
        } finally {
            conn.disconnect();
        }
    }
}
