package ai.vanelle.omnigrid;

import android.content.Context;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.platform.app.InstrumentationRegistry;
import org.junit.Test;
import org.junit.runner.RunWith;
import static org.junit.Assert.assertTrue;
import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;

@RunWith(AndroidJUnit4.class)
public class MainActivitySmokeTest {
    @Test public void homeScreenLaunchesInLocalOnlyMode() {
        try (ActivityScenario<MainActivity> ignored = ActivityScenario.launch(MainActivity.class)) {
            onView(withText("OMNIGRID AI")).check(matches(isDisplayed()));
            onView(withText("Moteur IA local")).check(matches(isDisplayed()));
            onView(withText("Analyser hors ligne")).check(matches(isDisplayed()));
            onView(withText("Télécharger / réinstaller le modèle local")).check(matches(isDisplayed()));
        }
    }

    @Test public void localModelProducesRealTextWhenCiProvidesModel() throws Exception {
        Context context = InstrumentationRegistry.getInstrumentation().getTargetContext();
        if (!LocalModelManager.isPresent(context)) {
            // A regular smoke test without a 429 MB test model remains valid.
            return;
        }
        assertTrue("GGUF SHA-256 verification failed", LocalModelManager.verifyIntegrity(context));
        String answer = LocalInference.generate(context, "Réponds en français en une phrase : pourquoi faut-il tester un logiciel ?");
        assertTrue("Local inference returned empty text", answer != null && !answer.trim().isEmpty());
    }
}
