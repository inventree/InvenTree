import { Route, Routes } from 'react-router-dom';

import { usePluginUIFeature } from '../../hooks/UsePluginUIFeature';
import type { RouteUIFeature } from './PluginUIFeatureTypes';
import RemoteComponent from './RemoteComponent';

import { useInvenTreeContext } from './PluginContext';

import NotFound from '../errors/NotFound';

export function PluginRoutes() {
  const routes = usePluginUIFeature<RouteUIFeature>({
    featureType: 'route',
    context: {}
  });

  const pluginContext = useInvenTreeContext();

  return (
    <Routes>
      {routes.map((route) => (
        <Route
          key={route.options.key}
          path={`${route.options.plugin_name}/${route.options.options.path}`}
          element={
            <RemoteComponent
              source={route.options.source}
              defaultFunctionName='getFeature'
              context={pluginContext}
            />
          }
        />
      ))}

      <Route path='*' element={<NotFound />} />
    </Routes>
  );
}
