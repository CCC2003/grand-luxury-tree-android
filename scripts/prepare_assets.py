#!/usr/bin/env python3
"""Fetch upstream MIT project and build self-contained WebView assets."""
import pathlib, re, shutil, subprocess, tempfile, urllib.request, sys, os
ROOT = pathlib.Path(__file__).resolve().parents[1]
DEST = ROOT / 'app/src/main/assets'
REPO = 'https://raw.githubusercontent.com/electronicminer/gesture-Christmas_tree-3d_with_photo/'
REV = os.getenv('TREE_REVISION', 'main')
MODEL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'

def download(url, target):
    print('Downloading', url, flush=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent':'GrandLuxuryTree-Android-build/1.0'})
    with urllib.request.urlopen(req, timeout=180) as r, target.open('wb') as f:
        shutil.copyfileobj(r,f)
    if target.stat().st_size == 0:
        raise RuntimeError(f'Empty download: {url}')


def fix_photo_focus(js):
    def replace_checked(old, new):
        nonlocal js
        if js.count(old) != 1:
            raise RuntimeError(
                "Photo focus patch mismatch: " + old[:80]
            )
        js = js.replace(old, new, 1)

    # 1. 根据摄像机中心计算照片位置
    replace_checked(
        """const desiredWorldPos = new THREE.Vector3(0, 2, 35);
                        const invMatrix = new THREE.Matrix4().copy(mainGroup.matrixWorld).invert();
                        target = desiredWorldPos.applyMatrix4(invMatrix);""",
        """const desiredWorldPos = camera.localToWorld(
                            new THREE.Vector3(0, 0, -15)
                        );
                        target = this.mesh.parent.worldToLocal(
                            desiredWorldPos
                        );"""
    )

    # 2. 自动适应横屏和竖屏尺寸
    replace_checked(
        "if (this.mesh === focusTargetMesh) s = 4.5; else s = this.baseScale * 0.8;",
        """if (this.mesh === focusTargetMesh) {
                        const frame = this.mesh.children[0];

                        const w = frame.geometry.parameters.width
                                  * frame.scale.x;

                        const h = frame.geometry.parameters.height
                                  * frame.scale.y;

                        const viewH = 30 * Math.tan(
                            THREE.MathUtils.degToRad(camera.fov / 2)
                        ) / camera.zoom;

                        const viewW = viewH * camera.aspect;

                        s = Math.min(
                            4.5,
                            viewW * 0.80 / w,
                            viewH * 0.70 / h
                        );
                    } else {
                        s = this.baseScale * 0.8;
                    }"""
    )

    # 3. 放大照片时暂停场景旋转
    replace_checked(
        """mainGroup.rotation.y = STATE.rotation.y;
            mainGroup.rotation.x = STATE.rotation.x;""",
        """if (STATE.mode === 'FOCUS') {
                STATE.rotation.y = mainGroup.rotation.y;
                STATE.rotation.x = mainGroup.rotation.x;
            } else {
                mainGroup.rotation.y = STATE.rotation.y;
                mainGroup.rotation.x = STATE.rotation.x;
            }

            mainGroup.updateMatrixWorld(true);"""
    )

    # 4. 防止低帧率时动画插值越界
    replace_checked(
        "this.mesh.position.lerp(target, lerpSpeed * dt);",
        "this.mesh.position.lerp(target, Math.min(1, lerpSpeed * dt));"
    )

    replace_checked(
        "this.mesh.scale.lerp(new THREE.Vector3(s,s,s), 4*dt);",
        "this.mesh.scale.lerp(new THREE.Vector3(s,s,s), Math.min(1, 4*dt));"
    )

    return js


def patch(html):
    # Optional web statistics and remote fonts are unnecessary offline.
    html = re.sub(r'<link\b[^>]*href=["\']https://cdnjs\.cloudflare\.com/[^"\']+["\'][^>]*>', '', html, flags=re.I)
    html = re.sub(r'<script\b[^>]*src=["\'](?:https:)?//(?:busuanzi\.ibruce\.info|mapmyvisitors\.com)/[^"\']+["\'][^>]*>\s*</script>', '', html, flags=re.I)
    html = re.sub(r'@import\s+url\(["\']https://fonts\.googleapis\.com/[^)]+\)\s*;', '', html)
    html = re.sub(r'<script\s+type=["\']importmap["\']\s*>.*?</script>', '', html, flags=re.S)
    html = html.replace('https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm', './wasm')
    html = html.replace(MODEL, './models/hand_landmarker.task')
    html = html.replace('autoScanLocal: true', 'autoScanLocal: false')
    html = html.replace('webkitdirectory directory multiple', 'multiple accept="image/*"')
    html = html.replace('Select Folder', '选择照片').replace('Select Files', '添加照片')
    html = html.replace('📷 Enable Gesture', '📷 开启手势').replace('Loading Memories', '正在加载星光')
    html = html.replace('Touch: Drag | Click Photo | Press \'S\' for Stats', '拖动旋转 · 点击照片放大')
    html = html.replace('Initializing...', '正在初始化…').replace('Gesture Active: Show Hand', '请将手掌对准前置摄像头').replace('Gesture Active', '手势已开启').replace('Retry Camera', '重试摄像头')
    html = html.replace('autoplay playsinline', 'autoplay muted playsinline')
    # Try GPU first; fall back to CPU on unsupported mobile WebViews.
    pattern = r'handLandmarker\s*=\s*await HandLandmarker\.createFromOptions\(vision,\s*(\{\s*baseOptions:.*?numHands:\s*1\s*\})\s*\);'
    def fallback(m):
        return 'const options = '+m.group(1)+';\n                try { handLandmarker = await HandLandmarker.createFromOptions(vision, options); } catch (gpuError) { options.baseOptions.delegate = "CPU"; handLandmarker = await HandLandmarker.createFromOptions(vision, options); }'
    html, n = re.subn(pattern, fallback, html, count=1, flags=re.S)
    if n != 1:
        raise RuntimeError('Upstream camera code changed; review patch before building.')
    # Avoid loading hundreds of missing images; hide duplicate album control on mobile.
    html = html.replace('</head>', '<style>label.control-btn:has(#folder-input){display:none} #footer-stats{display:none!important} @media(max-width:600px){.controls-wrapper{top:90px;right:10px}.control-btn{min-width:95px;padding:9px 12px}.hint-text{max-width:145px} #mode-bar{bottom:24px}}</style></head>')
    m = re.search(r'<script\s+type=["\']module["\']\s*>(.*?)</script>', html, re.S)
    if not m or './models/hand_landmarker.task' not in m.group(1) or './wasm' not in m.group(1):
        raise RuntimeError('Upstream layout changed; offline paths not found.')
    js = fix_photo_focus(m.group(1))
    html = html[:m.start()]+'<script type="module" src="./app.js"></script>'+html[m.end():]
    if re.search(r'(?:src|href)\s*=\s*["\'](?:https?:)?//', html, re.I) or re.search(r'https?://(?:cdn\.jsdelivr\.net|storage\.googleapis\.com)',js):
        raise RuntimeError('Unexpected external resource remains.')
    return html, js

def main():
    for cmd in ('node','npm'):
        if not shutil.which(cmd): raise RuntimeError(f'Install {cmd} (Node.js 20 recommended) first.')
    with tempfile.TemporaryDirectory(prefix='tree-build-') as td:
        work=pathlib.Path(td); assets=work/'assets'; assets.mkdir()
        download(REPO+REV+'/christmas_tree_touch%26gesture.html', work/'upstream.html')
        download(REPO+REV+'/LICENSE', assets/'UPSTREAM-LICENSE.txt')
        html,js=patch((work/'upstream.html').read_text(encoding='utf-8'))
        (assets/'index.html').write_text(html, encoding='utf-8')
        (work/'entry.js').write_text(js, encoding='utf-8')
        subprocess.run([shutil.which('npm'),'install','--no-audit','--no-fund','--save-exact','three@0.160.0','@mediapipe/tasks-vision@0.10.3','esbuild@0.24.2'],cwd=work,check=True)
        # Use npm exec so the executable also resolves on Windows.
        subprocess.run(['node','-e', "require('esbuild').buildSync({entryPoints:['entry.js'],bundle:true,format:'esm',platform:'browser',target:'chrome100',outfile:'assets/app.js',legalComments:'inline'})"], cwd=work,check=True)
        mp=work/'node_modules/@mediapipe/tasks-vision'
        shutil.copytree(mp/'wasm',assets/'wasm')
        licenses=assets/'licenses'; licenses.mkdir()
        for name,path in [('three',work/'node_modules/three'),('mediapipe',mp)]:
            for file in path.iterdir():
                if file.is_file() and file.name.lower().startswith(('license','notice')):
                    shutil.copyfile(file,licenses/(name+'-'+file.name))
        download(MODEL,assets/'models/hand_landmarker.task')
        for p in ('vision_wasm_internal.wasm','vision_wasm_nosimd_internal.wasm','vision_wasm_internal.js','vision_wasm_nosimd_internal.js'):
            f=assets/'wasm'/p
            if not f.is_file() or f.stat().st_size==0: raise RuntimeError('Missing WASM dependency: '+p)
        for f in (assets/'wasm').glob('*.wasm'):
            with f.open('rb') as fp:
                if fp.read(4)!=b'\x00asm': raise RuntimeError('Invalid WASM: '+str(f))
        if (assets/'models/hand_landmarker.task').stat().st_size < 100000: raise RuntimeError('Model download too small')
        (assets/'licenses'/'SOURCES.txt').write_text(f'Upstream: {REPO}{REV}/\nModel: {MODEL}\nThree.js 0.160.0; MediaPipe Tasks Vision 0.10.3\nAndroid adaptation: local-only WebView and localized controls.\n',encoding='utf-8')
        if DEST.exists(): shutil.rmtree(DEST)
        shutil.copytree(assets,DEST)
    print('Offline assets ready:', DEST)

if __name__=='__main__': main()
