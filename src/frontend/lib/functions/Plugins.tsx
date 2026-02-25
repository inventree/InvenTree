import {
  INVENTREE_PLUGIN_VERSION,
  type InvenTreePluginContext
} from '../types/Plugins';

/**
 * Check that the plugin version matches the expected version.
 * This is a helper function which only generates a warning if there is a mismatch.
 */
export function checkPluginVersion(context: InvenTreePluginContext) {
  const systemVersion: string = context?.version?.inventree || '';

  if (INVENTREE_PLUGIN_VERSION != systemVersion) {
    console.info(
      `Plugin version mismatch! Expected version ${INVENTREE_PLUGIN_VERSION}, got ${systemVersion}`
    );
  }
}

/**
 * Helper function to initialize the plugin context.
 */
export function initPlugin(context: InvenTreePluginContext) {
  // Check that the plugin version matches the expected version
  checkPluginVersion(context);

  // Activate the i18n context for the current locale
  context.i18n?.activate?.(context.locale);
}
