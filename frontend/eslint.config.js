import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
  globalIgnores(['dist', 'design_handoff_speakwise', 'test-results', 'playwright-report']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs.flat.recommended,
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      globals: globals.browser,
    },
    rules: {
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrors: 'none' },
      ],
    },
  },
  {
    // src/core must stay platform-agnostic so it can be shared with the React Native app.
    files: ['src/core/**/*.{ts,tsx}'],
    rules: {
      'no-restricted-globals': [
        'error',
        { name: 'window', message: 'src/core must not use browser APIs.' },
        { name: 'document', message: 'src/core must not use browser APIs.' },
        { name: 'navigator', message: 'src/core must not use browser APIs.' },
        { name: 'localStorage', message: 'src/core must not use browser APIs.' },
        { name: 'sessionStorage', message: 'src/core must not use browser APIs.' },
      ],
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            { group: ['react-dom', 'react-dom/*'], message: 'src/core must not depend on react-dom.' },
            { group: ['@/components/*', '@/features/*', '@/hooks/*', '@/context/*', '@/app/*'], message: 'src/core must not import UI code.' },
            { group: ['*.css'], message: 'src/core must not import CSS.' },
          ],
        },
      ],
    },
  },
])
