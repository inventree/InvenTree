/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_NETLIFY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
