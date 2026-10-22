let pluginGlobals: Promise<unknown> | null = null;

/*
 * Ensure the window globals required by external plugins are set,
 * loading them on first use.
 */
export function ensurePluginGlobals(): Promise<unknown> {
  pluginGlobals ??= import('./pluginGlobalsSetup');
  return pluginGlobals;
}
