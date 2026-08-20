import { lazy, Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Clock3,
  Database,
  Gauge,
  LocateFixed,
  Moon,
  RefreshCw,
  Sun,
  Waves,
} from 'lucide-react';

import SkeletonLoader from './components/SkeletonLoader';
import { fetchEarthquakes } from './services/api';
import { deriveDashboardStats } from './utils/earthquakes';

const PERIODS = [
  { value: '3d', label: '72 horas' },
  { value: '10d', label: '10 días' },
  { value: '30d', label: '30 días' },
];

const MapPanel = lazy(() => import('./components/MapPanel'));

function formatTime(value) {
  return new Intl.DateTimeFormat('es-ES', {
    day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
  }).format(new Date(value));
}

function relativeTime(value) {
  const minutes = Math.max(0, Math.round((Date.now() - new Date(value).getTime()) / 60_000));
  if (minutes < 1) return 'Ahora';
  if (minutes < 60) return `Hace ${minutes} min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Hace ${hours} h`;
  return `Hace ${Math.floor(hours / 24)} d`;
}

function magnitudeClass(magnitude) {
  if (magnitude >= 4) return 'magnitude magnitude--high';
  if (magnitude >= 2.5) return 'magnitude magnitude--medium';
  return 'magnitude magnitude--low';
}

function StatCard({ icon: Icon, label, value, suffix }) {
  return (
    <motion.article
      className="stat-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <span className="stat-card__icon"><Icon size={18} /></span>
      <div>
        <p>{label}</p>
        <strong>{value}<small>{suffix}</small></strong>
      </div>
    </motion.article>
  );
}

function EarthquakeRow({ earthquake, selected, onSelect }) {
  return (
    <button
      type="button"
      className={`earthquake-row ${selected ? 'earthquake-row--selected' : ''}`}
      onClick={() => onSelect(earthquake.id)}
    >
      <span className={magnitudeClass(earthquake.magnitude)}>M {earthquake.magnitude.toFixed(1)}</span>
      <span className="earthquake-row__body">
        <strong>{earthquake.location || 'Localización pendiente'}</strong>
        <small><Clock3 size={12} /> {relativeTime(earthquake.occurred_at)} · {earthquake.depth_km} km</small>
      </span>
      <ArrowUpRight size={16} aria-hidden="true" />
    </button>
  );
}

export default function App() {
  const [period, setPeriod] = useState('3d');
  const [minMagnitude, setMinMagnitude] = useState(0);
  const [maxDepth, setMaxDepth] = useState('all');
  const [data, setData] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [status, setStatus] = useState('loading');
  const [error, setError] = useState('');
  const [theme, setTheme] = useState(() => localStorage.getItem('seismos-theme') || 'dark');
  const [reloadToken, setReloadToken] = useState(0);

  const loadData = useCallback(() => setReloadToken((token) => token + 1), []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('seismos-theme', theme);
  }, [theme]);

  useEffect(() => {
    const controller = new AbortController();
    setStatus('loading');
    setError('');

    fetchEarthquakes({ period, minMagnitude, maxDepth, signal: controller.signal })
      .then((payload) => {
        setData(payload);
        setSelectedId((current) => (
          payload.items.some((item) => item.id === current) ? current : null
        ));
        setStatus('success');
      })
      .catch((requestError) => {
        if (requestError.name !== 'AbortError') {
          setError(requestError.message);
          setStatus('error');
        }
      });

    return () => controller.abort();
  }, [period, minMagnitude, maxDepth, reloadToken]);

  const earthquakes = useMemo(() => data?.items ?? [], [data]);
  const stats = useMemo(() => deriveDashboardStats(earthquakes), [earthquakes]);
  const selected = earthquakes.find((item) => item.id === selectedId);

  return (
    <div className="app-shell">
      <div className="ambient ambient--one" />
      <div className="ambient ambient--two" />

      <header className="topbar">
        <a className="brand" href="#top" aria-label="Seísmos, inicio">
          <span className="brand__mark"><Waves size={20} /></span>
          <span>SEÍSMOS<small>por OBRATEC</small></span>
        </a>
        <div className="topbar__actions">
          <span className="official-badge"><Database size={14} /> Datos oficiales IGN</span>
          <button
            className="icon-button"
            type="button"
            onClick={() => setTheme((value) => value === 'dark' ? 'light' : 'dark')}
            aria-label="Cambiar tema"
          >
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </header>

      <main id="top">
        <section className="hero">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <span className="eyebrow"><i /> Actividad sísmica actualizada</span>
            <h1>España, <em>en movimiento.</em></h1>
            <p>Una lectura clara y visual de la actividad sísmica reciente, a partir de la red oficial del Instituto Geográfico Nacional.</p>
          </motion.div>
          <aside className="hero__signal" aria-label="Estado de la red">
            <span className="signal-orbit"><Activity size={28} /></span>
            <div><small>ESTADO DE LA RED</small><strong>Monitorización activa</strong></div>
          </aside>
        </section>

        <section className="stats-grid" aria-label="Resumen sísmico">
          {status === 'loading' ? (
            Array.from({ length: 4 }, (_, index) => <SkeletonLoader key={index} type="stat" />)
          ) : (
            <>
              <StatCard icon={Activity} label="Eventos registrados" value={stats.total} suffix="" />
              <StatCard icon={Gauge} label="Mayor magnitud" value={stats.strongest.toFixed(1)} suffix=" M" />
              <StatCard icon={LocateFixed} label="Sismos superficiales" value={stats.shallow} suffix="" />
              <StatCard icon={Clock3} label="Última actualización" value={data ? formatTime(data.meta.fetched_at).split(',')[1] : '—'} suffix="" />
            </>
          )}
        </section>

        <section className="workspace">
          <div className="workspace__toolbar">
            <div className="segmented" aria-label="Periodo de consulta">
              {PERIODS.map((item) => (
                <button
                  type="button"
                  key={item.value}
                  className={period === item.value ? 'active' : ''}
                  onClick={() => setPeriod(item.value)}
                >{item.label}</button>
              ))}
            </div>
            <div className="filter-group">
              <label>Magnitud
                <select value={minMagnitude} onChange={(event) => setMinMagnitude(Number(event.target.value))}>
                  <option value="0">Todas</option>
                  <option value="2">M 2+</option>
                  <option value="3">M 3+</option>
                  <option value="4">M 4+</option>
                </select>
              </label>
              <label>Profundidad
                <select value={maxDepth} onChange={(event) => setMaxDepth(event.target.value)}>
                  <option value="all">Todas</option>
                  <option value="15">Hasta 15 km</option>
                  <option value="50">Hasta 50 km</option>
                </select>
              </label>
            </div>
          </div>

          {status === 'error' && (
            <div className="state-panel state-panel--error">
              <span><AlertTriangle size={28} /></span>
              <h2>No podemos conectar con la red sísmica</h2>
              <p>{error}</p>
              <button type="button" onClick={loadData}><RefreshCw size={16} /> Reintentar</button>
            </div>
          )}

          {status === 'loading' && (
            <div className="dashboard-grid">
              <SkeletonLoader type="map" />
              <div className="feed-panel"><SkeletonLoader /><SkeletonLoader /><SkeletonLoader /></div>
            </div>
          )}

          {status === 'success' && earthquakes.length === 0 && (
            <div className="state-panel">
              <span><Waves size={28} /></span>
              <h2>Sin eventos para estos filtros</h2>
              <p>Amplía el periodo o reduce la magnitud mínima para consultar más actividad.</p>
              <button type="button" onClick={() => { setMinMagnitude(0); setMaxDepth('all'); }}>Restablecer filtros</button>
            </div>
          )}

          {status === 'success' && earthquakes.length > 0 && (
            <div className="dashboard-grid">
              <motion.div
                className="map-panel"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3 }}
              >
                <Suspense fallback={<SkeletonLoader type="map" />}>
                  <MapPanel
                    earthquakes={earthquakes}
                    selectedId={selectedId}
                    onSelect={setSelectedId}
                    theme={theme}
                  />
                </Suspense>
                <div className="map-panel__topline">
                  <span><i /> En directo</span>
                  <small>{earthquakes.length} eventos visibles</small>
                </div>
                <div className="map-legend">
                  <span><i className="dot dot--low" /> &lt; 2.5</span>
                  <span><i className="dot dot--medium" /> 2.5–3.9</span>
                  <span><i className="dot dot--high" /> 4+</span>
                </div>
                {selected && (
                  <motion.article
                    className="selected-card"
                    key={selected.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <span className={magnitudeClass(selected.magnitude)}>M {selected.magnitude.toFixed(1)}</span>
                    <div>
                      <small>EPICENTRO SELECCIONADO</small>
                      <strong>{selected.location}</strong>
                      <p>{formatTime(selected.occurred_at)} · Profundidad {selected.depth_km} km</p>
                    </div>
                  </motion.article>
                )}
              </motion.div>

              <aside className="feed-panel">
                <div className="feed-panel__header">
                  <div><span>ÚLTIMOS EVENTOS</span><h2>Actividad reciente</h2></div>
                  <button type="button" onClick={loadData} aria-label="Actualizar datos"><RefreshCw size={17} /></button>
                </div>
                <div className="feed-list">
                  {earthquakes.slice(0, 18).map((earthquake) => (
                    <EarthquakeRow
                      key={earthquake.id}
                      earthquake={earthquake}
                      selected={earthquake.id === selectedId}
                      onSelect={setSelectedId}
                    />
                  ))}
                </div>
                <div className="feed-panel__footer">
                  <span><i /> {data.meta.stale ? 'Copia de respaldo' : 'Sincronizado con IGN'}</span>
                  <small>{formatTime(data.meta.fetched_at)}</small>
                </div>
              </aside>
            </div>
          )}
        </section>

        <section className="source-note">
          <Database size={22} />
          <div><strong>Datos públicos, lectura independiente.</strong><p>La información procede del Instituto Geográfico Nacional y puede revisarse después de su publicación.</p></div>
          <a href="https://www.ign.es/web/ultimos-terremotos" target="_blank" rel="noreferrer">Consultar fuente <ArrowUpRight size={15} /></a>
        </section>
      </main>

      <footer>
        <span>SEÍSMOS · Una iniciativa de OBRATEC</span>
        <span>No es un servicio oficial del Gobierno de España.</span>
      </footer>
    </div>
  );
}
