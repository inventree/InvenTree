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
  targetInstance,
  targetModel,
  targetId
}: {
  targetInstance?: any;
  targetModel?: ModelType | string;
  targetId?: string | number | null;
}): PluginPanelState {
  const globalSettings = useGlobalSettingsState();

  const pluginPanelsEnabled = useMemo(
    () => globalSettings.isSet('ENABLE_PLUGINS_INTERFACE'),
    [globalSettings]
  );

  // API query to fetch information on available plugin panels
  const { isFetching, data } = useQuery({
    enabled: pluginPanelsEnabled && !!targetModel && targetId != undefined,
    queryKey: [targetModel, targetId],
    queryFn: async () => {
      if (!pluginPanelsEnabled || !targetModel) {
        return Promise.resolve([]);
      }

      return api
        .get(apiUrl(ApiEndpoints.plugin_panel_list), {
          params: {
            target_model: targetModel,
            target_id: targetId
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
          name: identifierString(`${pluginKey}-${panel.name}`),
          label: panel.label || t`Plugin Panel`,
          icon: <InvenTreeIcon icon={panel.icon ?? 'plugin'} />,
          content: (
            <PluginPanel
              props={{
                ...panel,
                targetId: targetId,
                targetModel: targetModel,
                targetInstance: targetInstance
              }}
            />
          )
        };
      }) ?? []
    );
  }, [data, targetId, targetModel, targetInstance]);

  return {
    panels: panels
  };
}
