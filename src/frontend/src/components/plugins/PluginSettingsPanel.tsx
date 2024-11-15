import { useInvenTreeContext } from './PluginContext';
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
  pluginAdmin
}: Readonly<{
  pluginAdmin: PluginAdminInterface;
}>) {
  const pluginContext = useInvenTreeContext();

  return (
    <RemoteComponent
      source={pluginAdmin.source}
      defaultFunctionName='renderPluginSettings'
      context={{ ...pluginContext, context: pluginAdmin.context }}
    />
  );
}
