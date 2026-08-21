const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export async function fetchEarthquakes({ period, minMagnitude, maxDepth, signal }) {
  const params = new URLSearchParams({
    period,
    min_magnitude: String(minMagnitude),
  });
  if (maxDepth !== 'all') params.set('max_depth', String(maxDepth));

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/earthquakes?${params}`, { signal });
  } catch (networkError) {
    // El abort al cambiar de filtro NO es un fallo: App.jsx lo distingue por
    // `name` para no pintar un error. Si se enmascara aqui, cada cambio de
    // periodo mostraria el panel de error.
    if (networkError.name === 'AbortError') throw networkError;
    // Sin respuesta HTTP no hay status que mirar, y el mensaje nativo del
    // navegador ("Failed to fetch") es ingles tecnico en pantalla.
    throw new Error('No se ha podido consultar la actividad sísmica. Comprueba tu conexión y vuelve a intentarlo.');
  }
  if (!response.ok) {
    throw new Error(response.status === 503
      ? 'El servicio de datos del IGN no responde ahora mismo. Vuelve a intentarlo en unos minutos.'
      : 'No se ha podido consultar la actividad sísmica. Comprueba tu conexión y vuelve a intentarlo.');
  }
  return response.json();
}
