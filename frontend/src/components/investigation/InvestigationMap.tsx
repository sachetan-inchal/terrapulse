import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { 
  Layers, MapPin, Info, Flame, Eye, EyeOff, 
  Crosshair, AlertTriangle, Satellite, ChevronDown,
  Plus, Minus, Compass, Map as MapIcon, Globe
} from 'lucide-react';
import { StationMeasurement, HeatmapData } from '../../types/investigation';
import { SatelliteScene } from '../../types';

export type BasemapMode = 'labeled' | 'standard' | 'satellite' | 'terrain';

interface InvestigationMapProps {
  center: [number, number]; // [lat, lon]
  zoom?: number;
  stations: StationMeasurement[];
  heatmapData: HeatmapData | null;
  activeGeojson?: any;
  onSelectStation?: (station: StationMeasurement) => void;
  selectedStation?: StationMeasurement | null;
  locationName: string;
  scenes?: SatelliteScene[];
  selectedScene?: SatelliteScene | null;
  onSelectScene?: (scene: SatelliteScene) => void;
}

export const InvestigationMap: React.FC<InvestigationMapProps> = ({
  center,
  zoom,
  stations,
  heatmapData,
  activeGeojson,
  onSelectStation,
  selectedStation,
  locationName,
  scenes = [],
  selectedScene,
  onSelectScene
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  // Basemap Switcher State (Priority 6)
  const [basemapMode, setBasemapMode] = useState<BasemapMode>('labeled');
  const baseTilesRef = useRef<L.LayerGroup | null>(null);

  // Coordinates hover HUD
  const [cursorCoords, setCursorCoords] = useState<{ lat: number; lng: number } | null>(null);

  // Layer groups
  const stationsLayerGroupRef = useRef<L.LayerGroup | null>(null);
  const idwLayerGroupRef = useRef<L.GeoJSON | null>(null);
  const activeGeojsonGroupRef = useRef<L.GeoJSON | null>(null);
  const sceneFootprintGroupRef = useRef<L.GeoJSON | null>(null);

  // Layer Visibility Toggles
  const [showStations, setShowStations] = useState(true);
  const [showIDW, setShowIDW] = useState(true);
  const [showFootprint, setShowFootprint] = useState(true);
  const [showLayerMenu, setShowLayerMenu] = useState(false);

  // 1. Initialize Leaflet Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const map = L.map(mapContainerRef.current, {
      center: center,
      zoom: zoom !== undefined ? zoom : 2,
      zoomControl: false,
      attributionControl: false
    });

    mapInstanceRef.current = map;

    // Scale Bar Control
    L.control.scale({ imperial: false, position: 'bottomleft' }).addTo(map);

    // Mouse Coordinates Tracker
    map.on('mousemove', (e) => {
      setCursorCoords({ lat: e.latlng.lat, lng: e.latlng.lng });
    });

    // Layer group for basemap tiles
    baseTilesRef.current = L.layerGroup().addTo(map);

    // Layer group for stations
    stationsLayerGroupRef.current = L.layerGroup().addTo(map);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // 2. Basemap Switcher Effect (Priority 6: Labeled Satellite, Standard Map, Pure Satellite, Terrain)
  useEffect(() => {
    const map = mapInstanceRef.current;
    const group = baseTilesRef.current;
    if (!map || !group) return;

    group.clearLayers();

    if (basemapMode === 'labeled') {
      // High-res Esri Imagery + CartoDB Voyager place labels (Country, State, City, District)
      const esri = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19
      });
      const labels = L.tileLayer('https://basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        zIndex: 5
      });
      group.addLayer(esri);
      group.addLayer(labels);
    } else if (basemapMode === 'standard') {
      // Standard Worldwide Geographical OpenStreetMap (High contrast political boundaries, water, roads)
      const osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
      });
      group.addLayer(osm);
    } else if (basemapMode === 'satellite') {
      // Pure Satellite Imagery without textual labels
      const esri = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19
      });
      group.addLayer(esri);
    } else if (basemapMode === 'terrain') {
      // Esri World Topo Map (Topography, contours, mountain peaks, rivers, hydrology)
      const topo = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 19
      });
      group.addLayer(topo);
    }
  }, [basemapMode]);

  // 3. Pan to center when center coordinates or zoom change
  useEffect(() => {
    if (mapInstanceRef.current && center[0] !== undefined && center[1] !== undefined) {
      const targetZoom = zoom !== undefined ? zoom : mapInstanceRef.current.getZoom();
      mapInstanceRef.current.setView(center, targetZoom, { animate: true });
    }
  }, [center, zoom]);

  // 4. Render Telemetry Stations Layer with Informative Tooltips
  useEffect(() => {
    const map = mapInstanceRef.current;
    const group = stationsLayerGroupRef.current;
    if (!map || !group) return;

    group.clearLayers();
    if (!showStations) return;

    stations.forEach((st) => {
      let markerColor = '#10b981'; // Green (Good / Healthy)
      if (st.indicator === 'PM2.5') {
        if (st.value > 120) markerColor = '#ef4444'; // Unhealthy / Severe
        else if (st.value > 60) markerColor = '#f59e0b'; // Moderate / Stressed
        else markerColor = '#10b981';
      } else if (st.indicator === 'DO') {
        if (st.value < 2.0) markerColor = '#ef4444'; // Critical Hypoxia
        else if (st.value < 4.0) markerColor = '#f59e0b'; // Biological Stress
        else markerColor = '#06b6d4';
      }

      const isSelected = selectedStation?.station_id === st.station_id;

      const marker = L.circleMarker([st.latitude, st.longitude], {
        radius: isSelected ? 9 : 6,
        color: isSelected ? '#ffffff' : '#040816',
        weight: isSelected ? 3 : 1.5,
        fillColor: markerColor,
        fillOpacity: 0.95
      });

      marker.bindTooltip(
        `<div style="font-family: monospace; font-size: 11px; padding: 2px;">
          <strong>${st.station_name}</strong><br/>
          ${st.indicator}: <span style="color:${markerColor}; font-weight:bold;">${st.value} ${st.unit}</span><br/>
          <span style="font-size:9px; color:#888;">${st.provenance}</span>
        </div>`,
        { direction: 'top', offset: [0, -6], className: 'custom-leaflet-tooltip' }
      );

      marker.on('click', () => {
        if (onSelectStation) {
          onSelectStation(st);
        }
      });

      group.addLayer(marker);
    });
  }, [stations, showStations, selectedStation]);

  // 5. Render IDW Heatmap Surface (Geographically Bound to AOI)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (idwLayerGroupRef.current) {
      map.removeLayer(idwLayerGroupRef.current);
      idwLayerGroupRef.current = null;
    }

    if (!showIDW || !heatmapData || !heatmapData.geojson) return;

    const layer = L.geoJSON(heatmapData.geojson, {
      style: (feature) => {
        const val = feature?.properties?.value || feature?.properties?.val || 50;
        let fillColor = '#10b981';
        if (val > 120) fillColor = '#ef4444';
        else if (val > 80) fillColor = '#f97316';
        else if (val > 50) fillColor = '#eab308';
        else if (val > 30) fillColor = '#06b6d4';

        return {
          color: fillColor,
          weight: 0.8,
          opacity: 0.6,
          fillColor: fillColor,
          fillOpacity: 0.35
        };
      }
    }).addTo(map);

    idwLayerGroupRef.current = layer;
  }, [heatmapData, showIDW]);

  // 6. Render Active GeoJSON (Hotspots / Polygons from Agent)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (activeGeojsonGroupRef.current) {
      map.removeLayer(activeGeojsonGroupRef.current);
      activeGeojsonGroupRef.current = null;
    }

    if (!activeGeojson) return;

    const layer = L.geoJSON(activeGeojson, {
      pointToLayer: (feature, latlng) => {
        const isHotspot = feature.properties?.data_type === 'HOTSPOT';
        const color = isHotspot ? '#f43f5e' : '#38bdf8';
        return L.circleMarker(latlng, {
          radius: isHotspot ? 10 : 7,
          color: '#ffffff',
          weight: 2,
          fillColor: color,
          fillOpacity: 0.95
        });
      },
      style: (feature) => {
        if (feature?.properties?.data_type === 'INTERPOLATED_MODEL') {
          return {
            color: '#06b6d4',
            weight: 0.5,
            fillColor: '#06b6d4',
            fillOpacity: 0.35
          };
        }
        return {
          color: '#38bdf8',
          weight: 2,
          fillOpacity: 0.2
        };
      }
    }).addTo(map);

    activeGeojsonGroupRef.current = layer;
  }, [activeGeojson]);

  // 7. Render Satellite Scene Footprint
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (sceneFootprintGroupRef.current) {
      map.removeLayer(sceneFootprintGroupRef.current);
      sceneFootprintGroupRef.current = null;
    }

    if (!showFootprint || !selectedScene) return;

    let footprintGeojson: any = null;
    if (selectedScene.footprint) {
      footprintGeojson = selectedScene.footprint;
    } else if (selectedScene.bbox) {
      const [minLon, minLat, maxLon, maxLat] = selectedScene.bbox;
      footprintGeojson = {
        type: 'Feature',
        properties: { name: selectedScene.id },
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [minLon, minLat],
            [maxLon, minLat],
            [maxLon, maxLat],
            [minLon, maxLat],
            [minLon, minLat]
          ]]
        }
      };
    }

    if (footprintGeojson) {
      const layer = L.geoJSON(footprintGeojson, {
        style: {
          color: '#06b6d4',
          weight: 1.5,
          dashArray: '4, 4',
          fillColor: '#06b6d4',
          fillOpacity: 0.08
        }
      }).addTo(map);

      sceneFootprintGroupRef.current = layer;
    }
  }, [selectedScene, showFootprint]);

  // Zoom handlers
  const handleZoomIn = () => mapInstanceRef.current?.zoomIn();
  const handleZoomOut = () => mapInstanceRef.current?.zoomOut();
  const handleZoomReset = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView(center, zoom !== undefined ? zoom : 12, { animate: true });
    }
  };

  const isGlobalOverview = !locationName || locationName === 'Global Overview' || locationName.includes('No Location Selected');

  return (
    <div className="relative w-full h-full bg-[#030612] overflow-hidden select-none font-sans">
      {/* Leaflet Map Div */}
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Top Left: Selected Location HUD Badge */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-2">
        <div className="px-3 py-1.5 rounded-lg bg-[#040816]/90 border border-cyan-500/30 backdrop-blur-xl shadow-xl flex items-center gap-2 text-xs font-mono">
          <MapPin className={`w-3.5 h-3.5 ${!isGlobalOverview ? 'text-cyan-400 animate-pulse' : 'text-slate-500'}`} />
          <span className="font-semibold text-white">
            {!isGlobalOverview ? locationName : 'Global Standby (Awaiting AOI)'}
          </span>
          {!isGlobalOverview && center[0] !== 20.0 && (
            <span className="text-[10px] text-cyan-400/80 pl-1 border-l border-cyan-500/30">
              {center[0].toFixed(4)}°N, {center[1].toFixed(4)}°E
            </span>
          )}
        </div>
      </div>

      {/* Top Right: Basemap Mode Switcher & Layer Menu */}
      <div className="absolute top-3 right-3 z-10 flex items-center gap-2">
        {/* Basemap Switcher Pills (Priority 6) */}
        <div className="flex items-center bg-[#070e24]/95 p-1 rounded-xl border border-cyan-500/30 backdrop-blur-xl shadow-xl font-mono text-[10px]">
          <button
            onClick={() => setBasemapMode('labeled')}
            className={`px-2 py-1 rounded-lg transition-all flex items-center gap-1 ${
              basemapMode === 'labeled'
                ? 'bg-cyan-500/25 text-cyan-200 border border-cyan-400/50 font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
            title="Satellite Imagery with high-contrast Country, State, City, and District labels"
          >
            <Globe className="w-3 h-3 text-cyan-400" />
            <span>Labeled Sat</span>
          </button>
          <button
            onClick={() => setBasemapMode('standard')}
            className={`px-2 py-1 rounded-lg transition-all flex items-center gap-1 ${
              basemapMode === 'standard'
                ? 'bg-cyan-500/25 text-cyan-200 border border-cyan-400/50 font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
            title="OpenStreetMap Standard (High contrast political boundaries, rivers, roads, and cities)"
          >
            <MapIcon className="w-3 h-3 text-cyan-400" />
            <span>Standard</span>
          </button>
          <button
            onClick={() => setBasemapMode('satellite')}
            className={`px-2 py-1 rounded-lg transition-all flex items-center gap-1 ${
              basemapMode === 'satellite'
                ? 'bg-cyan-500/25 text-cyan-200 border border-cyan-400/50 font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
            title="Pure Satellite Imagery without text labels"
          >
            <Satellite className="w-3 h-3 text-cyan-400" />
            <span>Satellite</span>
          </button>
          <button
            onClick={() => setBasemapMode('terrain')}
            className={`px-2 py-1 rounded-lg transition-all flex items-center gap-1 ${
              basemapMode === 'terrain'
                ? 'bg-cyan-500/25 text-cyan-200 border border-cyan-400/50 font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
            title="Esri World Topographic Terrain with contours, mountain peaks, and elevation"
          >
            <Compass className="w-3 h-3 text-cyan-400" />
            <span>Terrain</span>
          </button>
        </div>

        {/* Layer Visibility Toggle Button */}
        <button
          onClick={() => setShowLayerMenu(!showLayerMenu)}
          className={`p-1.5 rounded-xl border backdrop-blur-xl shadow-xl transition-all ${
            showLayerMenu
              ? 'bg-cyan-500/20 text-cyan-300 border-cyan-400/60'
              : 'bg-[#070e24]/95 text-slate-300 border-cyan-500/30 hover:text-white'
          }`}
          title="Toggle Environmental Layers"
        >
          <Layers className="w-4 h-4" />
        </button>
      </div>

      {/* Layer Visibility Popover Menu */}
      {showLayerMenu && (
        <div className="absolute top-14 right-3 z-10 p-3 rounded-xl bg-[#070e24]/95 border border-cyan-500/35 backdrop-blur-2xl shadow-2xl w-56 text-xs font-mono space-y-2">
          <div className="font-bold text-cyan-400 uppercase text-[10px] pb-1 border-b border-cyan-500/20 flex items-center justify-between">
            <span>Layer Controls</span>
            <Layers className="w-3 h-3" />
          </div>

          <label className="flex items-center justify-between cursor-pointer py-0.5">
            <span className="text-slate-300">Ground Stations</span>
            <input
              type="checkbox"
              checked={showStations}
              onChange={(e) => setShowStations(e.target.checked)}
              className="accent-cyan-400"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer py-0.5">
            <span className="text-slate-300">IDW Heatmap Surface</span>
            <input
              type="checkbox"
              checked={showIDW}
              onChange={(e) => setShowIDW(e.target.checked)}
              className="accent-cyan-400"
            />
          </label>

          <label className="flex items-center justify-between cursor-pointer py-0.5">
            <span className="text-slate-300">Satellite AOI Footprint</span>
            <input
              type="checkbox"
              checked={showFootprint}
              onChange={(e) => setShowFootprint(e.target.checked)}
              className="accent-cyan-400"
            />
          </label>

          <button
            onClick={handleZoomReset}
            className="w-full mt-2 flex items-center justify-center gap-1.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[10px] font-bold transition-colors"
          >
            <Crosshair className="w-3 h-3 text-cyan-400" />
            <span>Recenter to Target</span>
          </button>
        </div>
      )}

      {/* Zoom and Recenter Controls (Floating Vertical Bar) */}
      <div className="absolute bottom-12 right-3 z-10 flex flex-col gap-1 bg-[#070e24]/90 p-1 rounded-xl border border-cyan-500/25 backdrop-blur-xl shadow-xl">
        <button
          onClick={handleZoomIn}
          className="p-1.5 rounded-lg hover:bg-cyan-950/40 text-slate-300 hover:text-cyan-300 transition-colors"
          title="Zoom In"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={handleZoomOut}
          className="p-1.5 rounded-lg hover:bg-cyan-950/40 text-slate-300 hover:text-cyan-300 transition-colors"
          title="Zoom Out"
        >
          <Minus className="w-3.5 h-3.5" />
        </button>
        <div className="h-px bg-slate-800 my-0.5" />
        <button
          onClick={handleZoomReset}
          className="p-1.5 rounded-lg hover:bg-cyan-950/40 text-slate-300 hover:text-cyan-300 transition-colors"
          title="Recenter"
        >
          <Crosshair className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Wilderness Station Unavailable Notice (Only when an active location has 0 stations) */}
      {!isGlobalOverview && stations.length === 0 && (
        <div className="absolute top-14 left-3 z-10 px-3 py-2 rounded-xl bg-amber-500/15 border border-amber-500/40 backdrop-blur-md shadow-lg max-w-sm text-xs font-mono text-amber-300 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-amber-200">No Continuous Sensors in AOI</div>
            <div className="text-[10px] text-amber-300/80">
              Ground telemetry stations are unavailable for this immediate boundary. Supported via Copernicus Sentinel-2 MSI satellite reflectance.
            </div>
          </div>
        </div>
      )}

      {/* Bottom Left: Comprehensive Legend (Priority 7) */}
      <div className="absolute bottom-3 left-3 z-10 p-2.5 rounded-xl bg-[#050b1a]/95 border border-cyan-500/25 backdrop-blur-xl shadow-2xl max-w-xs text-[10px] font-mono space-y-1.5">
        <div className="flex items-center gap-1.5 text-cyan-400 font-bold uppercase text-[9px]">
          <Info className="w-3 h-3 text-cyan-400" />
          <span>Geospatial Legend & Layers</span>
        </div>
        <div className="grid grid-cols-2 gap-x-2 gap-y-1 text-slate-300">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 shrink-0"></span>
            <span>Station (Good)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 shrink-0"></span>
            <span>Station (Severe)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-sm bg-cyan-500/40 border border-cyan-400 shrink-0"></span>
            <span>IDW Surface</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-fuchsia-500 shrink-0 ring-1 ring-white"></span>
            <span>Hotspot ($Gi^*$)</span>
          </div>
        </div>
      </div>

      {/* Bottom Right: Cursor Coordinates HUD */}
      {cursorCoords && (
        <div className="absolute bottom-3 right-16 z-10 px-2 py-1 rounded-md bg-[#050b1a]/90 border border-cyan-500/20 text-[9px] font-mono text-cyan-300 backdrop-blur-md">
          {cursorCoords.lat.toFixed(4)}°N, {cursorCoords.lng.toFixed(4)}°E
        </div>
      )}

      {/* Station Inspector Flyout Card (when user clicks a marker) */}
      {selectedStation && (
        <div className="absolute bottom-12 left-3 z-20 p-3 rounded-xl bg-[#050e24]/95 border border-cyan-400/40 backdrop-blur-xl shadow-2xl max-w-xs text-xs font-mono space-y-1.5">
          <div className="flex items-start justify-between gap-2 border-b border-cyan-500/20 pb-1">
            <div>
              <div className="font-bold text-white text-xs">{selectedStation.station_name}</div>
              <div className="text-[10px] text-cyan-400">{selectedStation.station_id}</div>
            </div>
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              {selectedStation.quality_flag}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[10px]">
            <div>
              <span className="text-slate-500 text-[9px]">MEASUREMENT</span>
              <div className="text-cyan-300 font-bold text-sm">
                {selectedStation.value} <span className="text-[9px] text-slate-400">{selectedStation.unit}</span>
              </div>
            </div>
            <div>
              <span className="text-slate-500 text-[9px]">INDICATOR</span>
              <div className="text-slate-200 font-semibold">{selectedStation.indicator}</div>
            </div>
          </div>

          <div className="text-[9px] text-slate-400 space-y-0.5 pt-1 border-t border-slate-800">
            <div>Timestamp: {selectedStation.timestamp}</div>
            <div>Agency: {selectedStation.provenance}</div>
          </div>
        </div>
      )}
    </div>
  );
};
