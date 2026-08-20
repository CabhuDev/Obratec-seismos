# Arquitectura

## Principios

1. **El frontend no depende del formato interno del IGN.** Solo consume la API propia.
2. **El feed es casi en tiempo real.** Se consulta bajo demanda y se reutiliza durante 120 segundos; la respuesta HTTP sí se lee por streaming con un límite duro antes de analizarla.
3. **Degradación controlada.** Si el IGN falla y existe una instantánea previa, se devuelve marcándola como `stale`.
4. **Sin base de datos en el MVP.** El catálogo de 3/10/30 días cabe en memoria; la persistencia se añadirá cuando sean necesarios históricos propios o alertas.
5. **Atribución visible.** La procedencia y la condición provisional acompañan a los datos.

## Componentes

### `backend/app/services/ign_parser.py`

Extrae de `terremotos.js` las variables `dias3`, `dias10` o `dias30`, valida el GeoJSON y normaliza cada evento. No ejecuta JavaScript ni utiliza `eval`.

### `backend/app/services/earthquakes.py`

Gestiona la relación periodo/colección y una caché independiente por periodo. Cada periodo tiene un bloqueo asíncrono y una ventana de reintento tras fallos: una recarga usa el feed y las peticiones concurrentes o posteriores reciben inmediatamente la misma instantánea obsoleta hasta el siguiente intento. Si aún no existe caché, las peticiones durante esa ventana devuelven HTTP 503 sin volver a consultar el feed. Admite inyección del cliente HTTP y del reloj para pruebas deterministas.

### `backend/app/main.py`

Expone FastAPI, aplica filtros y traduce los fallos explícitos de descarga o parseo sin caché a HTTP 503. El cliente no sigue redirecciones, limita la respuesta mientras la descarga y solo acepta una URL HTTPS cuyo host figure en la lista autorizada. URL, hosts autorizados, timeout, límite de respuesta, TTL, ventana de reintento y CORS se leen con Pydantic Settings.

### `frontend/src/services/api.js`

Única capa de acceso HTTP del frontend.

### `frontend/src/components/MapPanel.jsx`

Renderiza los eventos como GeoJSON en MapLibre. El mapa se carga de forma diferida para reducir el JavaScript inicial.

### `frontend/src/App.jsx`

Orquesta filtros, estados de red, estadísticas, selección y temas. Incluye estados explícitos de carga, error, vacío y éxito.

## Evolución prevista

Cuando el producto requiera históricos, notificaciones o analítica territorial:

- PostgreSQL + PostGIS para persistencia y consultas geoespaciales.
- Worker programado cada 2–5 minutos para ingestión autónoma.
- Historial de revisiones por `evid` para conservar cambios del IGN.
- API de detalle y estadísticas agregadas por territorio.

Estas piezas no se incluyen ahora para mantener un despliegue pequeño y mantenible.
