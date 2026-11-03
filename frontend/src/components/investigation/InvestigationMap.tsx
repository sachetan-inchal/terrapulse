import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { 
  Layers, MapPin, Radio, ShieldAlert, Info, Flame, Eye, EyeOff, 
  Maximize2, Crosshair, AlertTriangle, Satellite, Calendar, Cloud, ZoomIn
} from 'lucide-react';
import { StationMeasurement, HeatmapData } from '../../types/investigation';
import { SatelliteScene } from '../../types';

interface InvestigationMapProps {
  center: [number, number]; // [lat, lon]
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

  // Layer groups
  const stationsLayerGroupRef = useRef<L.LayerGroup | null>(null);
  const idwLayerGroupRef = useRef<L.GeoJSON | null>(null);
  const activeGeojsonGroupRef = useRef<L.GeoJSON | null>(null);
  const sceneFootprintGroupRef = useRef<L.GeoJSON | null>(null);

  // Layer Visibility Toggles
  const [showStations, setShowStations] = useState(true);
  const [showIDW, setShowIDW] = useState(true);
  const [showFootprint, setShowFootprint] = useState(true);

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    const map = L.map(mapContainerRef.current, {
      center: center,
      zoom: 12,
      zoomControl: false,
      attributionControl: false
    });

    mapInstanceRef.current = map;

    // 1. Esri World Imagery (High-res Dark Satellite)
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19
    }).addTo(map);

    // 2. CartoDB Voyager place labels
    L.tileLayer('https://basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png', {
      maxZoom: 19
    }).addTo(map);

    // Initialize layer group for stations
    stationsLayerGroupRef.current = L.layerGroup().addTo(map);

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Pan to center when center coordinates change
  useEffect(() => {
    if (mapInstanceRef.current && center[0] && center[1]) {
      mapInstanceRef.current.setView(center, mapInstanceRef.current.getZoom(), { animate: true });
    }
  }, [center]);

  // Render Stations Layer
  useEffect(() => {
    const map = mapInstanceRef.current;
    const group = stationsLayerGroupRef.current;
    if (!map || !group) return;

    group.clearLayers();
    if (!showStations) return;

    stations.forEach((st) => {
      let markerColor = '#10b981'; // green
      if (st.indicator === 'PM2.5') {
        if (st.value > 120) markerColor = '#ef4444'; // hazardous
        else if (st.value > 60) markerColor = '#f59e0b'; // moderate/poor
        else markerColor = '#10b981'; // good
      } else if (st.indicator === 'DO') {
        if (st.value < 2.0) markerColor = '#ef4444'; // critical hypoxia
        else if (st.value < 4.0) markerColor = '#f59e0b'; // stressed
        else markerColor = '#06b6d4'; // healthy
      }

      const isSelected = selectedStation?.station_id === st.station_id;

      const marker = L.circleMarker([st.latitude, st.longitude], {
        radius: isSelected ? 9 : 6,
        color: isSelected ? '#ffffff' : '#040816',
        weight: isSelected ? 3 : 1.5,
        fillColor: markerColor,
        fillOpacity: 0.9
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

  // Render IDW Heatmap Surface
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

  // Render Active GeoJSON (Hotspots / Polygons from Agent)
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

  // Render Satellite Scene Footprint
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
          dashArray: '4, 4',
          weight: 1.5,
          fillColor: '#0891b2',
          fillOpacity: 0.08
        }
      }).addTo(map);
      sceneFootprintGroupRef.current = layer;
    }
  }, [selectedScene, showFootprint]);

  const handleZoomReset = () => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.setView(center, 12, { animate: true });
    }
  };

  return (
    <div className="relative w-full h-full bg-[#030612] overflow-hidden select-none">
      {/* Leaflet Map Stage */}
      <div ref={mapContainerRef} className="w-full h-full z-0" />

      {/* Top Left: Study Area Indicator Pill */}
      <div className="absolute top-3 left-3 z-10 flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#050b1a]/90 border border-cyan-500/30 text-white font-mono text-xs backdrop-blur-md shadow-lg">
        <MapPin className="w-3.5 h-3.5 text-cyan-400" />
        <span className="font-semibold text-slate-200 truncate max-w-xs">{locationName}</span>
        <span className="text-[10px] text-cyan-400/80">
          [{center[0].toFixed(4)}°N, {center[1].toFixed(4)}°E]
        </span>
      </div>

      {/* Top Right: Layer Switcher Floating Controls */}
      <div className="absolute top-3 right-3 z-10 flex flex-col gap-1.5 p-2 rounded-xl bg-[#050b1a]/90 border border-cyan-500/25 backdrop-blur-md shadow-xl text-xs font-mono text-slate-300">
        <div className="text-[10px] uppercase font-bold text-slate-400 px-1 flex items-center gap-1.5">
          <Layers className="w-3 h-3 text-cyan-400" />
          <span>Spatial Layers</span>
        </div>

        <button
          onClick={() => setShowStations(!showStations)}
          className={`flex items-center justify-between px-2 py-1 rounded-md text-[11px] transition-colors ${
            showStations ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>Ground Stations ({stations.length})</span>
          </div>
          {showStations ? <Eye className="w-3 h-3 text-cyan-400" /> : <EyeOff className="w-3 h-3 text-slate-500" />}
        </button>

        <button
          onClick={() => setShowIDW(!showIDW)}
          className={`flex items-center justify-between px-2 py-1 rounded-md text-[11px] transition-colors ${
            showIDW ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
            <span>IDW Heatmap Surface</span>
          </div>
          {showIDW ? <Eye className="w-3 h-3 text-cyan-400" /> : <EyeOff className="w-3 h-3 text-slate-500" />}
        </button>

        <button
          onClick={() => setShowFootprint(!showFootprint)}
          className={`flex items-center justify-between px-2 py-1 rounded-md text-[11px] transition-colors ${
            showFootprint ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-500 hover:text-slate-300'
          }`}
        >
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-blue-400"></span>
            <span>Satellite Footprint</span>
          </div>
          {showFootprint ? <Eye className="w-3 h-3 text-cyan-400" /> : <EyeOff className="w-3 h-3 text-slate-500" />}
        </button>

        <button
          onClick={handleZoomReset}
          className="mt-1 flex items-center justify-center gap-1 px-2 py-1 rounded-md bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-[10px] transition-colors"
        >
          <Crosshair className="w-3 h-3 text-cyan-400" />
          <span>Recenter Study Area</span>
        </button>
      </div>

      {/* Ground Station Zero Availability Warning */}
      {stations.length === 0 && (
        <div className="absolute top-14 left-3 z-10 px-3 py-2 rounded-xl bg-amber-500/15 border border-amber-500/40 backdrop-blur-md shadow-lg max-w-sm text-xs font-mono text-amber-300 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold text-amber-200">No Ground Sensors in AOI</div>
            <div className="text-[10px] text-amber-300/80">
              Ground telemetry stations are unavailable for this immediate boundary. Satellite optical observations & spatial indices remain active.
            </div>
          </div>
        </div>
      )}

      {/* Planetary Computer Satellite Scene Card */}
      {selectedScene && (
        <div className="absolute top-[180px] right-3 z-10 p-3 rounded-xl bg-[#061026]/90 border border-cyan-500/30 backdrop-blur-md shadow-xl max-w-xs text-xs font-mono space-y-2">
          <div className="flex items-center justify-between border-b border-cyan-500/20 pb-1">
            <div className="flex items-center gap-1.5 text-cyan-300 font-bold">
              <Satellite className="w-3.5 h-3.5 text-cyan-400" />
              <span>Planetary Optical Scene</span>
            </div>
            <span className="text-[9px] px-1.5 py-0.2 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              {selectedScene.mission}
            </span>
          </div>

          {scenes.length > 1 && onSelectScene && (
            <select
              value={selectedScene.id}
              onChange={(e) => {
                const found = scenes.find((s) => s.id === e.target.value);
                if (found) onSelectScene(found);
              }}
              className="w-full bg-[#030612] border border-cyan-500/30 rounded px-2 py-1 text-[10px] text-cyan-300 focus:outline-none"
            >
              {scenes.map((sc) => (
                <option key={sc.id} value={sc.id}>
                  {sc.mission} ({sc.year}) - {sc.acquisition_date.split('T')[0]}
                </option>
              ))}
            </select>
          )}

          <div className="grid grid-cols-2 gap-2 text-[10px]">
            <div>
              <span className="text-slate-400">Sensor:</span>
              <div className="text-slate-200 font-semibold">{selectedScene.sensor}</div>
            </div>
            <div>
              <span className="text-slate-400">Acquisition:</span>
              <div className="text-slate-200 font-semibold">{selectedScene.acquisition_date.split('T')[0]}</div>
            </div>
            <div>
              <span className="text-slate-400">Cloud Cover:</span>
              <div className="text-slate-200 font-semibold">{selectedScene.cloud_cover.toFixed(1)}%</div>
            </div>
            <div>
              <span className="text-slate-400">Resolution:</span>
              <div className="text-slate-200 font-semibold">{selectedScene.spatial_resolution_m}m GSD</div>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Left: Epistemic Notice & Data Distinctions Legend */}
      <div className="absolute bottom-3 left-3 z-10 p-2.5 rounded-xl bg-[#050b1a]/90 border border-cyan-500/20 backdrop-blur-md shadow-xl max-w-sm text-[11px] font-mono space-y-1">
        <div className="flex items-center gap-1.5 text-slate-400 text-[10px] font-bold uppercase">
          <Info className="w-3 h-3 text-cyan-400" />
          <span>Epistemic Data Integrity</span>
        </div>
        <div className="flex items-center gap-3 text-[10px]">
          <div className="flex items-center gap-1 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>Direct Sensor</span>
          </div>
          <div className="flex items-center gap-1 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
            <span>IDW Model</span>
          </div>
          <div className="flex items-center gap-1 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-rose-500"></span>
            <span>Hotspot</span>
          </div>
        </div>
        {heatmapData && (
          <p className="text-[10px] text-cyan-300/80 leading-tight pt-0.5">
            Coverage: <strong>{heatmapData.coverage_percentage}%</strong> of study area within 10km radius.
          </p>
        )}
      </div>

      {/* Bottom Right: Station Inspector Card (when selected) */}
      {selectedStation && (
        <div className="absolute bottom-3 right-3 z-10 p-3.5 rounded-xl bg-[#050e24]/95 border border-cyan-400/40 backdrop-blur-xl shadow-2xl max-w-xs text-xs font-mono space-y-2">
          <div className="flex items-start justify-between gap-2 border-b border-cyan-500/20 pb-1.5">
            <div>
              <div className="font-bold text-white text-xs">{selectedStation.station_name}</div>
              <div className="text-[10px] text-cyan-400">{selectedStation.station_id}</div>
            </div>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              {selectedStation.quality_flag}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div>
              <span className="text-slate-500 text-[10px]">MEASUREMENT</span>
              <div className="text-cyan-300 font-bold text-sm">
                {selectedStation.value} <span className="text-[10px] text-slate-400">{selectedStation.unit}</span>
              </div>
            </div>
            <div>
              <span className="text-slate-500 text-[10px]">POLLUTANT</span>
              <div className="text-slate-200 font-semibold">{selectedStation.indicator}</div>
            </div>
          </div>

          <div className="text-[10px] text-slate-400 space-y-0.5 pt-1 border-t border-slate-800">
            <div>Timestamp: {selectedStation.timestamp}</div>
            <div>Agency: {selectedStation.provenance}</div>
          </div>

          {selectedStation.is_sample_data && (
            <div className="text-[9px] text-amber-300/90 bg-amber-500/10 p-1.5 rounded border border-amber-500/30 flex items-start gap-1">
              <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0 mt-0.5" />
              <span>{selectedStation.sample_data_note || "Sample benchmark data for demonstration."}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
