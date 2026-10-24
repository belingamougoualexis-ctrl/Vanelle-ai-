package com.vanelle.aircorezero

import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.util.Base64
import android.webkit.JavascriptInterface
import android.webkit.ValueCallback
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast

class MainActivity : Activity() {
    private lateinit var web: WebView
    private var fileChooserCallback: ValueCallback<Array<Uri>>? = null
    @Volatile private var pendingExportBytes: ByteArray? = null
    @Volatile private var pendingExportName: String = "aircore-export.json"
    @Volatile private var pendingExportMime: String = "application/json"

    companion object {
        private const val REQUEST_IMPORT = 7101
        private const val REQUEST_EXPORT = 7102
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        web = WebView(this)
        web.settings.javaScriptEnabled = true
        web.settings.domStorageEnabled = true
        web.webChromeClient = object : WebChromeClient() {
            override fun onShowFileChooser(
                webView: WebView?,
                filePathCallback: ValueCallback<Array<Uri>>?,
                fileChooserParams: FileChooserParams?
            ): Boolean {
                fileChooserCallback?.onReceiveValue(null)
                fileChooserCallback = filePathCallback
                return try {
                    val intent = Intent(Intent.ACTION_OPEN_DOCUMENT).apply {
                        addCategory(Intent.CATEGORY_OPENABLE)
                        type = "*/*"
                    }
                    startActivityForResult(intent, REQUEST_IMPORT)
                    true
                } catch (e: Exception) {
                    fileChooserCallback?.onReceiveValue(null)
                    fileChooserCallback = null
                    Toast.makeText(this@MainActivity, "Impossible d'ouvrir le sélecteur de fichiers", Toast.LENGTH_LONG).show()
                    false
                }
            }
        }
        web.webViewClient = WebViewClient()
        web.setBackgroundColor(android.graphics.Color.rgb(7, 20, 38))
        web.addJavascriptInterface(AirCoreBridge(), "AndroidAirCore")
        setContentView(web)
        web.loadUrl("file:///android_asset/index.html")
    }

    private inner class AirCoreBridge {
        @JavascriptInterface
        fun saveFile(name: String, base64Data: String, mimeType: String) {
            try {
                val bytes = Base64.decode(base64Data, Base64.DEFAULT)
                pendingExportBytes = bytes
                pendingExportName = name.replace(Regex("[^a-zA-Z0-9._-]"), "_").ifBlank { "aircore-export.json" }
                pendingExportMime = mimeType.ifBlank { "application/octet-stream" }
                runOnUiThread {
                    try {
                        val intent = Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
                            addCategory(Intent.CATEGORY_OPENABLE)
                            type = pendingExportMime
                            putExtra(Intent.EXTRA_TITLE, pendingExportName)
                        }
                        startActivityForResult(intent, REQUEST_EXPORT)
                    } catch (e: Exception) {
                        pendingExportBytes = null
                        Toast.makeText(this@MainActivity, "Export impossible : aucun sélecteur de fichiers disponible", Toast.LENGTH_LONG).show()
                    }
                }
            } catch (e: Exception) {
                runOnUiThread {
                    Toast.makeText(this@MainActivity, "Préparation de l'export échouée", Toast.LENGTH_LONG).show()
                }
            }
        }
    }

    @Deprecated("Deprecated by Android, retained for compatibility with minSdk 26")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        when (requestCode) {
            REQUEST_IMPORT -> {
                val callback = fileChooserCallback
                fileChooserCallback = null
                if (resultCode == RESULT_OK && data?.data != null) callback?.onReceiveValue(arrayOf(data.data!!))
                else callback?.onReceiveValue(null)
            }
            REQUEST_EXPORT -> {
                val bytes = pendingExportBytes
                pendingExportBytes = null
                if (resultCode == RESULT_OK && data?.data != null && bytes != null) {
                    try {
                        contentResolver.openOutputStream(data.data!!, "w")?.use { it.write(bytes) }
                            ?: throw IllegalStateException("Flux de sortie indisponible")
                        Toast.makeText(this, "Export réussi : fichier enregistré", Toast.LENGTH_LONG).show()
                    } catch (e: Exception) {
                        Toast.makeText(this, "Échec de l'export : " + (e.message ?: "erreur d'écriture"), Toast.LENGTH_LONG).show()
                    }
                } else Toast.makeText(this, "Export annulé", Toast.LENGTH_SHORT).show()
            }
        }
    }

    override fun onDestroy() {
        fileChooserCallback?.onReceiveValue(null)
        fileChooserCallback = null
        web.removeJavascriptInterface("AndroidAirCore")
        web.destroy()
        super.onDestroy()
    }
}
