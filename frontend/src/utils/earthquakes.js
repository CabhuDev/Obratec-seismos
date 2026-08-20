export function deriveDashboardStats(earthquakes) {
  const magnitudes = earthquakes.map((item) => item.magnitude);

  return {
    total: earthquakes.length,
    strongest: magnitudes.length ? Math.max(...magnitudes) : 0,
    shallow: earthquakes.filter((item) => item.depth_km <= 15).length,
  };
}
