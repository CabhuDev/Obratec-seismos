const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export async function fetchEarthquakes({ period, minMagnitude, maxDepth, signal }) {
  const params = new URLSearchParams({
    period,
    min_magnitude: String(minMagnitude),
  });
  if (maxDepth !== 'all') params.set('max_depth', String(maxDepth));

  const response = await fetch(`${API_BASE_URL}/api/v1/earthquakes?${params}`, { signal });
  if (!response.ok) {
    throw new Error(response.status === 503
      ? 'El IGN no está disponible temporalmente.'
      : 'No hemos podido cargar la actividad sísmica.');
  }
  return response.json();
}
