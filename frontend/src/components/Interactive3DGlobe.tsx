import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { LocationInfo, SatelliteScene } from '../types';

interface Interactive3DGlobeProps {
  location: LocationInfo;
  selectedScene?: SatelliteScene | null;
  zoomLevel?: number;
  isRotating?: boolean;
  className?: string;
}

export const Interactive3DGlobe: React.FC<Interactive3DGlobeProps> = ({
  location,
  selectedScene,
  zoomLevel = 1.0,
  isRotating = false,
  className = "w-full h-full"
}) => {
  const mountRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const globeGroupRef = useRef<THREE.Group | null>(null);
  const earthMeshRef = useRef<THREE.Mesh | null>(null);
  const markerMeshRef = useRef<THREE.Mesh | null>(null);
  const pulseRingRef = useRef<THREE.Mesh | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // Interaction state
  const isDraggingRef = useRef(false);
  const previousMousePositionRef = useRef({ x: 0, y: 0 });
  const targetRotationRef = useRef({ x: 0, y: 0 });
  const currentRotationRef = useRef({ x: 0, y: 0 });
  const autoRotateRef = useRef(isRotating);

  autoRotateRef.current = isRotating;

  // Convert Lat/Lon to 3D Cartesian coordinates on sphere of radius R
  const latLonToVector3 = (lat: number, lon: number, radius: number): THREE.Vector3 => {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    const x = -(radius * Math.sin(phi) * Math.cos(theta));
    const z = radius * Math.sin(phi) * Math.sin(theta);
    const y = radius * Math.cos(phi);
    return new THREE.Vector3(x, y, z);
  };

  // Align camera / globe to face given latitude and longitude
  const orientToLocation = (lat: number, lon: number) => {
    // To bring (lat, lon) to front facing camera (z > 0):
    const rotY = -(lon + 90) * (Math.PI / 180);
    const rotX = (lat) * (Math.PI / 180);
    targetRotationRef.current = { x: rotX, y: rotY };
  };

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth || 380;
    const height = container.clientHeight || 380;

    // 1. Scene setup
    const scene = new THREE.Scene();
    sceneRef.current = scene;

    // 2. Camera setup
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.z = 5.2 / zoomLevel;
    cameraRef.current = camera;

    // 3. Renderer setup
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    container.innerHTML = '';
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    // 4. Lighting setup
    const ambientLight = new THREE.AmbientLight(0x38bdf8, 0.45);
    scene.add(ambientLight);

    const sunLight = new THREE.DirectionalLight(0xffffff, 1.4);
    sunLight.position.set(5, 3, 5);
    scene.add(sunLight);

    const blueRimLight = new THREE.DirectionalLight(0x0284c7, 1.0);
    blueRimLight.position.set(-5, -2, -3);
    scene.add(blueRimLight);

    // 5. Globe Group
    const globeGroup = new THREE.Group();
    scene.add(globeGroup);
    globeGroupRef.current = globeGroup;

    // 6. Earth Sphere Geometry with Texture
    const radius = 1.95;
    const geometry = new THREE.SphereGeometry(radius, 64, 64);

    const textureLoader = new THREE.TextureLoader();
    const earthTexture = textureLoader.load('/textures/earth.jpg');
    earthTexture.colorSpace = THREE.SRGBColorSpace;

    const material = new THREE.MeshStandardMaterial({
      map: earthTexture,
      roughness: 0.65,
      metalness: 0.15,
      color: 0x93c5fd
    });

    const earthMesh = new THREE.Mesh(geometry, material);
    globeGroup.add(earthMesh);
    earthMeshRef.current = earthMesh;

    // 7. Atmospheric Glow Layer
    const atmosGeometry = new THREE.SphereGeometry(radius * 1.025, 48, 48);
    const atmosMaterial = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.15,
      side: THREE.BackSide
    });
    const atmosMesh = new THREE.Mesh(atmosGeometry, atmosMaterial);
    globeGroup.add(atmosMesh);

    // 8. Location Pin Marker
    const markerPos = latLonToVector3(location.latitude, location.longitude, radius * 1.01);
    const markerGeometry = new THREE.SphereGeometry(0.045, 16, 16);
    const markerMaterial = new THREE.MeshBasicMaterial({
      color: 0x00f0ff
    });
    const markerMesh = new THREE.Mesh(markerGeometry, markerMaterial);
    markerMesh.position.copy(markerPos);
    globeGroup.add(markerMesh);
    markerMeshRef.current = markerMesh;

    // 9. Animated Pulse Beacon Ring
    const ringGeometry = new THREE.RingGeometry(0.05, 0.09, 32);
    const ringMaterial = new THREE.MeshBasicMaterial({
      color: 0x38bdf8,
      transparent: true,
      opacity: 0.8,
      side: THREE.DoubleSide
    });
    const pulseRing = new THREE.Mesh(ringGeometry, ringMaterial);
    pulseRing.position.copy(markerPos);
    pulseRing.lookAt(new THREE.Vector3(0, 0, 0));
    globeGroup.add(pulseRing);
    pulseRingRef.current = pulseRing;

    // Initial orientation to location
    orientToLocation(location.latitude, location.longitude);
    currentRotationRef.current = { ...targetRotationRef.current };
    globeGroup.rotation.x = currentRotationRef.current.x;
    globeGroup.rotation.y = currentRotationRef.current.y;

    // 10. Mouse & Touch drag handling
    const handleMouseDown = (e: MouseEvent) => {
      isDraggingRef.current = true;
      previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const deltaX = e.clientX - previousMousePositionRef.current.x;
      const deltaY = e.clientY - previousMousePositionRef.current.y;

      targetRotationRef.current.y += deltaX * 0.006;
      targetRotationRef.current.x += deltaY * 0.006;
      // Clamp vertical rotation
      targetRotationRef.current.x = Math.max(-Math.PI / 2.2, Math.min(Math.PI / 2.2, targetRotationRef.current.x));

      previousMousePositionRef.current = { x: e.clientX, y: e.clientY };
    };

    const handleMouseUp = () => {
      isDraggingRef.current = false;
    };

    const domElement = renderer.domElement;
    domElement.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);

    // 11. Animation Loop
    let pulseScale = 1.0;
    const animate = () => {
      animFrameRef.current = requestAnimationFrame(animate);

      if (autoRotateRef.current && !isDraggingRef.current) {
        targetRotationRef.current.y += 0.002;
      }

      // Smooth interpolation (slerp-like lerp)
      currentRotationRef.current.x += (targetRotationRef.current.x - currentRotationRef.current.x) * 0.08;
      currentRotationRef.current.y += (targetRotationRef.current.y - currentRotationRef.current.y) * 0.08;

      if (globeGroupRef.current) {
        globeGroupRef.current.rotation.x = currentRotationRef.current.x;
        globeGroupRef.current.rotation.y = currentRotationRef.current.y;
      }

      // Pulse ring animation
      if (pulseRingRef.current) {
        pulseScale += 0.025;
        if (pulseScale > 2.6) pulseScale = 1.0;
        pulseRingRef.current.scale.set(pulseScale, pulseScale, pulseScale);
        (pulseRingRef.current.material as THREE.MeshBasicMaterial).opacity = Math.max(0, 0.9 - (pulseScale - 1.0) / 1.6);
      }

      renderer.render(scene, camera);
    };

    animate();

    // Resize observer
    const handleResize = () => {
      if (!container || !renderer || !camera) return;
      const w = container.clientWidth;
      const h = container.clientHeight;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };

    const resizeObserver = new ResizeObserver(handleResize);
    resizeObserver.observe(container);

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      resizeObserver.disconnect();
      domElement.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      geometry.dispose();
      material.dispose();
      atmosGeometry.dispose();
      atmosMaterial.dispose();
      markerGeometry.dispose();
      markerMaterial.dispose();
      ringGeometry.dispose();
      ringMaterial.dispose();
      renderer.dispose();
    };
  }, []);

  // Sync zoom level
  useEffect(() => {
    if (cameraRef.current) {
      cameraRef.current.position.z = 5.2 / zoomLevel;
      cameraRef.current.updateProjectionMatrix();
    }
  }, [zoomLevel]);

  // Update position and orient when location changes
  useEffect(() => {
    orientToLocation(location.latitude, location.longitude);
    if (markerMeshRef.current && pulseRingRef.current) {
      const radius = 1.95;
      const pos = latLonToVector3(location.latitude, location.longitude, radius * 1.01);
      markerMeshRef.current.position.copy(pos);
      pulseRingRef.current.position.copy(pos);
      pulseRingRef.current.lookAt(new THREE.Vector3(0, 0, 0));
    }
  }, [location]);

  return (
    <div className={`relative ${className} flex items-center justify-center select-none`}>
      <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing flex items-center justify-center" />
      {/* Target Location Overlay Callout */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center space-x-2 bg-[#040816]/90 border border-cyan-400/40 px-3 py-1 rounded-full backdrop-blur-md shadow-2xl pointer-events-none">
        <span className="w-2 h-2 rounded-full bg-[#00f0ff] animate-ping" />
        <span className="text-[11px] font-bold text-white tracking-wide">
          {location.name.split(',')[0]}
        </span>
        <span className="text-[9px] text-cyan-400 font-mono">
          {location.latitude.toFixed(4)}°N, {location.longitude.toFixed(4)}°E
        </span>
      </div>
    </div>
  );
};

