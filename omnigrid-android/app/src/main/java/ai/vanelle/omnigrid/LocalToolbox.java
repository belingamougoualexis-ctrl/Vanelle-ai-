package ai.vanelle.omnigrid;

import android.content.Context;
import android.os.Build;
import java.io.File;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * Strict allow-list of useful actions executed entirely on this Android device.
 * Commands are explicit so natural-language model output cannot silently trigger side effects.
 */
public final class LocalToolbox {
    private LocalToolbox() {}

    public static String help() {
        return "Outils réellement exécutables sur cet appareil :\n"
            + "• calc: (12 + 3) * 4 — calcul arithmétique local\n"
            + "• note: mon texte — enregistrer une note locale\n"
            + "• notes:list — afficher les notes locales\n"
            + "• time:now — date et heure de l'appareil\n"
            + "• device:info — informations Android non sensibles\n\n"
            + "Les autres demandes sont analysées par l'IA, sans prétendre exécuter des actions sur un ordinateur distant.";
    }

    public static boolean handles(String raw) {
        String s = raw.trim().toLowerCase(Locale.ROOT);
        return s.startsWith("calc:") || s.startsWith("note:") || s.equals("notes:list")
            || s.equals("time:now") || s.equals("device:info") || s.equals("tools:list");
    }

    public static String run(Context context, String raw) throws Exception {
        String s = raw.trim();
        String lower = s.toLowerCase(Locale.ROOT);
        if (lower.startsWith("calc:")) {
            String expression = s.substring(s.indexOf(':') + 1).trim();
            if (expression.isEmpty()) throw new IllegalArgumentException("Expression manquante après calc:.");
            double result = new ArithmeticParser(expression).parse();
            return "Calcul effectué localement : " + expression + " = " + result;
        }
        if (lower.startsWith("note:")) {
            String note = s.substring(s.indexOf(':') + 1).trim();
            if (note.isEmpty()) throw new IllegalArgumentException("Texte de note vide.");
            File dir = new File(context.getFilesDir(), "notes");
            if (!dir.exists() && !dir.mkdirs()) throw new IllegalStateException("Impossible de créer le dossier des notes.");
            File file = new File(dir, "note-" + System.currentTimeMillis() + ".txt");
            try (FileOutputStream out = new FileOutputStream(file)) {
                out.write(note.getBytes(StandardCharsets.UTF_8));
            }
            return "Note enregistrée localement : " + file.getName() + "\n" + note;
        }
        if (lower.equals("notes:list")) {
            File dir = new File(context.getFilesDir(), "notes");
            File[] files = dir.listFiles((d, name) -> name.endsWith(".txt"));
            if (files == null || files.length == 0) return "Aucune note locale enregistrée.";
            StringBuilder out = new StringBuilder("Notes locales (" + files.length + ") :\n");
            java.util.Arrays.sort(files, (a,b) -> Long.compare(b.lastModified(), a.lastModified()));
            int limit = Math.min(files.length, 30);
            for (int i=0; i<limit; i++) {
                String body = new String(java.nio.file.Files.readAllBytes(files[i].toPath()), StandardCharsets.UTF_8);
                out.append(i+1).append(". ").append(files[i].getName()).append(" — ").append(body).append('\n');
            }
            return out.toString();
        }
        if (lower.equals("time:now")) {
            return "Heure locale de l'appareil : " + new SimpleDateFormat("yyyy-MM-dd HH:mm:ss z", Locale.getDefault()).format(new Date());
        }
        if (lower.equals("device:info")) {
            return "Informations locales : Android " + Build.VERSION.RELEASE + " (API " + Build.VERSION.SDK_INT + "), fabricant "
                + Build.MANUFACTURER + ", modèle " + Build.MODEL + ", ABI " + Build.SUPPORTED_ABIS[0] + ".";
        }
        if (lower.equals("tools:list")) return help();
        throw new IllegalArgumentException("Commande locale non reconnue.");
    }

    private static final class ArithmeticParser {
        private final String input;
        private int pos = 0;
        ArithmeticParser(String input) {
            this.input = input;
            if (input.length() > 160) throw new IllegalArgumentException("Expression trop longue (160 caractères maximum).");
        }
        double parse() {
            double v = expression();
            spaces();
            if (pos != input.length()) throw new IllegalArgumentException("Caractère inattendu à la position " + pos + ".");
            if (!Double.isFinite(v)) throw new IllegalArgumentException("Résultat non fini.");
            return v;
        }
        private double expression() {
            double v = term();
            while (true) {
                spaces();
                if (eat('+')) v += term();
                else if (eat('-')) v -= term();
                else return v;
            }
        }
        private double term() {
            double v = factor();
            while (true) {
                spaces();
                if (eat('*')) v *= factor();
                else if (eat('/')) {
                    double d = factor();
                    if (d == 0d) throw new IllegalArgumentException("Division par zéro.");
                    v /= d;
                } else return v;
            }
        }
        private double factor() {
            spaces();
            if (eat('+')) return factor();
            if (eat('-')) return -factor();
            if (eat('(')) {
                double v = expression();
                spaces();
                if (!eat(')')) throw new IllegalArgumentException("Parenthèse fermante manquante.");
                return v;
            }
            int start = pos;
            boolean dot = false;
            while (pos < input.length()) {
                char c = input.charAt(pos);
                if (c >= '0' && c <= '9') pos++;
                else if (c == '.' && !dot) { dot = true; pos++; }
                else break;
            }
            if (start == pos) throw new IllegalArgumentException("Nombre attendu à la position " + pos + ".");
            try { return Double.parseDouble(input.substring(start, pos)); }
            catch (NumberFormatException e) { throw new IllegalArgumentException("Nombre invalide."); }
        }
        private boolean eat(char c) {
            if (pos < input.length() && input.charAt(pos) == c) { pos++; return true; }
            return false;
        }
        private void spaces() { while (pos < input.length() && Character.isWhitespace(input.charAt(pos))) pos++; }
    }
}
