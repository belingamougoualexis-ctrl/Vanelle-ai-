package ai.vanelle.omnigrid;

import androidx.test.ext.junit.runners.AndroidJUnit4;
import androidx.test.core.app.ActivityScenario;
import org.junit.Test;
import org.junit.runner.RunWith;
import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.matcher.ViewMatchers.withText;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;

@RunWith(AndroidJUnit4.class)
public class MainActivitySmokeTest {
    @Test public void homeScreenLaunchesAndShowsBrand() {
        try (ActivityScenario<MainActivity> ignored = ActivityScenario.launch(MainActivity.class)) {
            onView(withText("OMNIGRID AI")).check(matches(isDisplayed()));
            onView(withText("Nouvelle tâche")).check(matches(isDisplayed()));
            onView(withText("Paramètres IA et modèles")).check(matches(isDisplayed()));
        }
    }
}
