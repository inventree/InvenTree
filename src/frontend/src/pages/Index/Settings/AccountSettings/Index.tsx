import { Trans } from '@lingui/macro';
import { Tabs } from '@mantine/core';
import { useNavigate, useParams } from 'react-router-dom';

import { StylishText } from '../../../../components/items/StylishText';
import { AccountContent } from './UserPanel';

export default function AccountSettings() {
  const navigate = useNavigate();
  const { tabValue } = useParams();

  return (
    <>
      <StylishText>
        <Trans>Profile</Trans>
      </StylishText>
      <Tabs
        value={tabValue}
        onTabChange={(value) => navigate(`/profile/${value}`)}
      >
        <Tabs.List>
          <Tabs.Tab value="user">
            <Trans>User</Trans>
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="user">
          <AccountContent />
        </Tabs.Panel>
      </Tabs>
    </>
  );
}
