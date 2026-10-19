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

public final class MainActivity extends Activity {
    private static final String PREFS = "linguabloom";
    private static final String SERVER_KEY = "server_url";
    private WebView webView;
    private SharedPreferences prefs;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        // Start in the local learning space. The offline course module does not
        // require a configured server or an Internet connection.
        openOffline();
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
        setContentView(webView);
        webView.loadUrl("file:///android_asset/offline/index.html");
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
