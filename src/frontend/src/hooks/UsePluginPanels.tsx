import { useMantineColorScheme, useMantineTheme } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../App';
import { PanelType } from '../components/nav/Panel';
import { PluginContext } from '../components/plugins/PluginContext';
import PluginPanelContent, {
  PluginPanelProps,
  isPluginPanelHidden
} from '../components/plugins/PluginPanel';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { identifierString } from '../functions/conversion';
import { InvenTreeIcon, InvenTreeIconType } from '../functions/icons';
import { apiUrl } from '../states/ApiState';
import { useLocalState } from '../states/LocalState';
import {
  useGlobalSettingsState,
  useUserSettingsState
} from '../states/SettingsState';
import { useUserState } from '../states/UserState';

export function usePluginPanels({
  instance,
  model,
  id
}: {
  instance?: any;
  model?: ModelType | string;
  id?: string | number | null;
}): PanelType[] {
  const host = useLocalState.getState().host;
  const navigate = useNavigate();
  const user = useUserState();
  const { colorScheme } = useMantineColorScheme();
  const theme = useMantineTheme();
  const globalSettings = useGlobalSettingsState();
  const userSettings = useUserSettingsState();

  const pluginPanelsEnabled: boolean = useMemo(
    () => globalSettings.isSet('ENABLE_PLUGINS_INTERFACE'),
    [globalSettings]
  );

  // API query to fetch initial information on available plugin panels
  const { data: pluginData } = useQuery({
    enabled: pluginPanelsEnabled && !!model && id !== undefined,
    queryKey: ['custom-plugin-panels', model, id],
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

  // Cache the context data which is delivered to the plugins
  const contextData: PluginContext = useMemo(() => {
    return {
      model: model,
      id: id,
      instance: instance,
      user: user,
      host: host,
      api: api,
      navigate: navigate,
      globalSettings: globalSettings,
      userSettings: userSettings,
      theme: theme,
      colorScheme: colorScheme
    };
  }, [
    model,
    id,
    instance,
    user,
    host,
    api,
    navigate,
    globalSettings,
    userSettings,
    theme,
    colorScheme
  ]);

  // Track which panels are hidden: { panelName: true/false }
  // We need to memoize this as the plugins can determine this dynamically
  const [panelState, setPanelState] = useState<Record<string, boolean>>({});

  // Clear the visibility cache when the plugin data changes
  // This will force the plugin panels to re-calculate their visibility
  useEffect(() => {
    pluginData?.forEach((props: PluginPanelProps) => {
      const identifier = identifierString(
        `plugin-panel-${props.plugin}-${props.name}`
      );

      // Check if the panel is hidden (defaults to true until we know otherwise)
      isPluginPanelHidden({
        pluginProps: props,
        pluginContext: contextData
      }).then((result) => {
        setPanelState((prev) => ({ ...prev, [identifier]: result }));
      });
    });
  }, [pluginData, contextData]);

  const pluginPanels: PanelType[] = useMemo(() => {
    return (
      pluginData?.map((props: PluginPanelProps) => {
        const iconName: string = props.icon || 'plugin';
        const identifier = identifierString(
          `plugin-panel-${props.plugin}-${props.name}`
        );
        const isHidden: boolean = panelState[identifier] ?? true;

        const pluginContext: any = {
          ...contextData,
          context: props.context
        };

        return {
          name: identifier,
          label: props.label,
          icon: <InvenTreeIcon icon={iconName as InvenTreeIconType} />,
          content: (
            <PluginPanelContent
              pluginProps={props}
              pluginContext={pluginContext}
            />
          ),
          hidden: isHidden
        };
      }) ?? []
    );
  }, [panelState, pluginData, contextData]);

  return pluginPanels;
}
