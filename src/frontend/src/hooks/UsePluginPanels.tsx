import { t } from '@lingui/macro';
import { Alert, Text } from '@mantine/core';
import { useTimeout } from '@mantine/hooks';
import { Icon24Hours } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { ReactNode, useEffect, useMemo, useState } from 'react';

import { api } from '../App';
import { PanelType } from '../components/nav/Panel';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { identifierString } from '../functions/conversion';
import { InvenTreeIcon } from '../functions/icons';
import { apiUrl } from '../states/ApiState';

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
  targetModel: string;
  targetId?: string | number | null;
}): PluginPanelState {
  const { isFetching, data } = useQuery({
    queryKey: [targetModel, targetId],
    queryFn: () => {
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
