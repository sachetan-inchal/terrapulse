import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import { LocationInfo, SatelliteScene } from '../types';

interface InteractiveSatelliteMapProps {
  location: LocationInfo;
  selectedScene: SatelliteScene | null;
  overlayUrl: string;
  overlayBounds: [[number, number], [number, number]];
}

export const InteractiveSatelliteMap: React.FC<InteractiveSatelliteMapProps> = ({
  location,
  selectedScene,
  overlayUrl,
  overlayBounds
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const overlayLayerRef = useRef<L.ImageOverlay | null>(null);
  const aoiRectRef = useRef<L.Rectangle | null>(null);
  const footprintLayerRef = useRef<L.GeoJSON | null>(null);
  const markerRef = useRef<L.Marker | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Destroy existing instance if container re-mounts
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const lat = location.latitude;
    const lon = location.longitude;

    // Initialize Leaflet map with dark satellite base tiles
    const map = L.map(mapContainerRef.current, {
      center: [lat, lon],
      zoom: 11,
      zoomControl: false,
      attributionControl: false
    });

    mapInstanceRef.current = map;

    // 1. Esri High-Resolution World Imagery
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19
    }).addTo(map);

    // 2. Clear place labels overlay
    L.tileLayer('https://basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png', {
      maxZoom: 19
    }).addTo(map);

    // 3. Georeferenced Satellite Image Overlay (Real Sentinel-2 Window)
    if (overlayUrl) {
      const overlay = L.imageOverlay(overlayUrl, overlayBounds, {
        opacity: 0.90,
        interactive: false
      }).addTo(map);
      overlayLayerRef.current = overlay;
    }

    // 4. Cyan AOI Bounding Box
    const aoiRect = L.rectangle(overlayBounds, {
      color: '#38bdf8',
      weight: 2,
      fillColor: '#0284c7',
      fillOpacity: 0.12,
      dashArray: '5, 5'
    }).addTo(map);
    aoiRectRef.current = aoiRect;

    // 5. Actual Satellite Footprint Polygon (GeoJSON from STAC item)
    if (selectedScene?.footprint) {
      const footprint = L.geoJSON(selectedScene.footprint, {
        style: {
          color: '#f59e0b',
          weight: 2,
          fillColor: '#f59e0b',
          fillOpacity: 0.08,
          dashArray: '6, 4'
        }
      }).addTo(map);
      footprintLayerRef.current = footprint;
    }

    // 6. Center Coordinate Pin Marker
    const icon = L.divIcon({
      className: 'custom-pin-marker',
      html: `
        <div style="position: relative; display: flex; align-items: center; justify-content: center;">
          <div style="position: absolute; width: 22px; height: 22px; border-radius: 50%; background: rgba(56, 189, 248, 0.4); animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
          <div style="width: 10px; height: 10px; border-radius: 50%; background: #38bdf8; border: 2px solid #ffffff; box-shadow: 0 0 10px #38bdf8;"></div>
        </div>
      `,
      iconSize: [22, 22],
      iconAnchor: [11, 11]
    });

    const marker = L.marker([lat, lon], { icon }).addTo(map);
    markerRef.current = marker;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update map center, overlay, footprint and bounds when location or scene changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    const lat = location.latitude;
    const lon = location.longitude;

    map.flyTo([lat, lon], 11, { duration: 1.2 });

    // Update AOI rectangle
    if (aoiRectRef.current) {
      aoiRectRef.current.setBounds(overlayBounds);
    }

    // Update Marker
    if (markerRef.current) {
      markerRef.current.setLatLng([lat, lon]);
    }

    // Update Image Overlay
    if (overlayLayerRef.current) {
      overlayLayerRef.current.remove();
      overlayLayerRef.current = null;
    }

    if (overlayUrl) {
      const overlay = L.imageOverlay(overlayUrl, overlayBounds, {
        opacity: 0.90,
        interactive: false
      }).addTo(map);
      overlayLayerRef.current = overlay;
    }

    // Update Footprint
    if (footprintLayerRef.current) {
      footprintLayerRef.current.remove();
      footprintLayerRef.current = null;
    }

    if (selectedScene?.footprint) {
      const footprint = L.geoJSON(selectedScene.footprint, {
        style: {
          color: '#f59e0b',
          weight: 2,
          fillColor: '#f59e0b',
          fillOpacity: 0.08,
          dashArray: '6, 4'
        }
      }).addTo(map);
      footprintLayerRef.current = footprint;
    }
  }, [location, selectedScene, overlayUrl, overlayBounds]);

  return (
    <div className="w-full h-full relative overflow-hidden bg-slate-950">
      {/* Leaflet DOM container */}
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Real Legend Badge */}
      <div className="absolute bottom-2 left-2 z-10 flex items-center space-x-2 bg-[#090e1a]/90 border border-slate-800/80 px-2 py-1 rounded text-[9px] font-mono backdrop-blur-md">
        <span className="flex items-center gap-1 text-[#38bdf8]">
          <span className="inline-block w-2.5 h-1 border border-[#38bdf8] bg-[#0284c7]/30 border-dashed" />
          AOI
        </span>
        {selectedScene?.footprint && (
          <span className="flex items-center gap-1 text-[#f59e0b]">
            <span className="inline-block w-2.5 h-1 border border-[#f59e0b] bg-[#f59e0b]/30 border-dashed" />
            Footprint
          </span>
        )}
      </div>

      {/* Basemap Attribution badge */}
      <div className="absolute bottom-2 right-2 z-10 px-1.5 py-0.5 rounded bg-black/70 text-[8px] text-slate-400 font-mono pointer-events-none">
        Esri • Microsoft PC • Sentinel-2
      </div>
    </div>
  );
};
