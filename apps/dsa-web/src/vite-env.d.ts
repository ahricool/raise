/// <reference types="vite/client" />

declare const __APP_PACKAGE_VERSION__: string
declare const __APP_BUILD_TIME__: string

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
