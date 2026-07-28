import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';

const mode = process.env.SECURITY_HEADERS_TEST_MODE;

if (!mode) {
  for (const testMode of ['development', 'production']) {
    const result = spawnSync(process.execPath, [import.meta.filename], {
      env: {
        ...process.env,
        NODE_ENV: testMode,
        NEXT_PUBLIC_API_URL: 'https://api.example.test/api',
        SECURITY_HEADERS_TEST_MODE: testMode,
      },
      stdio: 'inherit',
    });
    assert.equal(result.status, 0, `${testMode} security-header check failed`);
  }
} else {
  const { default: nextConfig } = await import('../next.config.js');
  const [{ headers }] = await nextConfig.headers();
  const values = Object.fromEntries(headers.map(({ key, value }) => [key, value]));
  const csp = values['Content-Security-Policy'];

  assert.match(csp, /connect-src 'self' https:\/\/api\.example\.test/);
  assert.match(csp, /frame-ancestors 'none'/);
  assert.equal(values['X-Content-Type-Options'], 'nosniff');
  assert.equal(values['X-Frame-Options'], 'DENY');
  assert.ok(values['Permissions-Policy']);

  if (mode === 'production') {
    assert.doesNotMatch(csp, /'unsafe-eval'/);
    assert.doesNotMatch(csp, /ws:\/\/localhost/);
  } else {
    assert.match(csp, /'unsafe-eval'/);
    assert.match(csp, /ws:\/\/localhost:\*/);
  }

  console.log(`${mode} security headers verified.`);
}
