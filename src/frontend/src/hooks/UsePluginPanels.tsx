import { t } from '@lingui/macro';
import { Alert, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { api } from '../App';
import { PanelType } from '../components/nav/Panel';
import PluginPanel from '../components/plugins/PluginPanel';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { identifierString } from '../functions/conversion';
import { InvenTreeIcon } from '../functions/icons';
import { apiUrl } from '../states/ApiState';
import { useGlobalSettingsState } from '../states/SettingsState';

export type PluginPanelState = {
  panels: PanelType[];
};

export function usePluginPanels({
  instance,
  model,
  id
}: {
  instance?: any;
  model?: ModelType | string;
  id?: string | number | null;
}): PluginPanelState {
  const globalSettings = useGlobalSettingsState();

  const pluginPanelsEnabled = useMemo(
    () => globalSettings.isSet('ENABLE_PLUGINS_INTERFACE'),
    [globalSettings]
  );

  // API query to fetch initial information on available plugin panels
  const { isFetching, data } = useQuery({
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

  const panels: PanelType[] = useMemo(() => {
    return (
      data?.map((panel: any) => {
        const pluginKey = panel.plugin || 'plugin';
        return {
          name: identifierString(`pluigin-${pluginKey}-${panel.name}`),
          label: panel.label || t`Plugin Panel`,
          icon: <InvenTreeIcon icon={panel.icon ?? 'plugin'} />,
          content: (
            <PluginPanel
              props={{
                ...panel,
                id: id,
                model: model,
                instance: instance
              }}
            />
          )
        };
      }) ?? []
    );
  }, [data, id, model, instance]);

  return {
    panels: panels
  };
}
