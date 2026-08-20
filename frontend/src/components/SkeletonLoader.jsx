export default function SkeletonLoader({ type = 'card' }) {
  return <div className={`skeleton skeleton--${type}`} aria-label="Cargando datos" />;
}
