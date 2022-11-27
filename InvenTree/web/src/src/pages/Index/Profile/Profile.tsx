import {
  Tabs,
} from '@mantine/core';
import { useNavigate, useParams } from 'react-router-dom';
import { StylishText } from '../../../components/items/StylishText';
import { Trans } from '@lingui/macro'
import { UserPanel } from './UserPanel';
import { SettingsPanel } from './SettingsPanel';


export function Profile() {
  const navigate = useNavigate();
  const { tabValue } = useParams();

  return (
    <>
      <StylishText><Trans>Profile</Trans></StylishText>
      <Tabs
        orientation="vertical"
        value={tabValue}
        onTabChange={(value) => navigate(`/profile/${value}`)}
      >
        <Tabs.List>
          <Tabs.Tab value="user"><Trans>User</Trans></Tabs.Tab>
          <Tabs.Tab value="settings"><Trans>Settings</Trans></Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="user">
          <UserPanel />
        </Tabs.Panel>
        <Tabs.Panel value="settings">
          <SettingsPanel />
        </Tabs.Panel>
      </Tabs>
    </>
  );
}
