/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_DEMO: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

// Version information is replaced at build time
declare const __INVENTREE_LIB_VERSION__: string;
declare const __INVENTREE_REACT_VERSION__: string;
declare const __INVENTREE_REACT_DOM_VERSION__: string;
declare const __INVENTREE_MANTINE_VERSION__: string;
