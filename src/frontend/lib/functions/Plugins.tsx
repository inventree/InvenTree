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
