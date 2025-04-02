/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DEMO: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare const __INVENTREE_LIB_VERSION__: string;
