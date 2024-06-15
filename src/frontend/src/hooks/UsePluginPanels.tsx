import { useTimeout } from '@mantine/hooks';
import { Icon24Hours } from '@tabler/icons-react';
import { ReactNode, useEffect, useMemo, useState } from 'react';

import { PanelType } from '../components/nav/Panel';

export interface PluginPanelState extends PanelType {
  pluginKey: string;
  targetType: string;
  targetId?: string | number | null;
}

export function usePluginPanel({
  pluginKey,
  panelName,
  targetModel,
  targetId
}: {
  pluginKey: string;
  panelName: string;
  targetModel: string;
  targetId?: string | number | null;
}): PluginPanelState {
  // TODO: Query to fetch the "content" for the plugin

  const [loaded, setLoaded] = useState<boolean>(false);

  const { start } = useTimeout(() => setLoaded(true), 5000);

  useEffect(() => {
    start();
    console.log('starting timer!');
  }, []);

  const content = useMemo(() => {
    return loaded ? (
      'plugin content loaded!'
    ) : (
      <div>
        <p>Plugin content goes here...</p>
        <p>Plugin Key: {pluginKey}</p>
        <p>Panel Name: {panelName}</p>
        <p>Target Model: {targetModel}</p>
        <p>Target ID: {targetId}</p>
      </div>
    );
  }, [loaded, pluginKey, panelName, targetModel, targetId]);

  return {
    content: content,
    name: panelName,
    pluginKey: pluginKey,
    targetType: targetModel,
    targetId: targetId,
    label: 'A plugin panel',
    icon: <Icon24Hours />
  };
}
