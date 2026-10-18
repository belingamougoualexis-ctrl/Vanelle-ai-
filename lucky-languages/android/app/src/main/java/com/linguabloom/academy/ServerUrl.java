package com.linguabloom.academy;

import java.net.URI;
import java.net.URISyntaxException;

public final class ServerUrl {
    private ServerUrl() {}

    public static String normalize(String input) {
        if (input == null) throw new IllegalArgumentException("Saisissez l'adresse du serveur.");
        String value = input.trim();
        if (value.isEmpty()) throw new IllegalArgumentException("Saisissez l'adresse du serveur.");
        if (!value.matches("(?i)^https?://.*")) value = "http://" + value;
        try {
            URI uri = new URI(value);
            String scheme = uri.getScheme();
            if (scheme == null || !(scheme.equalsIgnoreCase("http") || scheme.equalsIgnoreCase("https")))
                throw new IllegalArgumentException("Utilisez une adresse HTTP ou HTTPS.");
            if (uri.getHost() == null || uri.getHost().isEmpty())
                throw new IllegalArgumentException("L'adresse du serveur est invalide.");
            if (uri.getUserInfo() != null)
                throw new IllegalArgumentException("Ne mettez pas d'identifiants dans l'adresse.");
            String normalized = new URI(scheme.toLowerCase(), null, uri.getHost(), uri.getPort(),
                    uri.getPath() == null || uri.getPath().equals("/") ? "" : uri.getPath(),
                    null, null).toString();
            return normalized.endsWith("/") ? normalized.substring(0, normalized.length() - 1) : normalized;
        } catch (URISyntaxException ex) {
            throw new IllegalArgumentException("L'adresse du serveur est invalide.");
        }
    }
}
