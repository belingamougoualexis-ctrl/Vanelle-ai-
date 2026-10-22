package ai.vanelle.omnigrid;

import android.app.DownloadManager;
import android.content.Context;
import android.database.Cursor;
import android.net.Uri;
import java.io.File;
import java.io.FileInputStream;
import java.security.MessageDigest;
import java.util.Locale;

/** One-time OS-managed download and integrity verification for the local GGUF model. */
public final class LocalModelManager {
    public static final String MODEL_NAME = LocalInference.MODEL_FILE;
    public static final String MODEL_URL = "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_0.gguf";
    public static final String EXPECTED_SHA256 = "7671c0c304e6ce5a7fc577bcb12aba01e2c155cc2efd29b2213c95b18edaf6ed";
    private static final String PREFS = "local_model_download";
    private static final String DOWNLOAD_ID = "download_id";
    private static final String VERIFIED = "verified_sha256";
    private LocalModelManager() {}
    public static File modelFile(Context context) {
        File dir = context.getExternalFilesDir("models");
        if (dir == null) dir = new File(context.getFilesDir(), "models");
        if (!dir.exists()) dir.mkdirs();
        return new File(dir, MODEL_NAME);
    }
    public static boolean isPresent(Context context) {
        File f = modelFile(context);
        return f.isFile() && f.length() > 300_000_000L;
    }
    public static boolean isVerified(Context context) { return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getBoolean(VERIFIED, false) && isPresent(context); }
    public static void clearVerified(Context context) { context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putBoolean(VERIFIED, false).apply(); }
    public static long startDownload(Context context) {
        clearVerified(context);
        File destination = modelFile(context);
        if (destination.exists() && !destination.delete()) throw new IllegalStateException("Impossible de remplacer le modèle incomplet.");
        DownloadManager dm = (DownloadManager) context.getSystemService(Context.DOWNLOAD_SERVICE);
        DownloadManager.Request request = new DownloadManager.Request(Uri.parse(MODEL_URL));
        request.setTitle("VANELLE OMNIGRID AI — modèle local");
        request.setDescription("Téléchargement initial d'environ 430 Mo. L'inférence sera ensuite hors ligne.");
        request.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
        request.setAllowedOverMetered(true);
        request.setAllowedOverRoaming(false);
        request.setDestinationInExternalFilesDir(context, "models", MODEL_NAME);
        long id = dm.enqueue(request);
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putLong(DOWNLOAD_ID, id).apply();
        return id;
    }
    public static long savedDownloadId(Context context) {
        return context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).getLong(DOWNLOAD_ID, -1L);
    }
    public static String downloadStatus(Context context) {
        long id = savedDownloadId(context);
        if (isVerified(context)) return "Modèle vérifié — prêt hors ligne";
        if (id < 0) return isPresent(context) ? "Modèle présent — vérification requise" : "Modèle non téléchargé";
        DownloadManager dm = (DownloadManager) context.getSystemService(Context.DOWNLOAD_SERVICE);
        try (Cursor c = dm.query(new DownloadManager.Query().setFilterById(id))) {
            if (c == null || !c.moveToFirst()) return "Téléchargement introuvable";
            int status = c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS));
            long done = c.getLong(c.getColumnIndexOrThrow(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR));
            long total = c.getLong(c.getColumnIndexOrThrow(DownloadManager.COLUMN_TOTAL_SIZE_BYTES));
            if (status == DownloadManager.STATUS_SUCCESSFUL) return "Téléchargement terminé — vérification d'intégrité requise";
            if (status == DownloadManager.STATUS_FAILED) return "Échec du téléchargement (code " + c.getInt(c.getColumnIndexOrThrow(DownloadManager.COLUMN_REASON)) + "). Relance-le.";
            if (total > 0) return "Téléchargement : " + (done * 100 / total) + "% (" + (done / 1_000_000) + "/" + (total / 1_000_000) + " Mo)";
            return "Téléchargement en cours…";
        } catch (Exception e) { return "État du téléchargement indisponible"; }
    }
    public static boolean verifyIntegrity(Context context) throws Exception {
        File f = modelFile(context);
        if (!f.isFile() || f.length() < 300_000_000L) return false;
        try (FileInputStream in = new FileInputStream(f)) {
            byte[] magic = new byte[4];
            if (in.read(magic) != 4 || magic[0] != 'G' || magic[1] != 'G' || magic[2] != 'U' || magic[3] != 'F') return false;
        }
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (FileInputStream in = new FileInputStream(f)) {
            byte[] buffer = new byte[1024 * 1024]; int n;
            while ((n = in.read(buffer)) > 0) digest.update(buffer, 0, n);
        }
        StringBuilder hex = new StringBuilder();
        for (byte b : digest.digest()) hex.append(String.format(Locale.ROOT, "%02x", b & 0xff));
        boolean valid = EXPECTED_SHA256.equals(hex.toString());
        context.getSharedPreferences(PREFS, Context.MODE_PRIVATE).edit().putBoolean(VERIFIED, valid).apply();
        return valid;
    }
}
