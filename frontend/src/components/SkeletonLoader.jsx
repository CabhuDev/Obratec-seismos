export default function SkeletonLoader({ type = 'card' }) {
  // Decorativo: el estado de carga se anuncia UNA vez desde App.jsx, no
  // una por cada hueco. Un aria-label sobre un div sin role no lo lee nadie.
  return <div className={`skeleton skeleton--${type}`} aria-hidden="true" />;
}
