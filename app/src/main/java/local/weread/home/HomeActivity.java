package local.weread.home;

import android.content.Intent;
import android.os.Bundle;
import android.os.SystemClock;

public class HomeActivity extends ControlActivity {
    private static long lastHome = -10000L;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        routeHome();
    }

    @Override protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        setIntent(intent);
        routeHome();
    }

    private void routeHome() {
        long now = SystemClock.elapsedRealtime();
        boolean repeated = now - lastHome < 4000;
        lastHome = now;
        showControls();
        if (getPreferencesStore().getBoolean("dedicated", false) && !repeated) openReader();
    }

    @Override public void onBackPressed() {
        // The controls remain a reachable exit even when the reader is unavailable.
        if (getPreferencesStore().getBoolean("dedicated", false)) openReader();
    }
}
