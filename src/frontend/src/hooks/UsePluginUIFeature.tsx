import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { api } from '../App';
import { useInvenTreeContext } from '../components/plugins/PluginContext';
import { findExternalPluginFunction } from '../components/plugins/PluginSource';
import type {
  BaseUIFeature,
  PluginUIFeatureAPIResponse,
  PluginUIFuncWithoutInvenTreeContextType
} from '../components/plugins/PluginUIFeatureTypes';
import { ApiEndpoints } from '../enums/ApiEndpoints';
import { apiUrl } from '../states/ApiState';
import { useGlobalSettingsState } from '../states/SettingsState';

export function usePluginUIFeature<UIFeatureT extends BaseUIFeature>({
  enabled = true,
  featureType,
  context
}: {
  enabled?: boolean;
  featureType: UIFeatureT['featureType'];
  context: UIFeatureT['requestContext'];
}) {
  const globalSettings = useGlobalSettingsState();

  const pluginUiFeaturesEnabled: boolean = useMemo(
    () => globalSettings.isSet('ENABLE_PLUGINS_INTERFACE'),
    [globalSettings]
  );

  // API query to fetch initial information on available plugin panels
  const { data: pluginData } = useQuery<
    PluginUIFeatureAPIResponse<UIFeatureT>[]
  >({
    enabled: pluginUiFeaturesEnabled && !!featureType && enabled,
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
            `ERR: Failed to fetch plugin ui features for feature "${featureType}":`,
            error
          );
          return [];
        });
    }
  });

  // Cache the context data which is delivered to the plugins
  const inventreeContext = useInvenTreeContext();

  return useMemo<
    {
      options: UIFeatureT['responseOptions'];
      func: PluginUIFuncWithoutInvenTreeContextType<UIFeatureT>;
    }[]
  >(() => {
    return (
      pluginData?.map((feature) => {
        return {
          options: {
            ...feature
          },
          func: (async (featureContext) => {
            const func = await findExternalPluginFunction(
              feature.source,
              'getFeature'
            );
            if (!func) return;

            return func({
              featureContext,
              inventreeContext
            });
          }) as PluginUIFuncWithoutInvenTreeContextType<UIFeatureT>
        };
      }) || []
    );
  }, [pluginData, inventreeContext]);
}
