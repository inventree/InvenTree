import { useMemo } from 'react';

import { useGlobalSettingsState } from '../states/SettingsState';

/**
 * Simple hook for returning the "instance name" of the Server
 */
export default function useInstanceName(): string {
  const globalSettings = useGlobalSettingsState();

  return useMemo(() => {
    return globalSettings.getSetting('INVENTREE_INSTANCE', 'InvenTree');
  }, [globalSettings]);
}
