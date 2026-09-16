import { t } from '@lingui/core/macro';
import { Accordion, Alert, Card, Stack, Text } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import { useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';

import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { useInstance } from '../../hooks/UseInstance';
import { InfoItem } from '../items/InfoItem';
import { PluginSettingList } from '../settings/SettingList';
import type { PluginInterface } from './PluginInterface';
import PluginSettingsPanel from './PluginSettingsPanel';

/**
 * Displays a drawer with detailed information on a specific plugin
 */
export default function PluginDrawer({
  pluginKey,
  onPluginLoaded
}: Readonly<{
  pluginKey: string;
  onPluginLoaded?: (plugin: PluginInterface) => void;
}>) {
  const { id } = useParams();

  const pluginPrimaryKey: string = useMemo(() => {
    return pluginKey || id || '';
  }, [pluginKey, id]);

  const {
    instance: plugin,
    instanceQuery: { isFetching, error }
  } = useInstance<PluginInterface>({
    endpoint: ApiEndpoints.plugin_list,
    hasPrimaryKey: true,
    pk: pluginPrimaryKey
  });

  const { instance: pluginAdmin } = useInstance({
    endpoint: ApiEndpoints.plugin_admin,
    pathParams: { key: pluginPrimaryKey },
    defaultValue: {},
    hasPrimaryKey: false,
    refetchOnMount: true
  });

  useEffect(() => {
    if (plugin) {
      onPluginLoaded?.(plugin);
    }
  }, [plugin, onPluginLoaded]);

  const hasSettings: boolean = useMemo(() => {
    return !!plugin?.mixins?.settings;
  }, [plugin]);

  if (isFetching || !plugin) {
    return null;
  }

  if (!plugin.active) {
    return (
      <Alert
        color='red'
        title={t`Plugin Inactive`}
        icon={<IconExclamationCircle />}
      >
        <Text>{t`Plugin is not active`}</Text>
      </Alert>
    );
  }

  return (
    <Accordion defaultValue={['plugin-details', 'plugin-settings']} multiple>
      <Accordion.Item value='plugin-details'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Plugin Information`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <Stack gap='xs'>
            <Card withBorder>
              <Stack gap='md'>
                <Stack pos='relative' gap='xs'>
                  <InfoItem type='text' name={t`Name`} value={plugin?.name} />
                  <InfoItem
                    type='text'
                    name={t`Description`}
                    value={plugin?.meta.description}
                  />
                  <InfoItem
                    type='text'
                    name={t`Author`}
                    value={plugin?.meta.author}
                  />
                  <InfoItem
                    type='text'
                    name={t`Date`}
                    value={plugin?.meta.pub_date}
                  />
                  <InfoItem
                    type='text'
                    name={t`Version`}
                    value={plugin?.meta.version}
                  />
                  <InfoItem
                    type='boolean'
                    name={t`Active`}
                    value={plugin?.active}
                  />
                  {plugin?.meta.website && (
                    <InfoItem
                      type='text'
                      name={t`Website`}
                      value={plugin?.meta.website}
                      link={plugin?.meta.website}
                    />
                  )}
                </Stack>
              </Stack>
            </Card>
            <Card withBorder>
              <Stack gap='md'>
                <Stack pos='relative' gap='xs'>
                  {plugin?.is_package && (
                    <InfoItem
                      type='text'
                      name={t`Package Name`}
                      value={plugin?.package_name}
                    />
                  )}
                  <InfoItem
                    type='text'
                    name={t`Installation Path`}
                    value={plugin?.meta.package_path}
                  />
                  <InfoItem
                    type='boolean'
                    name={t`Builtin`}
                    value={plugin?.is_builtin}
                  />
                  <InfoItem
                    type='boolean'
                    name={t`Package`}
                    value={plugin?.is_package}
                  />
                </Stack>
              </Stack>
            </Card>
          </Stack>
        </Accordion.Panel>
      </Accordion.Item>
      {hasSettings && (
        <Accordion.Item value='plugin-settings'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Plugin Settings`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <Card withBorder>
              <PluginSettingList pluginKey={pluginPrimaryKey} />
            </Card>
          </Accordion.Panel>
        </Accordion.Item>
      )}
      {pluginAdmin?.source && (
        <Accordion.Item value='plugin-custom'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Plugin Configuration`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <Card withBorder>
              <PluginSettingsPanel pluginAdmin={pluginAdmin} />
            </Card>
          </Accordion.Panel>
        </Accordion.Item>
      )}
    </Accordion>
  );
}
