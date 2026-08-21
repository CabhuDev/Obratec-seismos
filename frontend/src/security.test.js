import { readFileSync } from 'node:fs';

import { describe, expect, it } from 'vitest';

describe('third-party resources', () => {
  it('keeps fonts self-hosted', () => {
    const html = readFileSync('index.html', 'utf8');

    expect(html).not.toContain('fonts.googleapis.com');
    expect(html).not.toContain('fonts.gstatic.com');
  });
});
