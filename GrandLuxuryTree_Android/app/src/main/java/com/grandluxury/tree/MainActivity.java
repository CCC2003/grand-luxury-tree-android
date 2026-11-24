package com.grandluxury.tree;

import android.Manifest;
import android.app.Activity;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.webkit.*;
import android.widget.Toast;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.util.Collections;

public class MainActivity extends Activity {
    private static final String HOST = "appassets.androidplatform.net";
    private static final String HOME = "https://" + HOST + "/index.html";
    private static final int CAMERA = 21, PICK = 22;
    private WebView web;
    private PermissionRequest pending;
    private ValueCallback<Uri[]> picker;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        web = new WebView(this);
        web.setBackgroundColor(0xff050d1a);
        setContentView(web);
        immersive();
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(true); // system photo picker only; no broad storage permission
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setMediaPlaybackRequiresUserGesture(false);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) {
                return !trusted(r.getUrl());
            }
            @Override public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest r) {
                Uri u = r.getUrl();
                if (!trusted(u)) return error(403, "Forbidden");
                String path = u.getPath();
                if (path == null || path.contains("..") || path.contains("\\")) return error(403, "Forbidden");
                path = path.equals("/") ? "index.html" : path.substring(1);
                String mime = path.endsWith(".wasm") ? "application/wasm" :
                    path.endsWith(".js") || path.endsWith(".mjs") ? "application/javascript" :
                    path.endsWith(".html") ? "text/html" : path.endsWith(".css") ? "text/css" :
                    path.endsWith(".png") ? "image/png" : path.endsWith(".jpg") ? "image/jpeg" : "application/octet-stream";
                try { return new WebResourceResponse(mime, mime.startsWith("text/") || mime.equals("application/javascript") ? "UTF-8" : null, getAssets().open(path)); }
                catch (IOException e) { return error(404, "Not Found"); }
            }
            @Override public void onReceivedError(WebView v, WebResourceRequest r, WebResourceError e) {
                if (r.isForMainFrame()) Toast.makeText(MainActivity.this,"页面加载失败，请更新 Android System WebView",Toast.LENGTH_LONG).show();
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public void onPermissionRequest(PermissionRequest r) {
                runOnUiThread(() -> {
                    if (!trusted(r.getOrigin()) || !java.util.Arrays.asList(r.getResources()).contains(PermissionRequest.RESOURCE_VIDEO_CAPTURE)) { r.deny(); return; }
                    if (checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) grantCamera(r);
                    else { if(pending != null) pending.deny(); pending = r; requestPermissions(new String[]{Manifest.permission.CAMERA}, CAMERA); }
                });
            }
            @Override public void onPermissionRequestCanceled(PermissionRequest r) { runOnUiThread(() -> { if(pending == r) pending = null; }); }
            @Override public boolean onShowFileChooser(WebView v, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (picker != null) picker.onReceiveValue(null);
                picker = callback;
                Intent i = new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("image/*");
                i.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
                try { startActivityForResult(i, PICK); } catch (Exception ex) { picker.onReceiveValue(null); picker = null; }
                return true;
            }
        });
        web.loadUrl(HOME);
    }
    private boolean trusted(Uri u) { return u != null && "https".equals(u.getScheme()) && HOST.equals(u.getHost()) && (u.getPort() == -1 || u.getPort() == 443); }
    private WebResourceResponse error(int code, String reason) { return new WebResourceResponse("text/plain", "UTF-8", code, reason, Collections.emptyMap(), new ByteArrayInputStream(new byte[0])); }
    private void grantCamera(PermissionRequest r) { r.grant(new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE}); }
    @Override public void onRequestPermissionsResult(int req, String[] p, int[] g) {
        super.onRequestPermissionsResult(req,p,g);
        if(req == CAMERA && pending != null) { if(g.length > 0 && g[0] == PackageManager.PERMISSION_GRANTED) grantCamera(pending); else pending.deny(); pending = null; }
    }
    @Override protected void onActivityResult(int req, int result, Intent data) {
        super.onActivityResult(req,result,data);
        if(req == PICK && picker != null) {
            Uri[] values = null;
            if(result == RESULT_OK && data != null) {
                if(data.getClipData() != null) { int n=data.getClipData().getItemCount(); values=new Uri[n]; for(int i=0;i<n;i++) values[i]=data.getClipData().getItemAt(i).getUri(); }
                else if(data.getData()!=null) values = new Uri[]{data.getData()};
            }
            picker.onReceiveValue(values); picker=null;
        }
    }
    private void immersive() { getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_STABLE); }
    @Override public void onWindowFocusChanged(boolean focused) { super.onWindowFocusChanged(focused); if(focused) immersive(); }
    @Override protected void onPause() { if(web!=null) web.onPause(); super.onPause(); }
    @Override protected void onResume() { super.onResume(); if(web!=null) web.onResume(); immersive(); }
    @Override protected void onDestroy() { if(pending!=null) pending.deny(); if(picker!=null) picker.onReceiveValue(null); if(web!=null){ web.destroy(); web=null; } super.onDestroy(); }
}
