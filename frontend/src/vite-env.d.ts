/// <reference types="vite/client" />

// Typed access to the variables in frontend/.env (see .env.example).
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_API_PREFIX?: string
  readonly VITE_API_TIMEOUT_MS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
