import { t } from '@lingui/macro';
import { IconRadar } from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { usePluginsWithMixin } from '../../hooks/UsePlugins';
import { apiUrl } from '../../states/ApiState';
import { ActionButton } from '../buttons/ActionButton';
import type { ApiFormFieldSet } from '../forms/fields/ApiFormField';
import type { PluginInterface } from './PluginInterface';

export default function LocateItemButton({
  stockId,
  locationId
}: Readonly<{
  stockId?: number;
  locationId?: number;
}>) {
  const locatePlugins = usePluginsWithMixin('locate');

  const [selectedPlugin, setSelectedPlugin] = useState<string | undefined>(
    undefined
  );

  useEffect(() => {
    // Ensure that the selected plugin is in the list of available plugins
    if (selectedPlugin && locatePlugins) {
      const plugin = locatePlugins.find(
        (plugin: PluginInterface) => plugin.key === selectedPlugin
      );
      if (!plugin) {
        setSelectedPlugin(undefined);
      }
    } else {
      setSelectedPlugin(locatePlugins[0]?.key ?? undefined);
    }
  }, [selectedPlugin, locatePlugins]);

  const locateFields: ApiFormFieldSet = useMemo(() => {
    return {
      plugin: {
        field_type: 'choice',
        value: selectedPlugin,
        onValueChange: (value: string) => {
          setSelectedPlugin(value);
        },
        choices: locatePlugins.map((plugin: PluginInterface) => {
          return {
            value: plugin.key,
            display_name: plugin.meta?.human_name ?? plugin.name
          };
        })
      },
      item: {
        hidden: true,
        value: stockId
      },
      location: {
        hidden: true,
        value: locationId
      }
    };
  }, [stockId, locationId, locatePlugins]);

  const locateForm = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.plugin_locate_item),
    method: 'POST',
    title: t`Locate Item`,
    fields: locateFields,
    successMessage: t`Item location requested`
  });

  if (!locatePlugins || locatePlugins.length === 0) {
    return null;
  }

  if (!stockId && !locationId) {
    return null;
  }

  return (
    <>
      {locateForm.modal}
      <ActionButton
        icon={<IconRadar />}
        variant='outline'
        size='lg'
        tooltip={t`Locate Item`}
        onClick={locateForm.open}
        tooltipAlignment='bottom'
      />
    </>
  );
}
