package com.linguabloom.academy;

import android.app.Activity;
import android.app.AlertDialog;
import android.graphics.Color;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.CookieManager;
import android.webkit.GeolocationPermissions;
import android.webkit.PermissionRequest;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.content.Intent;
import android.content.SharedPreferences;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ProgressBar;
import android.webkit.JavascriptInterface;
import org.json.JSONObject;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.security.MessageDigest;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public final class MainActivity extends Activity {
    private static final String PREFS = "linguabloom";
    private static final String SERVER_KEY = "server_url";
    private WebView webView;
    private SharedPreferences prefs;
    private final ExecutorService modelExecutor = Executors.newSingleThreadExecutor();
    private static final String MODEL_NAME = "Gemma3-1B-IT_multi-prefill-seq_q4_ekv4096.litertlm";
    private static final String MODEL_URL = "https://huggingface.co/cuesetac/gemma-3-1b-it-litertlm/resolve/main/Gemma3-1B-IT_multi-prefill-seq_q4_ekv4096.litertlm";
    private static final long MODEL_BYTES = 584417280L;
    private static final String MODEL_SHA256 = "1325ae366d31950f137c9c357b9fa89448b176d76998180c08ceaca78bba98be";
    private ProgressBar modelProgress;
    private TextView modelStatus;
    private Button retryButton;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        ensureLocalModel();
    }

    private int dp(float value) {
        return (int) (value * getResources().getDisplayMetrics().density + 0.5f);
    }

    private void showServerSetup() {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setGravity(Gravity.CENTER_HORIZONTAL);
        panel.setPadding(dp(24), dp(38), dp(24), dp(24));
        panel.setBackgroundColor(Color.rgb(247, 246, 255));

        TextView brand = new TextView(this);
        brand.setText("LinguaBloom");
        brand.setTextColor(Color.rgb(77, 55, 160));
        brand.setTextSize(30);
        brand.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        brand.setGravity(Gravity.CENTER);
        panel.addView(brand, new LinearLayout.LayoutParams(-1, -2));

        TextView subtitle = new TextView(this);
        subtitle.setText("ACADEMY  •  APPRENDRE SANS LIMITES");
        subtitle.setTextColor(Color.rgb(100, 94, 125));
        subtitle.setTextSize(12);
        subtitle.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams subParams = new LinearLayout.LayoutParams(-1, -2);
        subParams.setMargins(0, dp(8), 0, dp(28));
        panel.addView(subtitle, subParams);

        TextView explanation = new TextView(this);
        explanation.setText("Connectez l'application au serveur LinguaBloom Academy. L'API et le moteur IA doivent être démarrés sur ce serveur. Utilisez son adresse locale ou HTTPS.");
        explanation.setTextColor(Color.rgb(43, 40, 58));
        explanation.setTextSize(16);
        explanation.setGravity(Gravity.CENTER);
        panel.addView(explanation, new LinearLayout.LayoutParams(-1, -2));

        EditText serverInput = new EditText(this);
        serverInput.setSingleLine(true);
        serverInput.setHint("https://votre-serveur.example ou 192.168.1.10:8000");
        serverInput.setText(prefs.getString(SERVER_KEY, ""));
        serverInput.setInputType( android.text.InputType.TYPE_CLASS_TEXT | android.text.InputType.TYPE_TEXT_VARIATION_URI);
        LinearLayout.LayoutParams inputParams = new LinearLayout.LayoutParams(-1, -2);
        inputParams.setMargins(0, dp(24), 0, dp(12));
        panel.addView(serverInput, inputParams);

        Button connect = new Button(this);
        connect.setText("CONNECTER");
        connect.setTextColor(Color.WHITE);
        connect.setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(89, 65, 183)));
        panel.addView(connect, new LinearLayout.LayoutParams(-1, dp(52)));

        Button offline = new Button(this);
        offline.setText("APPRENDRE HORS LIGNE");
        offline.setTextColor(Color.rgb(25, 53, 80));
        offline.setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(226, 239, 245)));
        LinearLayout.LayoutParams offlineParams = new LinearLayout.LayoutParams(-1, dp(52));
        offlineParams.setMargins(0, dp(10), 0, 0);
        panel.addView(offline, offlineParams);
        offline.setOnClickListener(v -> openOffline());

        TextView note = new TextView(this);
        note.setText("Cette version Android nécessite un serveur accessible. Elle ne prétend pas embarquer le modèle IA ni la base de données dans le téléphone.");
        note.setTextColor(Color.rgb(110, 105, 130));
        note.setTextSize(12);
        LinearLayout.LayoutParams noteParams = new LinearLayout.LayoutParams(-1, -2);
        noteParams.setMargins(0, dp(18), 0, 0);
        panel.addView(note, noteParams);

        connect.setOnClickListener(v -> {
            try {
                String url = ServerUrl.normalize(serverInput.getText().toString());
                prefs.edit().putString(SERVER_KEY, url).apply();
                openServer(url);
            } catch (IllegalArgumentException e) {
                serverInput.setError(e.getMessage());
            }
        });
        setContentView(panel);
    }


    private void openOffline() {
        webView = new WebView(this);
        webView.setBackgroundColor(Color.WHITE);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        webView.setWebViewClient(new WebViewClient());
        webView.addJavascriptInterface(new TutorBridge(), "AndroidTutor");
        setContentView(webView);
        webView.loadUrl("file:///android_asset/offline/index.html");
    }

    private File modelFile() {
        File dir = new File(getFilesDir(), "models");
        if (!dir.exists()) dir.mkdirs();
        return new File(dir, MODEL_NAME);
    }

    private void ensureLocalModel() {
        File model = modelFile();
        if (model.isFile() && model.length() == MODEL_BYTES && MODEL_SHA256.equals(sha256(model))) {
            openOffline();
            return;
        }
        showModelSetup();
        startModelDownload();
    }

    private void showModelSetup() {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setGravity(Gravity.CENTER);
        panel.setPadding(dp(28), dp(24), dp(28), dp(24));
        panel.setBackgroundColor(Color.rgb(243, 246, 250));
        TextView title = new TextView(this);
        title.setText("LinguaBloom Academy");
        title.setTextColor(Color.rgb(16, 43, 70));
        title.setTextSize(28);
        title.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        title.setGravity(Gravity.CENTER);
        panel.addView(title, new LinearLayout.LayoutParams(-1, -2));
        TextView subtitle = new TextView(this);
        subtitle.setText("Préparation du professeur IA hors ligne");
        subtitle.setTextColor(Color.rgb(8, 126, 121));
        subtitle.setTextSize(16);
        subtitle.setGravity(Gravity.CENTER);
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(-1, -2);
        sp.setMargins(0, dp(10), 0, dp(20));
        panel.addView(subtitle, sp);
        modelStatus = new TextView(this);
        modelStatus.setText("Vérification du modèle…");
        modelStatus.setTextColor(Color.rgb(23, 43, 67));
        modelStatus.setGravity(Gravity.CENTER);
        panel.addView(modelStatus, new LinearLayout.LayoutParams(-1, -2));
        modelProgress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        modelProgress.setMax(1000);
        LinearLayout.LayoutParams bp = new LinearLayout.LayoutParams(-1, dp(12));
        bp.setMargins(0, dp(18), 0, dp(12));
        panel.addView(modelProgress, bp);
        TextView detail = new TextView(this);
        detail.setText("Téléchargement unique : environ 584 Mo. En cas de coupure, les données déjà reçues sont conservées et la reprise continue au prochain essai. Le modèle répond ensuite sans envoyer tes questions sur Internet.");
        detail.setTextColor(Color.rgb(96, 116, 136));
        detail.setTextSize(13);
        detail.setGravity(Gravity.CENTER);
        panel.addView(detail, new LinearLayout.LayoutParams(-1, -2));
        retryButton = new Button(this);
        retryButton.setText("Reprendre le téléchargement");
        retryButton.setVisibility(View.GONE);
        panel.addView(retryButton, new LinearLayout.LayoutParams(-1, dp(50)));
        retryButton.setOnClickListener(v -> startModelDownload());
        setContentView(panel);
    }

    private void startModelDownload() {
        if (modelStatus == null) showModelSetup();
        retryButton.setEnabled(false);
        retryButton.setVisibility(View.GONE);
        modelExecutor.execute(() -> {
            File target = modelFile();
            File partial = new File(target.getAbsolutePath() + ".part");
            try {
                runOnUiThread(() -> modelStatus.setText("Connexion au dépôt du modèle…"));
                long existing = partial.isFile() ? partial.length() : 0L;
                HttpURLConnection connection = (HttpURLConnection) new URL(MODEL_URL).openConnection();
                connection.setConnectTimeout(20000);
                connection.setReadTimeout(30000);
                connection.setInstanceFollowRedirects(true);
                connection.setRequestProperty("User-Agent", "LinguaBloomAcademy/1.1");
                if (existing > 0) connection.setRequestProperty("Range", "bytes=" + existing + "-");
                int code = connection.getResponseCode();
                boolean append = code == HttpURLConnection.HTTP_PARTIAL && existing > 0;
                if (code != HttpURLConnection.HTTP_OK && !append) {
                    if (code == HttpURLConnection.HTTP_PARTIAL) throw new java.io.IOException("Réponse de reprise inattendue.");
                    throw new java.io.IOException("Téléchargement impossible (HTTP " + code + ").");
                }
                if (!append) existing = 0L;
                final long offset = existing;
                long total = MODEL_BYTES;
                runOnUiThread(() -> modelStatus.setText("Téléchargement du modèle IA…"));
                try (InputStream in = connection.getInputStream();
                     FileOutputStream out = new FileOutputStream(partial, append)) {
                    byte[] buffer = new byte[64 * 1024];
                    long received = offset;
                    int n;
                    while ((n = in.read(buffer)) != -1) {
                        out.write(buffer, 0, n);
                        received += n;
                        final long current = received;
                        runOnUiThread(() -> {
                            if (modelProgress != null) modelProgress.setProgress((int)Math.min(1000L, current * 1000L / total));
                            if (modelStatus != null) modelStatus.setText("Modèle IA : " + String.format(java.util.Locale.FRANCE, "%.1f", current / 1048576.0) + " / 557 Mo");
                        });
                    }
                    out.getFD().sync();
                } finally {
                    connection.disconnect();
                }
                if (partial.length() != MODEL_BYTES) throw new java.io.IOException("Téléchargement incomplet : " + partial.length() + " octets reçus. Appuie sur reprendre.");
                if (!MODEL_SHA256.equals(sha256(partial))) {
                    partial.delete();
                    throw new java.io.IOException("Vérification de sécurité échouée. Le fichier incomplet a été supprimé ; relance le téléchargement.");
                }
                if (target.exists()) target.delete();
                if (!partial.renameTo(target)) throw new java.io.IOException("Impossible de finaliser le modèle téléchargé.");
                runOnUiThread(() -> {
                    modelStatus.setText("Modèle vérifié. Ouverture de l’académie…");
                    modelProgress.setProgress(1000);
                    openOffline();
                });
            } catch (Exception e) {
                runOnUiThread(() -> {
                    modelStatus.setText("Téléchargement interrompu. " + (e.getMessage() == null ? "Vérifie la connexion et réessaie." : e.getMessage()) + "\nLes données partielles sont conservées.");
                    retryButton.setText("Reprendre le téléchargement");
                    retryButton.setEnabled(true);
                    retryButton.setVisibility(View.VISIBLE);
                });
            }
        });
    }

    private String sha256(File file) {
        try (InputStream in = new FileInputStream(file)) {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] buffer = new byte[64 * 1024];
            int n;
            while ((n = in.read(buffer)) != -1) digest.update(buffer, 0, n);
            StringBuilder out = new StringBuilder();
            for (byte b : digest.digest()) out.append(String.format(java.util.Locale.ROOT, "%02x", b));
            return out.toString();
        } catch (Exception e) { return ""; }
    }

    private final class TutorBridge {
        @JavascriptInterface public void ask(String prompt) {
            final String question = prompt == null ? "" : prompt.trim();
            modelExecutor.execute(() -> {
                try {
                    LocalTutor tutor = new LocalTutor(MainActivity.this);
                    tutor.initialize();
                    final StringBuilder answer = new StringBuilder();
                    tutor.ask(question, chunk -> answer.append(chunk));
                    runOnUiThread(() -> {
                        if (webView != null) webView.evaluateJavascript("window.onLocalTutorResponse && window.onLocalTutorResponse(" + JSONObject.quote(answer.toString()) + ")", null);
                        tutor.close();
                    });
                } catch (Exception e) {
                    runOnUiThread(() -> {
                        if (webView != null) webView.evaluateJavascript("window.onLocalTutorResponse && window.onLocalTutorResponse(" + JSONObject.quote("Le professeur IA n’a pas pu démarrer sur cet appareil : " + (e.getMessage() == null ? "mémoire ou modèle incompatible." : e.getMessage())) + ")", null);
                    });
                }
            });
        }
    }

    @Override protected void onDestroy() {
        modelExecutor.shutdownNow();
        super.onDestroy();
    }

    private void openServer(String url) {
        webView = new WebView(this);
        webView.setBackgroundColor(Color.WHITE);
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setMediaPlaybackRequiresUserGesture(true);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, false);

        webView.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme() == null ? "" : uri.getScheme();
                if (scheme.equals("http") || scheme.equals("https")) {
                    String current = prefs.getString(SERVER_KEY, "");
                    if (uri.toString().startsWith(current) || uri.getHost().equals(Uri.parse(current).getHost())) return false;
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                    return true;
                }
                return true;
            }

            @Override public void onReceivedError(WebView view, WebResourceRequest request, android.webkit.WebResourceError error) {
                if (request.isForMainFrame()) Toast.makeText(MainActivity.this,
                        "Serveur inaccessible. Vérifiez l'adresse et la connexion.", Toast.LENGTH_LONG).show();
            }
        });
        webView.setWebChromeClient(new WebChromeClient() {
            @Override public void onPermissionRequest(PermissionRequest request) {
                runOnUiThread(() -> {
                    boolean audio = false;
                    for (String resource : request.getResources()) {
                        if (PermissionRequest.RESOURCE_AUDIO_CAPTURE.equals(resource)) audio = true;
                    }
                    if (audio) request.grant(new String[]{PermissionRequest.RESOURCE_AUDIO_CAPTURE});
                    else request.deny();
                });
            }
            @Override public void onGeolocationPermissionsShowPrompt(String origin, GeolocationPermissions.Callback callback) {
                callback.invoke(origin, false, false);
            }
        });
        setContentView(webView);
        webView.loadUrl(url);
    }

    @Override public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else new AlertDialog.Builder(this)
                .setMessage("Quitter LinguaBloom Academy ?")
                .setNegativeButton("Annuler", (d, w) -> d.dismiss())
                .setNeutralButton("Changer de serveur", (d, w) -> showServerSetup())
                .setPositiveButton("Quitter", (d, w) -> finish())
                .show();
    }
}
