package local.weread.home;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.role.RoleManager;
import android.content.ComponentName;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.provider.Settings;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

public class ControlActivity extends Activity {
    protected SharedPreferences getPreferencesStore() {
        return getSharedPreferences("home", MODE_PRIVATE);
    }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        showControls();
    }

    protected void showControls() {
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(Color.WHITE);
        LinearLayout column = new LinearLayout(this);
        column.setOrientation(LinearLayout.VERTICAL);
        column.setPadding(dp(28), dp(36), dp(28), dp(28));
        scroll.addView(column);
        TextView title = new TextView(this);
        title.setText("文石微信读书极简首页");
        title.setTextColor(Color.BLACK);
        title.setTextSize(28);
        column.addView(title);
        boolean dedicated = getPreferencesStore().getBoolean("dedicated", false);
        TextView note = new TextView(this);
        note.setText(dedicated
            ? "当前：微信读书专用模式\n开机和返回首页时进入微信读书。\n4 秒内返回首页两次，可打开此设置页。"
            : "当前：极简首页模式\n点击下方按钮阅读或进入设置。\n可随时切换为微信读书专用模式。");
        note.setTextColor(Color.DKGRAY);
        note.setTextSize(18);
        note.setPadding(0, dp(14), 0, dp(20));
        column.addView(note);
        button(column, "打开微信读书", () -> openReader());
        button(column, dedicated ? "切换为极简首页" : "切换为微信读书专用模式", () -> {
            getPreferencesStore().edit().putBoolean("dedicated", !dedicated).apply();
            showControls();
            Toast.makeText(this, "模式已切换，下次返回首页生效。", Toast.LENGTH_LONG).show();
        });
        button(column, "Wi-Fi 设置", () -> open(new Intent(Settings.ACTION_WIFI_SETTINGS)));
        button(column, "系统设置", () -> open(new Intent(Settings.ACTION_SETTINGS)));
        button(column, "文石桌面 · 墨水屏与前光", () -> openBoox());
        button(column, "设为默认首页", () -> enableHome());
        button(column, "恢复原来的文石首页", () -> confirmRestore());
        TextView services = new TextView(this);
        services.setText("应用及 Google 服务的停用与恢复，请在电脑端运行配套工具，逐项选择。此首页不会自动停用任何服务。");
        services.setTextColor(Color.DKGRAY);
        services.setTextSize(16);
        services.setPadding(0, dp(20), 0, dp(16));
        column.addView(services);
        setContentView(scroll);
    }

    private int dp(int value) { return Math.round(value * getResources().getDisplayMetrics().density); }

    private void button(LinearLayout column, String text, Runnable action) {
        Button b = new Button(this);
        b.setText(text);
        b.setTextColor(Color.BLACK);
        b.setTextSize(20);
        b.setAllCaps(false);
        b.setMinHeight(dp(62));
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.topMargin = dp(12);
        column.addView(b, params);
        b.setOnClickListener(v -> action.run());
    }

    protected boolean openReader() {
        // Prefer the e-ink edition, with the regular edition as a fallback.
        for (String pkg : new String[]{"com.tencent.weread.eink", "com.tencent.weread"}) {
            try {
                Intent launch = getPackageManager().getLaunchIntentForPackage(pkg);
                if (launch == null) continue;
                launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_RESET_TASK_IF_NEEDED);
                startActivity(launch);
                return true;
            } catch (RuntimeException ex) { /* Try the next installed edition. */ }
        }
        Toast.makeText(this, "无法打开微信读书，请在原文石桌面检查是否已安装、启用。", Toast.LENGTH_LONG).show();
        return false;
    }

    private void open(Intent intent) {
        try { startActivity(intent); }
        catch (RuntimeException ex) { Toast.makeText(this, "无法打开此设置，请使用原厂设置入口。", Toast.LENGTH_LONG).show(); }
    }

    private Intent booxIntent() {
        return new Intent().setComponent(new ComponentName("com.onyx", "com.onyx.StartupActivity"));
    }

    private void openBoox() { open(booxIntent()); }

    private void enableHome() {
        getPackageManager().setComponentEnabledSetting(new ComponentName(this, HomeActivity.class),
            PackageManager.COMPONENT_ENABLED_STATE_ENABLED, PackageManager.DONT_KILL_APP);
        // RoleManager is available from Android 10; Android 8/9 use the system chooser.
        if (Build.VERSION.SDK_INT >= 29) {
            RoleManager roles = getSystemService(RoleManager.class);
            if (roles != null && roles.isRoleAvailable(RoleManager.ROLE_HOME)) {
                if (!roles.isRoleHeld(RoleManager.ROLE_HOME)) {
                    try { startActivityForResult(roles.createRequestRoleIntent(RoleManager.ROLE_HOME), 1); }
                    catch (RuntimeException ex) { open(new Intent(Settings.ACTION_HOME_SETTINGS)); }
                } else Toast.makeText(this, "已经是默认首页。", Toast.LENGTH_SHORT).show();
                return;
            }
        }
        open(new Intent(Settings.ACTION_HOME_SETTINGS));
    }

    private void confirmRestore() {
        Intent original = booxIntent();
        if (original.resolveActivity(getPackageManager()) == null) {
            Toast.makeText(this, "找不到文石原厂桌面，请在系统中手动选择默认首页。", Toast.LENGTH_LONG).show();
            open(new Intent(Settings.ACTION_HOME_SETTINGS));
            return;
        }
        new AlertDialog.Builder(this).setTitle("恢复文石首页？")
            .setMessage("恢复后，返回首页将使用原厂桌面。本工具的首页入口会停用，应用列表中的设置入口保留。书籍和服务停用状态保持。")
            .setNegativeButton("取消", null)
            .setPositiveButton("恢复", (dialog, which) -> {
                try {
                    // Verify the original launcher can open before disabling our HOME component.
                    startActivity(original);
                    getPackageManager().clearPackagePreferredActivities(getPackageName());
                    getPackageManager().setComponentEnabledSetting(new ComponentName(this, HomeActivity.class),
                        PackageManager.COMPONENT_ENABLED_STATE_DISABLED, PackageManager.DONT_KILL_APP);
                    finish();
                } catch (RuntimeException ex) {
                    Toast.makeText(this, "恢复失败，请在系统默认应用中选择原桌面。", Toast.LENGTH_LONG).show();
                }
            }).show();
    }
}
