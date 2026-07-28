import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTypeScript from 'eslint-config-next/typescript';

export default defineConfig([
  ...nextVitals,
  ...nextTypeScript,
  {
    rules: {
      // Existing hooks intentionally reset loading/form state when their inputs change.
      'react-hooks/set-state-in-effect': 'off',
    },
  },
  globalIgnores([
    '.next/**',
    'node_modules/**',
    'coverage/**',
    'build/**',
    'dist/**',
    'out/**',
    'next-env.d.ts',
  ]),
]);
