import {
  INVENTREE_PLUGIN_VERSION,
  type InvenTreePluginContext
} from '../types/Plugins';

export function checkPluginVersion(context: InvenTreePluginContext) {
  if (context.version != INVENTREE_PLUGIN_VERSION) {
    console.warn(
      `Plugin version mismatch! Expected ${INVENTREE_PLUGIN_VERSION}, got ${context.version}`
    );
  }
}
