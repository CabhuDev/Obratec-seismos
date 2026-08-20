# OBRATEC Seísmos

Una experiencia pública y visual para consultar la actividad sísmica reciente en España con datos oficiales del [Instituto Geográfico Nacional](https://www.ign.es/web/ultimos-terremotos).

> Proyecto independiente. No es un servicio oficial del Gobierno de España.

## Qué incluye

- Mapa interactivo de España con MapLibre.
- Eventos de los últimos 3, 10 o 30 días.
- Filtros por magnitud y profundidad.
- Resumen de actividad, magnitud máxima y sismos superficiales.
- Selección sincronizada entre mapa y listado.
- Temas claro y oscuro, interfaz responsive y estados de carga, error y vacío.
- API propia con caché de 120 segundos y respaldo de datos en memoria.
- Atribución y aviso de provisionalidad de los datos del IGN.

## Arquitectura

```text
Feed público del IGN
        ↓
FastAPI · normalización y caché
        ↓
GET /api/v1/earthquakes
        ↓
React · Vite · MapLibre
```

El navegador no consume directamente el archivo JavaScript del IGN. El backend lo descarga, extrae la colección GeoJSON solicitada y devuelve un contrato JSON estable.

Consulta [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) y [docs/API_REFERENCE.md](docs/API_REFERENCE.md) para más detalle.

## Desarrollo local

### Backend

```bash
uv sync --dev
uv run uvicorn backend.app.main:app --reload --port 8000
```

API y OpenAPI:

- `http://localhost:8000/api/health`
- `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Web: `http://localhost:5173`

Vite reenvía automáticamente `/api` al backend en el puerto `8000`.

## Docker

```bash
docker compose up --build
```

Web completa: `http://localhost:8080`

## Configuración

Copia `.env.example` a `.env` para configurar la API. Docker Compose interpola ese archivo
raíz y pasa los valores `SEISMOS_*` al contenedor `api`; el backend local también lo lee.

| Variable | Predeterminado | Uso |
|---|---|---|
| `SEISMOS_IGN_FEED_URL` | Feed público del IGN | Origen de los datos |
| `SEISMOS_IGN_ALLOWED_HOSTS` | `www.ign.es` | Lista de hosts HTTPS autorizados para el feed |
| `SEISMOS_IGN_TIMEOUT_SECONDS` | `10` | Timeout de red |
| `SEISMOS_IGN_MAX_RESPONSE_BYTES` | `5000000` | Límite duro de descarga del feed |
| `SEISMOS_CACHE_TTL_SECONDS` | `120` | Duración de la caché |
| `SEISMOS_UPSTREAM_RETRY_SECONDS` | `30` | Espera antes de reintentar el feed tras un fallo |
| `SEISMOS_CORS_ORIGINS` | `http://localhost:5173` local / `http://localhost:8080` Docker | Orígenes frontend autorizados |

Para un frontend Vite independiente, copia `frontend/.env.example` a `frontend/.env` y
configura `VITE_API_BASE_URL` solo si la API está en otro origen. En desarrollo se usa el
proxy de Vite y en Docker se deja vacío: Nginx sirve la web y reenvía `/api` al contenedor
`api` bajo el mismo origen.

## Verificación

```bash
uv run ruff check backend
uv run pytest backend/tests --cov=backend.app --cov-fail-under=80 -q

cd frontend
npm run lint
npm test
npm run build
```

## Fuente y licencia de los datos

Fuente: **Instituto Geográfico Nacional (IGN), Ministerio de Transportes y Movilidad Sostenible**.

- [Últimos terremotos](https://www.ign.es/web/ultimos-terremotos)
- [Política de datos del IGN](https://www.ign.es/web/ign/portal/politica-datos)
- [Licencia compatible con CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.es_ES)

Los parámetros sísmicos pueden revisarse después de su publicación. El diseño, el código y la interpretación visual de esta aplicación son independientes del IGN.

## Licencia

Código publicado bajo [MIT](LICENSE).
