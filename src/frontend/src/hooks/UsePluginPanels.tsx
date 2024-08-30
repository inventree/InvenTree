import { t } from '@lingui/macro';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { api } from '../App';
import { PanelType } from '../components/nav/Panel';
import PluginPanel from '../components/plugins/PluginPanel';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { identifierString } from '../functions/conversion';
import { InvenTreeIcon, InvenTreeIconType } from '../functions/icons';
import { apiUrl } from '../states/ApiState';
import { useGlobalSettingsState } from '../states/SettingsState';

export function usePluginPanels({
  instance,
  model,
  id
}: {
  instance?: any;
  model?: ModelType | string;
  id?: string | number | null;
}): PanelType[] {
  const globalSettings = useGlobalSettingsState();

  const pluginPanelsEnabled: boolean = useMemo(
    () => globalSettings.isSet('ENABLE_PLUGINS_INTERFACE'),
    [globalSettings]
  );

  // API query to fetch initial information on available plugin panels
  const { isFetching, data: pluginPanels } = useQuery({
    enabled: pluginPanelsEnabled && !!model && id != undefined,
    queryKey: [model, id],
    queryFn: async () => {
      if (!pluginPanelsEnabled || !model) {
        return Promise.resolve([]);
      }

      return api
        .get(apiUrl(ApiEndpoints.plugin_panel_list), {
          params: {
            target_model: model,
            target_id: id
          }
        })
        .then((response: any) => response.data)
        .catch((error: any) => {
          console.error('Failed to fetch plugin panels:', error);
          return [];
        });
    }
  });

  return (
    pluginPanels?.map((pluginPanelProps: any) => {
      const iconName: string = pluginPanelProps.icon || 'plugin';

      return PluginPanel({
        ...pluginPanelProps,
        name: identifierString(
          `plugin-panel-${pluginPanelProps.plugin}-${pluginPanelProps.name}`
        ),
        label: pluginPanelProps.label || t`Plugin Panel`,
        icon: <InvenTreeIcon icon={iconName as InvenTreeIconType} />,
        id: id,
        model: model,
        instance: instance,
        pluginKey: pluginPanelProps.plugin || 'plugin'
      });
    }) ?? []
  );
}
