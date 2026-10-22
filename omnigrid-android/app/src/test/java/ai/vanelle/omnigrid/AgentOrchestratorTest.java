package ai.vanelle.omnigrid;

import org.junit.Test;
import static org.junit.Assert.*;

public class AgentOrchestratorTest {
    @Test public void routesCodingRequestsToDeveloper() {
        assertEquals(AgentOrchestrator.Role.CODING_ASSISTANT,
            AgentOrchestrator.select("Aide-moi à corriger ce bug Java").role);
    }

    @Test public void routesLessonsToTutor() {
        assertEquals(AgentOrchestrator.Role.TUTOR,
            AgentOrchestrator.select("Explique-moi cet exercice de mathématiques").role);
    }

    @Test public void routesSensitiveRequestsToSafetyReviewer() {
        assertEquals(AgentOrchestrator.Role.SAFETY_REVIEWER,
            AgentOrchestrator.select("Comment supprimer définitivement des fichiers ?").role);
    }

    @Test public void routesWritingRequestsToWriter() {
        assertEquals(AgentOrchestrator.Role.WRITER,
            AgentOrchestrator.select("Rédige une lettre officielle").role);
    }

    @Test public void promptNamesSelectedAgentAndDoesNotClaimExecution() {
        String prompt=AgentOrchestrator.buildPrompt("Écris un email");
        assertTrue(prompt.contains("Agent : Rédacteur") || prompt.contains("AGENT : Rédacteur"));
        assertTrue(prompt.contains("N'invente ni accès"));
    }

    @Test public void catalogExplainsActualLimitations() {
        String catalog=AgentOrchestrator.catalog();
        assertTrue(catalog.contains("Tuteur pédagogique"));
        assertTrue(catalog.contains("processus autonomes distants"));
    }
}
