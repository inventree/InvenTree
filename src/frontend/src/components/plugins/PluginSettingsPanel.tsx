import { t } from '@lingui/macro';
import { Alert, Stack, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useEffect, useMemo, useRef, useState } from 'react';

import { useInvenTreeContext } from './PluginContext';
import { findExternalPluginFunction } from './PluginSource';
import RemoteComponent from './RemoteComponent';

/**
 * Interface for the plugin admin data
 */
export interface PluginAdminInterface {
  source: string;
  context: any;
}

/**
 * A panel which is used to display custom settings UI for a plugin.
 *
 * This settings panel is loaded dynamically,
 * and requires that the plugin provides a javascript module,
 * which exports a function `renderPluginSettings`
 */
export default function PluginSettingsPanel({
  pluginInstance,
  pluginAdmin
}: {
  pluginInstance: any;
  pluginAdmin: PluginAdminInterface;
}) {
  const pluginContext = useInvenTreeContext();

  return (
    <RemoteComponent
      source={pluginAdmin.source}
      defaultFunctionName="renderPluginSettings"
      context={{ ...pluginContext, context: pluginAdmin.context }}
    />
  );
}
