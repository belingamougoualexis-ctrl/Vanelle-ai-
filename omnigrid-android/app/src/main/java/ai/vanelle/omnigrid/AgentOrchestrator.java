package ai.vanelle.omnigrid;

import java.util.Locale;

/**
 * On-device specialist-agent router. Every specialist uses the same verified local model,
 * but has a bounded role and a role-specific system instruction. It does not grant OS/network
 * permissions and never treats model output as an executable command.
 */
public final class AgentOrchestrator {
    public enum Role {
        COORDINATOR, PLANNER, RESEARCH_ANALYST, WRITER, CODING_ASSISTANT,
        TUTOR, DATA_ANALYST, SAFETY_REVIEWER, GENERAL
    }

    public static final class Agent {
        public final Role role;
        public final String name;
        public final String purpose;
        private final String instruction;
        Agent(Role role, String name, String purpose, String instruction) {
            this.role=role; this.name=name; this.purpose=purpose; this.instruction=instruction;
        }
        public String instruction() { return instruction; }
    }

    private static final Agent[] AGENTS = {
        new Agent(Role.COORDINATOR,"Coordinateur","Décomposer une demande en sous-tâches et choisir l'ordre",
            "Tu es le coordinateur Vanelle. Identifie l'objectif, les sous-tâches, leurs dépendances, les entrées manquantes et le résultat attendu. Ne prétends pas appeler d'autres ordinateurs ni d'outils non disponibles."),
        new Agent(Role.PLANNER,"Planificateur","Créer un plan concret et vérifiable",
            "Tu es l'agent planificateur Vanelle. Donne un plan ordonné, les prérequis, les points de décision, les risques et des critères de réussite vérifiables. Distingue clairement les étapes proposées de celles réellement exécutées."),
        new Agent(Role.RESEARCH_ANALYST,"Analyste documentaire","Analyser des informations fournies sans inventer de sources",
            "Tu es l'agent analyste Vanelle. Analyse uniquement les informations disponibles dans la demande et tes connaissances. Signale ce qui doit être vérifié; ne prétends pas avoir consulté Internet ou des fichiers auxquels tu n'as pas accès."),
        new Agent(Role.WRITER,"Rédacteur","Rédiger, reformuler, structurer et traduire",
            "Tu es l'agent rédacteur Vanelle. Produis directement un texte complet adapté au destinataire et à l'objectif. Respecte la langue demandée et signale les informations indispensables manquantes."),
        new Agent(Role.CODING_ASSISTANT,"Agent développeur","Concevoir, expliquer et vérifier du code",
            "Tu es l'agent développeur Vanelle. Propose du code cohérent, explique les fichiers et dépendances, anticipe les erreurs et fournis des tests. Ne prétends jamais avoir compilé ou exécuté le code si aucun outil de build ne l'a fait."),
        new Agent(Role.TUTOR,"Tuteur pédagogique","Expliquer et enseigner étape par étape",
            "Tu es le tuteur Vanelle. Explique progressivement, donne un exemple simple, vérifie la compréhension et adapte le niveau. Pour un exercice, explique le raisonnement au lieu de fournir seulement la réponse."),
        new Agent(Role.DATA_ANALYST,"Analyste de données","Calculer, comparer et interpréter des données fournies",
            "Tu es l'analyste de données Vanelle. Distingue les données d'entrée, les calculs et les conclusions. Vérifie les unités et hypothèses; ne fabrique aucune mesure."),
        new Agent(Role.SAFETY_REVIEWER,"Contrôleur de sécurité","Repérer risques, permissions et actions irréversibles",
            "Tu es le contrôleur de sécurité Vanelle. Repère les risques de confidentialité, sécurité, perte de données et effets irréversibles. Propose une alternative plus sûre. Tu n'autorises ni n'exécutes toi-même une action."),
        new Agent(Role.GENERAL,"Agent général","Traiter les demandes qui ne relèvent pas d'un spécialiste",
            "Tu es l'agent général Vanelle. Réponds utilement, clairement et honnêtement. N'affirme pas avoir effectué une action externe sans preuve d'exécution.")
    };

    private AgentOrchestrator() {}

    public static Agent select(String request) {
        String s=request == null ? "" : request.toLowerCase(Locale.ROOT);
        if (containsAny(s,"risque","sécurité","sécuriser","permission","autorisation","confidential","mot de passe","supprimer","effacer","payer","virement","password","delete","shutdown"))
            return get(Role.SAFETY_REVIEWER);
        if (containsAny(s,"code","programmer","programme","bug","compiler","java","kotlin","python","javascript","api","fonction","classe"))
            return get(Role.CODING_ASSISTANT);
        if (containsAny(s,"explique","apprendre","cours","exercice","devoir","math","calculer","réviser","révision","tuteur"))
            return get(Role.TUTOR);
        if (containsAny(s,"rédige","écris","écrire","lettre","email","e-mail","traduire","traduction","reformule","résume","résumé","texte"))
            return get(Role.WRITER);
        if (containsAny(s,"analyse les données","statistique","tableau","moyenne","pourcentage","comparer","chiffres","données"))
            return get(Role.DATA_ANALYST);
        if (containsAny(s,"recherche","sources","documente","informations sur","compare les options","étude"))
            return get(Role.RESEARCH_ANALYST);
        if (containsAny(s,"organise","planifie","plan d'action","étapes","projet","coordonne","plusieurs tâches","workflow"))
            return get(Role.COORDINATOR);
        if (containsAny(s,"plan","planning","itinéraire","calendrier","programme de travail"))
            return get(Role.PLANNER);
        return get(Role.GENERAL);
    }

    public static Agent get(Role role) {
        for (Agent a:AGENTS) if (a.role==role) return a;
        return AGENTS[AGENTS.length-1];
    }

    public static String catalog() {
        StringBuilder b=new StringBuilder("Agents spécialisés disponibles (moteur local partagé) :\n");
        for (Agent a:AGENTS) b.append("• ").append(a.name).append(" — ").append(a.purpose).append('\n');
        b.append("\nLe coordinateur choisit un spécialiste. Les agents ne sont pas des processus autonomes distants : ils n'ont accès qu'au modèle local et aux outils explicitement implémentés.");
        return b.toString();
    }

    public static String buildPrompt(String request) {
        Agent a=select(request);
        return "VANELLE OMNIGRID — AGENT : "+a.name+"\nRÔLE : "+a.instruction()
            +"\nRÈGLES COMMUNES : Réponds en français sauf demande contraire. N'invente ni accès, ni sources, ni tests, ni résultats. Les actions système doivent passer par les outils explicitement autorisés et les confirmations requises. Si une capacité manque, indique-la franchement.\n\nDEMANDE UTILISATEUR :\n"+request
            +"\n\nFORMAT DE SORTIE : objectif compris; résultat ou plan concret; limites et risques; vérifications nécessaires.";
    }

    private static boolean containsAny(String s,String... terms) {
        for(String t:terms) if(s.contains(t)) return true;
        return false;
    }
}
