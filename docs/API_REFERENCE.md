# API Reference

Base local: `http://localhost:8000`

## `GET /api/health`

Comprueba que el proceso HTTP está operativo.

```json
{"status":"ok"}
```

## `GET /api/v1/earthquakes`

Devuelve terremotos normalizados desde el feed oficial del IGN.

### Query parameters

| Parámetro | Tipo | Valores | Predeterminado |
|---|---|---|---|
| `period` | string | `3d`, `10d`, `30d` | `3d` |
| `min_magnitude` | number | `0`–`10` | `0` |
| `max_depth` | number | `0`–`1000` km | sin límite |

### Ejemplo

```http
GET /api/v1/earthquakes?period=3d&min_magnitude=2&max_depth=50
```

```json
{
  "meta": {
    "count": 1,
    "period": "3d",
    "stale": false,
    "fetched_at": "2026-08-20T18:00:00Z",
    "source": "Instituto Geográfico Nacional (IGN)"
  },
  "items": [
    {
      "id": "es2026test",
      "magnitude": 2.4,
      "magnitude_type": "mbLg",
      "depth_km": 10.0,
      "occurred_at": "2026-08-20T17:46:04Z",
      "local_time": "2026-08-20T19:46:04",
      "location": "SE CHURRIANA DE LA VEGA.GR",
      "intensity": "II",
      "longitude": -3.6,
      "latitude": 37.1
    }
  ]
}
```

### Errores

- `422`: parámetros no válidos.
- `503`: feed del IGN no disponible y sin copia en caché.

`stale: true` indica que no se pudo obtener o validar una instantánea nueva del IGN y se entregó la última copia disponible.
