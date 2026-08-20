import { describe, expect, it } from 'vitest';

import { deriveDashboardStats } from './earthquakes';

const earthquakes = [
  { id: 'a', magnitude: 2.4, depth_km: 10 },
  { id: 'b', magnitude: 3.8, depth_km: 55 },
  { id: 'c', magnitude: 1.9, depth_km: 4 },
];

describe('deriveDashboardStats', () => {
  it('summarizes total, strongest and shallow earthquakes', () => {
    expect(deriveDashboardStats(earthquakes)).toEqual({
      total: 3,
      strongest: 3.8,
      shallow: 2,
    });
  });
});
