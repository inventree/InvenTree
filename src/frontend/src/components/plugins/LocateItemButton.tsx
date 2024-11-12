import { t } from '@lingui/macro';
import { IconRadar } from '@tabler/icons-react';
import { useCallback } from 'react';
import type { ModelType } from '../../enums/ModelType';
import { usePluginsWithMixin } from '../../hooks/UsePlugins';
import { ActionButton } from '../buttons/ActionButton';

export default function LocateItemButton({
  model,
  id
}: {
  model: ModelType;
  id?: number;
}) {
  const locatePlugins = usePluginsWithMixin('locate');

  const locateItem = useCallback(() => {
    // todo
  }, [locatePlugins]);

  if (!locatePlugins || locatePlugins.length === 0) {
    return null;
  }

  if (!id) {
    return null;
  }

  return (
    <ActionButton
      icon={<IconRadar />}
      variant='transparent'
      size='lg'
      tooltip={t`Locate Item`}
      onClick={locateItem}
      tooltipAlignment='bottom'
    />
  );
}
