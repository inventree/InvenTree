import {
  Tabs,
} from '@mantine/core';
import { useNavigate, useParams } from 'react-router-dom';
import { StylishText } from '../../../components/items/StylishText';
import { Trans, t } from '@lingui/macro'
import { UserPanel } from './UserPanel';
import { SettingsPanel } from './SettingsPanel';


export function Profile() {
  const navigate = useNavigate();
  const { tabValue } = useParams();

  return (
    <>
      <StylishText><Trans>Profile</Trans></StylishText>
      <Tabs
        value={tabValue}
        onTabChange={(value) => navigate(`/profile/${value}`)}
      >
        <Tabs.List>
          <Tabs.Tab value="user"><Trans>User</Trans></Tabs.Tab>
          <Tabs.Tab value="user-settings"><Trans>User Settings</Trans></Tabs.Tab>
          <Tabs.Tab value="notification-settings"><Trans>Notification Settings</Trans></Tabs.Tab>
          <Tabs.Tab value="global-settings"><Trans>Global Settings</Trans></Tabs.Tab>
          <Tabs.Tab value="plugin-settings"><Trans>Plugin Settings</Trans></Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="user">
          <UserPanel />
        </Tabs.Panel>
        <Tabs.Panel value="user-settings">
          <SettingsPanel reference='user' title={t`User Settings`} description={t`Settings for the current user`} />
        </Tabs.Panel>
        <Tabs.Panel value="notification-settings">
          <SettingsPanel reference='notification' title={t`Notification Settings`} description={t`Settings for the notifications`} />
        </Tabs.Panel>
        <Tabs.Panel value="global-settings">
          <SettingsPanel reference='global'
            title={t`Global Server Settings`}
            description={t`Global Settings for this instance`}
            sections={[
              { key: 'abc', name: 'ABC', description: 'ABC description' },
              { key: 'a1', name: 'A1', description: 'ABC description' },
              { key: 'a2', name: 'A2', description: 'ABC description' },
              { key: 'a2', name: 'A3', description: 'ABC description' },
            ]}
          />
        </Tabs.Panel>
        <Tabs.Panel value="plugin-settings">
          <SettingsPanel reference='plugin' title={t`Plugin Settings`} description={t`Plugin Settings for this instance`} url='plugin/settings/' />
        </Tabs.Panel>
      </Tabs>
    </>
  );
}
