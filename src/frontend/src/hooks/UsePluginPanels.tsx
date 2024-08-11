import { t } from '@lingui/macro';
import { Alert, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { api } from '../App';
import { PanelType } from '../components/nav/Panel';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { identifierString } from '../functions/conversion';
import { InvenTreeIcon } from '../functions/icons';
import { apiUrl } from '../states/ApiState';
import { useGlobalSettingsState } from '../states/SettingsState';

export type PluginPanelState = {
  panels: PanelType[];
};

// Placeholder content for a panel with no content
function PanelNoContent() {
  return (
    <Alert color="red" title={t`No Content`}>
      <Text>{t`No content provided for this plugin`}</Text>
    </Alert>
  );
}

export function usePluginPanels({
  targetModel,
  targetId
}: {
  targetModel?: ModelType | string;
  targetId?: string | number | null;
}): PluginPanelState {
  const globalSettings = useGlobalSettingsState();

  const pluginPanelsEnabled = useMemo(
    () => globalSettings.isSet('ENABLE_PLUGINS_INTERFACE'),
    [globalSettings]
  );

  const { isFetching, data } = useQuery({
    enabled: pluginPanelsEnabled && !!targetModel,
    queryKey: [targetModel, targetId],
    queryFn: () => {
      console.log('Fetching plugin panels:', targetModel, targetId);

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
          content: panel.content || <PanelNoContent />
        };
      }) ?? []
    );
  }, [data]);

  return {
    panels: panels
  };
}
