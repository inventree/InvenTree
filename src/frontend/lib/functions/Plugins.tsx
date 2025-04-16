import {
  INVENTREE_PLUGIN_VERSION,
  type InvenTreePluginContext
} from '../types/Plugins';

function extractVersion(version: string) {
  // Extract the version number from the string
  const [major, minor, patch] = version
    .split('.')
    .map((v) => Number.parseInt(v, 10));

  return { major, minor, patch };
}

/**
 * Check th e
 */
export function checkPluginVersion(context: InvenTreePluginContext) {
  const pluginVersion = extractVersion(INVENTREE_PLUGIN_VERSION);
  const systemVersion = extractVersion(context.version.inventree);

  const mismatch = `Plugin version mismatch! Expected version ${INVENTREE_PLUGIN_VERSION}, got ${context.version}`;

  // A major version mismatch indicates a potentially breaking change
  if (pluginVersion.major !== systemVersion.major) {
    console.warn(mismatch);
  } else if (INVENTREE_PLUGIN_VERSION != context.version.inventree) {
    console.info(mismatch);
  }
}
