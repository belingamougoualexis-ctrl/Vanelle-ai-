package com.vanelleacademy.academy;

import android.net.Uri;

/** Normalizes a server URL and rejects malformed or unsupported schemes. */
public final class ServerUrl {
    private ServerUrl() {}

    public static String normalize(String raw) {
        if (raw == null) throw new IllegalArgumentException("Saisis l'adresse du serveur.");
        String value = raw.trim();
        if (value.isEmpty()) throw new IllegalArgumentException("Saisis l'adresse du serveur.");
        if (value.indexOf(' ') >= 0 || value.indexOf('\n') >= 0 || value.indexOf('\r') >= 0) {
            throw new IllegalArgumentException("L'adresse ne doit pas contenir d'espaces.");
        }
        if (!value.matches("(?i)^https?://.*")) value = "http://" + value;
        Uri uri = Uri.parse(value);
        String scheme = uri.getScheme();
        if (scheme == null || (!scheme.equalsIgnoreCase("http") && !scheme.equalsIgnoreCase("https"))) {
            throw new IllegalArgumentException("Utilise une adresse HTTP ou HTTPS.");
        }
        if (uri.getHost() == null || uri.getHost().trim().isEmpty() || uri.getUserInfo() != null) {
            throw new IllegalArgumentException("Adresse de serveur invalide.");
        }
        if (uri.getQuery() != null || uri.getFragment() != null) {
            throw new IllegalArgumentException("Retire les paramètres et le fragment de l'adresse du serveur.");
        }
        String normalized = value;
        while (normalized.endsWith("/")) normalized = normalized.substring(0, normalized.length() - 1);
        return normalized;
    }
}
