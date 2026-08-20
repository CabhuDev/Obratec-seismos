import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import App from './App';

vi.mock('./components/MapPanel', () => ({
  default: () => <div data-testid="map-panel" />,
}));

const response = {
  meta: {
    count: 1,
    period: '3d',
    stale: false,
    fetched_at: '2026-08-20T18:00:00Z',
    source: 'Instituto Geográfico Nacional (IGN)',
  },
  items: [
    {
      id: 'es2026test',
      magnitude: 2.4,
      depth_km: 10,
      occurred_at: '2026-08-20T17:46:04Z',
      local_time: '2026-08-20T19:46:04',
      location: 'SE CHURRIANA DE LA VEGA.GR',
      longitude: -3.6,
      latitude: 37.1,
    },
  ],
};

describe('App', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => response,
    }));
  });

  it('shows official earthquake data after loading', async () => {
    render(<App />);

    expect(screen.getByRole('heading', { name: /España, en movimiento/i })).toBeInTheDocument();
    expect((await screen.findAllByText('SE CHURRIANA DE LA VEGA.GR')).length).toBeGreaterThan(0);
    expect(screen.getAllByText('M 2.4').length).toBeGreaterThan(0);
    expect(await screen.findByTestId('map-panel')).toBeInTheDocument();
  });
});
