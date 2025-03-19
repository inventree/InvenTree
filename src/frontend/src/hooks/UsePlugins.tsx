import { ApiEndpoints } from '@lib/core';
import { useCallback } from 'react';
import { useInstance } from '../../lib/hooks/UseInstance';
import type { PluginInterface } from '../components/plugins/PluginInterface';

export interface UsePluginResult {
  plugins: PluginInterface[];
  withMixin: (mixin: string) => PluginInterface[];
}

/**
 * Hook for storing information on active plugins
 */
export const usePlugins = (): UsePluginResult => {
  const pluginQuery = useInstance({
    endpoint: ApiEndpoints.plugin_list,
    defaultValue: [],
    hasPrimaryKey: false,
    refetchOnMount: true,
    refetchOnWindowFocus: false,
    params: {
      active: true
    }
  });

  const pluginsWithMixin = useCallback(
    (mixin: string) => {
      return pluginQuery.instance.filter((plugin: PluginInterface) => {
        return !!plugin.mixins[mixin];
      });
    },
    [pluginQuery.instance]
  );

  return {
    plugins: pluginQuery.instance,
    withMixin: pluginsWithMixin
  };
};

export const usePluginsWithMixin = (mixin: string): PluginInterface[] => {
  const plugins = usePlugins();

  return plugins.withMixin(mixin);
};
