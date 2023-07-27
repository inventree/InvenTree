/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SERVER_SELECTOR_DEV: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
