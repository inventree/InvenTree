import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { api } from '../App';
import { PanelType } from '../components/nav/Panel';
import { PluginContext } from '../components/plugins/PluginContext';
import {
  PluginPanelProps,
  isPluginPanelHidden
} from '../components/plugins/PluginPanel';
import PluginPanelContent from '../components/plugins/PluginPanel';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { identifierString } from '../functions/conversion';
import { InvenTreeIcon, InvenTreeIconType } from '../functions/icons';
import { apiUrl } from '../states/ApiState';
import { useLocalState } from '../states/LocalState';
import { useGlobalSettingsState } from '../states/SettingsState';
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
  const globalSettings = useGlobalSettingsState();

  const pluginPanelsEnabled: boolean = useMemo(
    () => globalSettings.isSet('ENABLE_PLUGINS_INTERFACE'),
    [globalSettings]
  );

  // API query to fetch initial information on available plugin panels
  const { isFetching, data: pluginData } = useQuery({
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

  const pluginPanels: PanelType[] = useMemo(() => {
    return (
      pluginData?.map((props: PluginPanelProps) => {
        const iconName: string = props.icon || 'plugin';
        const content: any = props.content || 'some content here';

        // Construct the plugin attributes - to be passed through for rendering
        const pluginContext: PluginContext = {
          pluginName: props.plugin,
          target: undefined,
          model: model,
          id: id,
          instance: instance,
          user: user,
          navigate: navigate,
          host: host,
          api: api
        };

        const isHidden = isPluginPanelHidden({
          pluginProps: props,
          pluginContext: pluginContext
        });

        return {
          name: identifierString(`plugin-panel-${props.plugin}-${props.name}`),
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

        /*
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
      */
      }) ?? []
    );
  }, [pluginData, id, model, instance, user, navigate, host]);

  return pluginPanels;
}
