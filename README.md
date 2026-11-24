# 星光圣诞树 · Grand Luxury Tree 安卓离线封装工程

**本 ZIP 是构建工程，不是已编译的 APK。** 当前交付环境无法连接 GitHub 或下载二进制依赖，也没有 Android SDK，未完成实际编译、安装或真机验证。构建成功后才会生成 APK。原网页由 electronicminer 开发（MIT），本工程在构建时下载原作者的移动端 HTML 和许可证，保留原粒子、照片、触摸和手势逻辑，不是用其他圣诞树替代。

原项目：https://github.com/electronicminer/gesture-Christmas_tree-3d_with_photo

## 推荐：使用 GitHub Actions 自动生成 APK（无需本地 Android Studio）

1. 在 GitHub 创建自己的空仓库，例如 `grand-luxury-tree-android`，可选私有仓库，不勾选创建 README。
2. 在 Ubuntu 终端进入解压出来的 `GrandLuxuryTree_Android` 目录，执行下面命令，将 YOUR_USERNAME 换成自己的 GitHub 用户名。需要具备 GitHub 的登录认证和访问网络的能力。

```bash
git init -b main
git add .
git commit -m "Android offline wrapper"
git remote add origin https://github.com/YOUR_USERNAME/grand-luxury-tree-android.git
git push -u origin main
```

3. 在该 GitHub 仓库的 Actions 页面，点击 Build offline Android APK。首次 push 通常会自动运行，也可以点击 Run workflow 手动触发。
4. 构建成功后在该次运行页面的 Artifacts 下载 `GrandLuxuryTree-Android` 压缩包，解压得到 `GrandLuxuryTree-Android.apk`。这是用于自行安装的 debug 签名 APK，不是应用商店发布版。
5. 发送到安卓手机，允许当前文件管理器安装未知来源的应用，安装，打开“星光圣诞树”。点击开启手势，授予相机权限，再通过添加照片选择本地相册图片。

## 本地构建（可选）

需要 JDK 17、Node.js 20、Python 3、Gradle 8.9、Android SDK platform 35/build-tools 35.0.0。安装依赖时需要联网；如网络不可达须先解决网络问题。

```bash
python3 scripts/prepare_assets.py
gradle --no-daemon :app:assembleDebug
```

输出 `app/build/outputs/apk/debug/app-debug.apk`。也可先执行 prepare_assets.py，再用 Android Studio 打开工程并构建 APK。

## 离线方案及使用限制

- Three.js、MediaPipe JS、WASM、手势模型均由构建脚本打入 assets；应用不申请 INTERNET 权限。远程字体、访客统计去除，应用内部仅处理本地 HTTPS 虚拟源，不需本地 HTTP 服务器。
- 原版手势：张手散开、握拳聚合、捏合随机放大照片。触摸拖动旋转，下方按钮切换模式。加入 Android 摄像头运行时权限及系统多图选择。
- Android 8.0 以上为安装下限；建议 Android 12 以上、较新的 Android System WebView、支持 WebGL 和 WebAssembly 的设备。旧手机或特定系统可能因 WebView/GPU 限制不能正常运行。GPU 手势初始化失败后尝试 CPU。
- 相册请选择实际存储在手机内的照片，而不是仅存在云端的照片。照片沿用原版行为，仅本次会话加载；未实现永久保存。
- 构建完成后建议先开启飞行模式，检查首次打开是否显示粒子、摄像头权限、三种手势、相册多选和旋转。自动构建会验证签名与主要资源是否存在，但不能替代真机测试。
- 原源码默认使用 main 分支；若上游变更导致补丁不匹配，会明确报错，而不是静默生成缺资源的包。可通过 TREE_REVISION 环境变量指定已核对的上游提交。
