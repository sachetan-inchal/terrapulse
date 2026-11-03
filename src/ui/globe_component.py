"""Interactive 3D Photorealistic Earth Globe WebGL Component for Streamlit.

Renders an authentic, interactive 3D WebGL spherical Earth in space with:
- Three.js WebGL orbital globe with atmosphere glow, starfield, and rotation controls
- Exact UV-matching lat/lon to Three.js Cartesian coordinate mapping
- Display of actual geographic scene footprints and 4-quadrant tiles on the globe
- Spherical coordinate patch projection: STICKS the satellite mosaic/scene directly
  onto the curvature of the 3D Earth at its exact geographic bounding box (lat/lon)
- Smooth animated camera fly-in from orbital space down to the regional observation
- Clean Light-Theme glassmorphism HUD with resolved place name, coordinates, and instant fly-to buttons
- Top-right HUD controls (Zoom in, Zoom out, Compass, Recenter)
"""

import base64
import json
from io import BytesIO
from typing import List, Dict, Any, Optional
from PIL import Image
import numpy as np


def _image_to_base64_jpeg(img_or_arr, max_dim: int = 800) -> str:
    """Converts a PIL Image, filepath, or numpy array to a compressed base64 JPEG data URI."""
    try:
        if isinstance(img_or_arr, str):
            im = Image.open(img_or_arr).convert("RGB")
        elif isinstance(img_or_arr, np.ndarray):
            im = Image.fromarray(img_or_arr).convert("RGB")
        elif isinstance(img_or_arr, Image.Image):
            im = img_or_arr.convert("RGB")
        else:
            return ""

        if max(im.size) > max_dim:
            im.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        buf = BytesIO()
        im.save(buf, format="JPEG", quality=82)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image to base64: {e}")
        return ""


def build_3d_globe_html(
    target_name: str,
    lat: float,
    lon: float,
    bbox: List[float],  # [min_lon, min_lat, max_lon, max_lat]
    stitched_image: Any,  # ndarray or PIL Image or filepath
    scenes: Optional[List[Dict[str, Any]]] = None,
    active_scene_id: Optional[str] = "mosaic",
    height_px: int = 560
) -> str:
    """
    Constructs a standalone, responsive WebGL 3D Globe HTML string with Three.js.
    Accurately navigates and zooms to target coordinates and displays true scene footprints.
    """
    stitched_b64 = _image_to_base64_jpeg(stitched_image)
    if not stitched_b64:
        stitched_b64 = _image_to_base64_jpeg("stitched_result.jpg")

    min_lon, min_lat, max_lon, max_lat = bbox[0], bbox[1], bbox[2], bbox[3]

    scenes_data = []
    if scenes:
        for sc in scenes[:8]:
            sc_bbox = sc.get("bbox", [])
            if len(sc_bbox) == 4:
                scenes_data.append({
                    "id": sc.get("id", ""),
                    "date": sc.get("date", ""),
                    "bbox": sc_bbox,
                    "isSelected": (sc.get("id") == active_scene_id),
                    "isQuadrant": sc.get("is_quadrant", False),
                    "quadrantLabel": sc.get("quadrant_label", "")
                })

    payload_json = json.dumps({
        "targetName": target_name,
        "lat": lat,
        "lon": lon,
        "bbox": [min_lon, min_lat, max_lon, max_lat],
        "stitchedImage": stitched_b64,
        "scenes": scenes_data,
        "activeSceneId": active_scene_id
    })

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body, html {{ width: 100%; height: 100%; overflow: hidden; background: #0f172a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
    #canvas-container {{ width: 100%; height: 100%; position: relative; }}
    
    /* Clean Light Glassmorphism Overlays */
    .hud-overlay {{
        position: absolute;
        pointer-events: none;
        z-index: 10;
    }}
    
    /* Top Left Target Search Card */
    .target-card {{
        top: 14px;
        left: 16px;
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid #bfdbfe;
        border-radius: 10px;
        padding: 12px 16px;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
        pointer-events: auto;
        color: #0f172a;
        display: flex;
        flex-direction: column;
        gap: 5px;
        max-width: 330px;
    }}
    .target-title {{
        font-size: 0.92rem;
        font-weight: 700;
        color: #0f172a;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    .target-coords {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #2563eb;
        font-weight: 600;
    }}
    .target-btn-group {{
        display: flex;
        gap: 6px;
        margin-top: 4px;
    }}
    .action-btn {{
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        color: #1d4ed8;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.15s ease;
        text-align: center;
    }}
    .action-btn:hover {{
        background: #2563eb;
        color: #ffffff;
        border-color: #1d4ed8;
    }}
    
    /* Top Right Floating HUD Controls */
    .hud-controls {{
        top: 14px;
        right: 16px;
        display: flex;
        flex-direction: column;
        gap: 6px;
        pointer-events: auto;
    }}
    .hud-btn {{
        width: 34px;
        height: 34px;
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        color: #334155;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.15s ease;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
    }}
    .hud-btn:hover {{
        background: #eff6ff;
        border-color: #2563eb;
        color: #2563eb;
    }}
    
    /* Bottom Status Strip */
    .timeline-strip {{
        bottom: 12px;
        left: 50%;
        transform: translateX(-50%);
        background: rgba(255, 255, 255, 0.94);
        border: 1px solid #cbd5e1;
        border-radius: 30px;
        padding: 6px 20px;
        display: flex;
        align-items: center;
        gap: 12px;
        backdrop-filter: blur(10px);
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #334155;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
        pointer-events: auto;
    }}
    .timeline-dot {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #059669;
        box-shadow: 0 0 6px #059669;
        animation: pulse 1.8s infinite;
    }}
    @keyframes pulse {{
        0%, 100% {{ opacity: 1; transform: scale(1); }}
        50% {{ opacity: 0.4; transform: scale(1.2); }}
    }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
</head>
<body>

<div id="canvas-container">
    <!-- Top Left Target / Region Info -->
    <div class="hud-overlay target-card">
        <div class="target-title">
            <span>📍</span> <span id="ui-target-name">Target Region</span>
        </div>
        <div class="target-coords" id="ui-coords">--° N, --° E</div>
        <div style="font-size: 0.70rem; color: #64748b;">
            Georeferenced Satellite Projection Clamped to Surface
        </div>
        <div class="target-btn-group">
            <button class="action-btn" id="btn-zoom-region">🔍 Zoom to AOI</button>
            <button class="action-btn" id="btn-zoom-orbit">🌍 Full Orbit</button>
        </div>
    </div>

    <!-- Top Right Controls -->
    <div class="hud-overlay hud-controls">
        <button class="hud-btn" id="btn-compass" title="Reset North">🧭</button>
        <button class="hud-btn" id="btn-plus" title="Zoom In">+</button>
        <button class="hud-btn" id="btn-minus" title="Zoom Out">-</button>
        <button class="hud-btn" id="btn-recenter" title="Recenter Target">🎯</button>
    </div>

    <!-- Bottom Status -->
    <div class="hud-overlay timeline-strip">
        <div class="timeline-dot"></div>
        <span style="font-weight: 600;">3D SPHERICAL SURFACE PROJECTION</span>
        <span style="color: #cbd5e1;">|</span>
        <span id="ui-bbox-info">AOI: [...]</span>
    </div>
</div>

<script>
    const DATA = {payload_json};
    
    document.getElementById("ui-target-name").innerText = DATA.targetName;
    document.getElementById("ui-coords").innerText = `${{DATA.lat.toFixed(4)}}° N, ${{DATA.lon.toFixed(4)}}° E`;
    document.getElementById("ui-bbox-info").innerText = `AOI: [${{DATA.bbox[0].toFixed(2)}}, ${{DATA.bbox[1].toFixed(2)}}, ${{DATA.bbox[2].toFixed(2)}}, ${{DATA.bbox[3].toFixed(2)}}]`;

    const container = document.getElementById("canvas-container");

    // =========================================================================
    // 1. THREE.JS SCENE SETUP
    // =========================================================================
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 2000);
    const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true }});
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 104;
    controls.maxDistance = 500;
    controls.rotateSpeed = 0.6;

    // Ambient & Directional Lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.3);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, 1.4);
    sunLight.position.set(400, 200, 300);
    scene.add(sunLight);

    // =========================================================================
    // 2. STARFIELD BACKGROUND
    // =========================================================================
    const starsGeom = new THREE.BufferGeometry();
    const starCount = 1000;
    const starPos = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount * 3; i += 3) {{
        starPos[i] = (Math.random() - 0.5) * 1200;
        starPos[i+1] = (Math.random() - 0.5) * 1200;
        starPos[i+2] = (Math.random() - 0.5) * 1200;
    }}
    starsGeom.setAttribute("position", new THREE.BufferAttribute(starPos, 3));
    const starsMat = new THREE.PointsMaterial({{ color: 0x94a3b8, size: 1.0, transparent: true, opacity: 0.6 }});
    const starField = new THREE.Points(starsGeom, starsMat);
    scene.add(starField);

    // =========================================================================
    // 3. PHOTOREALISTIC EARTH GLOBE SPHERE
    // =========================================================================
    const GLOBE_RADIUS = 100.0;
    const globeGeom = new THREE.SphereGeometry(GLOBE_RADIUS, 64, 64);

    const textureLoader = new THREE.TextureLoader();
    const earthTexture = textureLoader.load(
        "https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg",
        () => renderer.render(scene, camera)
    );

    const globeMat = new THREE.MeshStandardMaterial({{
        map: earthTexture,
        roughness: 0.85,
        metalness: 0.05
    }});
    const globeMesh = new THREE.Mesh(globeGeom, globeMat);
    scene.add(globeMesh);

    // Subtle Atmosphere Glow Layer
    const atmosGeom = new THREE.SphereGeometry(GLOBE_RADIUS * 1.015, 64, 64);
    const atmosMat = new THREE.MeshBasicMaterial({{
        color: 0x38bdf8,
        transparent: true,
        opacity: 0.12,
        side: THREE.BackSide
    }});
    const atmosMesh = new THREE.Mesh(atmosGeom, atmosMat);
    scene.add(atmosMesh);

    // =========================================================================
    // 4. PRECISE COORDINATE MATH: LAT/LON TO THREE.JS SPHERE VERTEX
    // =========================================================================
    function latLonToXYZ(lat, lon, radius) {{
        const u = (lon + 180.0) / 360.0;
        const v = (90.0 - lat) / 180.0;
        const thetaLength = Math.PI;
        const phiLength = 2 * Math.PI;
        const x = - radius * Math.cos(u * phiLength) * Math.sin(v * thetaLength);
        const y = radius * Math.cos(v * thetaLength);
        const z = radius * Math.sin(u * phiLength) * Math.sin(v * thetaLength);
        return new THREE.Vector3(x, y, z);
    }}

    // Target Location Marker (Pin at Coordinates)
    const targetPos = latLonToXYZ(DATA.lat, DATA.lon, GLOBE_RADIUS);
    const targetNorm = targetPos.clone().normalize();

    // Red Pulsing Target Pin
    const markerGeom = new THREE.SphereGeometry(1.2, 16, 16);
    const markerMat = new THREE.MeshBasicMaterial({{ color: 0xef4444 }});
    const markerMesh = new THREE.Mesh(markerGeom, markerMat);
    markerMesh.position.copy(latLonToXYZ(DATA.lat, DATA.lon, GLOBE_RADIUS * 1.006));
    scene.add(markerMesh);

    // Concentric Ring Beacon
    const ringGeom = new THREE.RingGeometry(1.5, 2.5, 32);
    const ringMat = new THREE.MeshBasicMaterial({{ color: 0x2563eb, side: THREE.DoubleSide, transparent: true, opacity: 0.85 }});
    const ringMesh = new THREE.Mesh(ringGeom, ringMat);
    ringMesh.position.copy(latLonToXYZ(DATA.lat, DATA.lon, GLOBE_RADIUS * 1.008));
    ringMesh.lookAt(targetPos.clone().multiplyScalar(2));
    scene.add(ringMesh);

    // Vertical Laser Beacon Beam
    const beamGeom = new THREE.CylinderGeometry(0.2, 0.2, 22, 8);
    const beamMat = new THREE.MeshBasicMaterial({{ color: 0x3b82f6, transparent: true, opacity: 0.6 }});
    const beamMesh = new THREE.Mesh(beamGeom, beamMat);
    beamMesh.position.copy(latLonToXYZ(DATA.lat, DATA.lon, GLOBE_RADIUS + 11.0));
    beamMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), targetNorm);
    scene.add(beamMesh);

    // =========================================================================
    // 5. STICK OUR SATELLITE IMAGE DIRECTLY ONTO THE GLOBE CURVATURE
    // =========================================================================
    function createStitchedStickerMesh(minLon, minLat, maxLon, maxLat, radius, imageB64) {{
        const segments = 24;
        const geom = new THREE.BufferGeometry();
        const positions = [];
        const uvs = [];
        const indices = [];

        for (let i = 0; i <= segments; i++) {{
            const v = i / segments;
            const curLat = minLat + v * (maxLat - minLat);

            for (let j = 0; j <= segments; j++) {{
                const u = j / segments;
                const curLon = minLon + u * (maxLon - minLon);

                const pt = latLonToXYZ(curLat, curLon, radius);
                positions.push(pt.x, pt.y, pt.z);
                uvs.push(u, v);
            }}
        }}

        for (let i = 0; i < segments; i++) {{
            for (let j = 0; j < segments; j++) {{
                const a = i * (segments + 1) + j;
                const b = (i + 1) * (segments + 1) + j;
                const c = (i + 1) * (segments + 1) + (j + 1);
                const d = i * (segments + 1) + (j + 1);

                indices.push(a, b, d);
                indices.push(b, c, d);
            }}
        }}

        geom.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
        geom.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
        geom.setIndex(indices);
        geom.computeVertexNormals();

        const stickerTex = textureLoader.load(imageB64);
        stickerTex.generateMipmaps = true;

        const stickerMat = new THREE.MeshBasicMaterial({{
            map: stickerTex,
            transparent: true,
            opacity: 0.98,
            side: THREE.DoubleSide
        }});

        return new THREE.Mesh(geom, stickerMat);
    }}

    const stickerMesh = createStitchedStickerMesh(
        DATA.bbox[0], DATA.bbox[1], DATA.bbox[2], DATA.bbox[3],
        GLOBE_RADIUS * 1.004,
        DATA.stitchedImage
    );
    scene.add(stickerMesh);

    // AOI Boundary Outline
    const aoiPts = [
        latLonToXYZ(DATA.bbox[1], DATA.bbox[0], GLOBE_RADIUS * 1.007),
        latLonToXYZ(DATA.bbox[1], DATA.bbox[2], GLOBE_RADIUS * 1.007),
        latLonToXYZ(DATA.bbox[3], DATA.bbox[2], GLOBE_RADIUS * 1.007),
        latLonToXYZ(DATA.bbox[3], DATA.bbox[0], GLOBE_RADIUS * 1.007),
        latLonToXYZ(DATA.bbox[1], DATA.bbox[0], GLOBE_RADIUS * 1.007)
    ];
    const aoiGeom = new THREE.BufferGeometry().setFromPoints(aoiPts);
    const aoiMat = new THREE.LineBasicMaterial({{ color: 0x2563eb, linewidth: 3 }});
    const aoiLine = new THREE.Line(aoiGeom, aoiMat);
    scene.add(aoiLine);

    // =========================================================================
    // 5b. SCENE FOOTPRINT OUTLINES (GEOGRAPHIC SYNCHRONIZATION)
    // =========================================================================
    if (DATA.scenes && DATA.scenes.length > 0) {{
        const quadColors = [0x3b82f6, 0x10b981, 0xf59e0b, 0x8b5cf6];
        DATA.scenes.forEach((sc, idx) => {{
            const b = sc.bbox;
            if (b && b.length === 4) {{
                const fPts = [
                    latLonToXYZ(b[1], b[0], GLOBE_RADIUS * 1.005),
                    latLonToXYZ(b[1], b[2], GLOBE_RADIUS * 1.005),
                    latLonToXYZ(b[3], b[2], GLOBE_RADIUS * 1.005),
                    latLonToXYZ(b[3], b[0], GLOBE_RADIUS * 1.005),
                    latLonToXYZ(b[1], b[0], GLOBE_RADIUS * 1.005)
                ];
                const fGeom = new THREE.BufferGeometry().setFromPoints(fPts);
                let col = 0x64748b;
                if (sc.isSelected) {{
                    col = 0xf59e0b; // Gold for active selection
                }} else if (sc.isQuadrant) {{
                    col = quadColors[idx % quadColors.length];
                }}
                const fMat = new THREE.LineBasicMaterial({{ color: col, linewidth: sc.isSelected ? 3 : 1 }});
                const fLine = new THREE.Line(fGeom, fMat);
                scene.add(fLine);
            }}
        }});
    }}

    // =========================================================================
    // 6. INITIAL CAMERA ALIGNMENT: DIRECTLY FACING TARGET COORDINATES
    // =========================================================================
    const ORBIT_DISTANCE = 250.0;
    const REGION_DISTANCE = 114.0;

    camera.position.copy(targetNorm.clone().multiplyScalar(ORBIT_DISTANCE));
    camera.lookAt(targetPos);
    controls.target.copy(new THREE.Vector3(0, 0, 0));
    controls.update();

    // =========================================================================
    // 7. CAMERA FLY-IN ANIMATION CONTROLLER
    // =========================================================================
    let isAnimating = false;
    let animStartPos = new THREE.Vector3();
    let animEndPos = new THREE.Vector3();
    let animStartTarget = new THREE.Vector3();
    let animEndTarget = new THREE.Vector3();
    let animProgress = 0;

    function flyTo(targetDistance, targetLookAt) {{
        animStartPos.copy(camera.position);
        animEndPos.copy(targetNorm.clone().multiplyScalar(targetDistance));
        animStartTarget.copy(controls.target);
        animEndTarget.copy(targetLookAt);
        animProgress = 0;
        isAnimating = true;
    }}

    setTimeout(() => {{
        flyTo(REGION_DISTANCE, targetPos);
    }}, 400);

    document.getElementById("btn-zoom-region").addEventListener("click", () => {{
        flyTo(REGION_DISTANCE, targetPos);
    }});

    document.getElementById("btn-zoom-orbit").addEventListener("click", () => {{
        flyTo(ORBIT_DISTANCE, new THREE.Vector3(0, 0, 0));
    }});

    document.getElementById("btn-compass").addEventListener("click", () => {{
        flyTo(ORBIT_DISTANCE, new THREE.Vector3(0, 0, 0));
    }});

    document.getElementById("btn-plus").addEventListener("click", () => {{
        const curDist = camera.position.length();
        flyTo(Math.max(curDist * 0.75, 105), controls.target);
    }});

    document.getElementById("btn-minus").addEventListener("click", () => {{
        const curDist = camera.position.length();
        flyTo(Math.min(curDist * 1.35, 450), controls.target);
    }});

    document.getElementById("btn-recenter").addEventListener("click", () => {{
        flyTo(REGION_DISTANCE, targetPos);
    }});

    // =========================================================================
    // 8. RENDER LOOP
    // =========================================================================
    function animate() {{
        requestAnimationFrame(animate);

        if (isAnimating) {{
            animProgress += 0.022;
            const t = Math.min(animProgress, 1.0);
            const ease = 1 - Math.pow(1 - t, 3);
            camera.position.lerpVectors(animStartPos, animEndPos, ease);
            controls.target.lerpVectors(animStartTarget, animEndTarget, ease);
            controls.update();
            if (t >= 1.0) {{
                isAnimating = false;
            }}
        }} else {{
            controls.update();
        }}

        renderer.render(scene, camera);
    }}
    animate();

    window.addEventListener("resize", () => {{
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    }});
</script>
</body>
</html>
"""
    return html_content
