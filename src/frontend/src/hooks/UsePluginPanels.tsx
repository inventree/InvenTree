import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { api } from '../App';
import { PanelType } from '../components/panels/Panel';
import {
  InvenTreeContext,
  useInvenTreeContext
} from '../components/plugins/PluginContext';
import PluginPanelContent from '../components/plugins/PluginPanel';
import {
  PluginUIFeature,
  PluginUIFeatureType
} from '../components/plugins/PluginUIFeature';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { identifierString } from '../functions/conversion';
import { InvenTreeIcon, InvenTreeIconType } from '../functions/icons';
import { apiUrl } from '../states/ApiState';
import { useGlobalSettingsState } from '../states/SettingsState';

/**
 * @param model - The model type for the plugin (e.g. 'part' / 'purchaseorder')
 * @param id - The ID (primary key) of the model instance for the plugin
 * @param instance - The model instance data (if available)
 */
export type PluginPanelContext = InvenTreeContext & {
  model?: ModelType | string;
  id?: string | number | null;
  instance?: any;
};

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
  const { data: pluginData } = useQuery({
    enabled: pluginPanelsEnabled && !!model && id !== undefined,
    queryKey: ['custom-plugin-panels', model, id],
    queryFn: async () => {
      if (!pluginPanelsEnabled || !model) {
        return Promise.resolve([]);
      }

      const url = apiUrl(ApiEndpoints.plugin_ui_features_list, undefined, {
        feature_type: PluginUIFeatureType.panel
      });

      return api
        .get(url, {
          params: {
            target_model: model,
            target_id: id
          }
        })
        .then((response: any) => response.data)
        .catch((_error: any) => {
          console.error(`ERR: Failed to fetch plugin panels`);
          return [];
        });
    }
  });

  // Cache the context data which is delivered to the plugins
  const inventreeContext = useInvenTreeContext();
  const contextData = useMemo<PluginPanelContext>(() => {
    return {
      model: model,
      id: id,
      instance: instance,
      ...inventreeContext
    };
  }, [model, id, instance]);

  const pluginPanels: PanelType[] = useMemo(() => {
    return (
      pluginData?.map((props: PluginUIFeature) => {
        const iconName: string = props?.icon || 'plugin';
        const identifier = identifierString(
          `${props.plugin_name}-${props.key}`
        );

        const pluginContext: any = {
          ...contextData,
          context: props.context
        };

        return {
          name: identifier,
          label: props.title,
          icon: <InvenTreeIcon icon={iconName as InvenTreeIconType} />,
          content: (
            <PluginPanelContent
              pluginFeature={props}
              pluginContext={pluginContext}
            />
          )
        };
      }) ?? []
    );
  }, [pluginData, contextData]);

  return pluginPanels;
}
