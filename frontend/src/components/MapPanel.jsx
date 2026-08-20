import { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const SOURCE_ID = 'earthquakes';
const MAP_STYLE = {
  version: 8,
  sources: {
    carto: {
      type: 'raster',
      tiles: ['https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'],
      tileSize: 256,
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO',
    },
  },
  layers: [{ id: 'carto-dark', type: 'raster', source: 'carto' }],
};

function mapColors() {
  const styles = getComputedStyle(document.documentElement);
  return {
    amber: styles.getPropertyValue('--amber').trim(),
    brand: styles.getPropertyValue('--brand').trim(),
    red: styles.getPropertyValue('--red').trim(),
    surface: styles.getPropertyValue('--surface-solid').trim(),
  };
}

function toGeoJson(earthquakes) {
  return {
    type: 'FeatureCollection',
    features: earthquakes.map((item) => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [item.longitude, item.latitude] },
      properties: { ...item },
    })),
  };
}

export default function MapPanel({ earthquakes, selectedId, onSelect, theme }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const earthquakesRef = useRef(earthquakes);
  const onSelectRef = useRef(onSelect);

  useEffect(() => {
    earthquakesRef.current = earthquakes;
    onSelectRef.current = onSelect;
  }, [earthquakes, onSelect]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return undefined;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: [-3.7, 39.7],
      zoom: 5.1,
      minZoom: 3,
      attributionControl: false,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-left');

    map.on('load', () => {
      const colors = mapColors();
      map.addSource(SOURCE_ID, { type: 'geojson', data: toGeoJson(earthquakesRef.current) });
      map.addLayer({
        id: 'earthquake-glow',
        type: 'circle',
        source: SOURCE_ID,
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['get', 'magnitude'], 1, 12, 5, 40],
          'circle-color': colors.brand,
          'circle-opacity': 0.12,
          'circle-blur': 0.7,
        },
      });
      map.addLayer({
        id: 'earthquake-points',
        type: 'circle',
        source: SOURCE_ID,
        paint: {
          'circle-radius': ['interpolate', ['linear'], ['get', 'magnitude'], 1, 5, 5, 15],
          'circle-color': [
            'step', ['get', 'magnitude'], colors.amber, 2.5, colors.brand, 4, colors.red,
          ],
          'circle-stroke-color': colors.surface,
          'circle-stroke-width': 1.5,
          'circle-opacity': 0.92,
        },
      });
      map.on('click', 'earthquake-points', (event) => {
        const feature = event.features?.[0];
        if (feature) onSelectRef.current(feature.properties.id);
      });
      map.on('mouseenter', 'earthquake-points', () => { map.getCanvas().style.cursor = 'pointer'; });
      map.on('mouseleave', 'earthquake-points', () => { map.getCanvas().style.cursor = ''; });
    });

    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const update = () => {
      const source = map.getSource(SOURCE_ID);
      if (source) source.setData(toGeoJson(earthquakes));
    };
    if (map.isStyleLoaded()) update();
    else map.once('load', update);
  }, [earthquakes]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.getLayer('earthquake-points')) return;
    const colors = mapColors();
    map.setPaintProperty('earthquake-glow', 'circle-color', colors.brand);
    map.setPaintProperty('earthquake-points', 'circle-color', [
      'step', ['get', 'magnitude'], colors.amber, 2.5, colors.brand, 4, colors.red,
    ]);
    map.setPaintProperty('earthquake-points', 'circle-stroke-color', colors.surface);
  }, [theme]);

  useEffect(() => {
    const selected = earthquakes.find((item) => item.id === selectedId);
    if (selected && mapRef.current) {
      mapRef.current.flyTo({ center: [selected.longitude, selected.latitude], zoom: 8, duration: 900 });
    }
  }, [selectedId, earthquakes]);

  return <div ref={containerRef} className="map-canvas" aria-label="Mapa de terremotos de España" />;
}
