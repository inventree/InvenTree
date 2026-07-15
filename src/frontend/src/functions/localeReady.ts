/**
 * Tiny pub/sub so code outside the React tree (e.g. router.tsx) can safely
 * prefetch chunks that evaluate top-level i18n macros, without needing to
 * know how/when LanguageContext finishes activating the locale.
 */
type Listener = () => void;

let ready = false;
const listeners = new Set<Listener>();

export function markLocaleReady() {
  if (ready) return;
  ready = true;
  for (const listener of listeners) listener();
  listeners.clear();
}

export function onLocaleReady(listener: Listener) {
  if (ready) {
    listener();
  } else {
    listeners.add(listener);
  }
}
