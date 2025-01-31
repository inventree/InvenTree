import { Trans, t } from '@lingui/macro';
import { Accordion, Alert, Stack } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { lazy } from 'react';

import { StylishText } from '../../../../components/items/StylishText';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { Loadable } from '../../../../functions/loading';
import { useServerApiState } from '../../../../states/ApiState';
import { useUserState } from '../../../../states/UserState';

const PluginListTable = Loadable(
  lazy(() => import('../../../../tables/plugin/PluginListTable'))
);

const PluginErrorTable = Loadable(
  lazy(() => import('../../../../tables/plugin/PluginErrorTable'))
);

export default function PluginManagementPanel() {
  const pluginsEnabled = useServerApiState(
    (state) => state.server.plugins_enabled
  );

  const user = useUserState();

  return (
    <Stack>
      {!pluginsEnabled && (
        <Alert
          title={<Trans>Info</Trans>}
          icon={<IconInfoCircle />}
          color='blue'
        >
          <Trans>
            External plugins are not enabled for this InvenTree installation.
          </Trans>
        </Alert>
      )}

      <Accordion defaultValue='pluginlist'>
        <Accordion.Item value='pluginlist'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Plugins`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <PluginListTable />
          </Accordion.Panel>
        </Accordion.Item>

        <Accordion.Item value='pluginsettings'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Plugin Settings`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <GlobalSettingList
              keys={[
                'ENABLE_PLUGINS_SCHEDULE',
                'ENABLE_PLUGINS_EVENTS',
                'ENABLE_PLUGINS_INTERFACE',
                'ENABLE_PLUGINS_URL',
                'ENABLE_PLUGINS_NAVIGATION',
                'ENABLE_PLUGINS_APP',
                'PLUGIN_ON_STARTUP',
                'PLUGIN_UPDATE_CHECK'
              ]}
            />
          </Accordion.Panel>
        </Accordion.Item>
        {user.isSuperuser() && (
          <Accordion.Item value='pluginerror'>
            <Accordion.Control>
              <StylishText size='lg'>{t`Plugin Errors`}</StylishText>
            </Accordion.Control>
            <Accordion.Panel>
              <PluginErrorTable />
            </Accordion.Panel>
          </Accordion.Item>
        )}
      </Accordion>
    </Stack>
  );
}
