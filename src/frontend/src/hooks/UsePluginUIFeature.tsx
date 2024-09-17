import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { api } from '../App';
import {
  PluginContext,
  usePluginContext
} from '../components/plugins/PluginContext';
import { findExternalPluginFunction } from '../components/plugins/PluginSource';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';
import { useGlobalSettingsState } from '../states/SettingsState';

export function usePluginUIFeature<
  RequestContextT extends Record<string, any>,
  ResponseOptionsT extends Record<string, any>,
  RenderContextT extends Record<string, any>
>({ featureType, context }: { featureType: string; context: RequestContextT }) {
  const globalSettings = useGlobalSettingsState();

  const pluginUiFeaturesEnabled: boolean = useMemo(
    () => globalSettings.isSet('ENABLE_PLUGINS_INTERFACE'),
    [globalSettings]
  );

  // API query to fetch initial information on available plugin panels
  const { data: pluginData } = useQuery({
    enabled: pluginUiFeaturesEnabled && !!featureType,
    queryKey: ['custom-ui-features', featureType, JSON.stringify(context)],
    queryFn: async () => {
      if (!pluginUiFeaturesEnabled || !featureType) {
        return Promise.resolve([]);
      }

      return api
        .get(
          apiUrl(ApiEndpoints.plugin_ui_features_list, undefined, {
            feature_type: featureType
          }),
          {
            params: context
          }
        )
        .then((response: any) => response.data)
        .catch((error: any) => {
          console.error(
            `Failed to fetch plugin ui features for feature "${featureType}":`,
            error
          );
          return [];
        });
    }
  });

  // Cache the context data which is delivered to the plugins
  const pluginContext = usePluginContext();

  return useMemo<
    {
      options: ResponseOptionsT;
      func: (
        ref: HTMLDivElement,
        params: { renderContext: RenderContextT; pluginContext: PluginContext }
      ) => void;
    }[]
  >(() => {
    return (
      pluginData?.map((feature: any) => ({
        options: feature.options,
        func: async (ref: HTMLDivElement, renderContext: RenderContextT) => {
          const func = await findExternalPluginFunction(
            feature.source,
            'getFeature'
          );
          return func(ref, {
            renderContext,
            pluginContext
          });
        }
      })) || []
    );
  }, [pluginData, pluginContext]);
}
