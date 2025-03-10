import { t } from '@lingui/macro';
import { Accordion } from '@mantine/core';

import { StylishText } from '../../../../components/items/StylishText';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { GroupTable } from '../../../../tables/settings/GroupTable';
import { UserTable } from '../../../../tables/settings/UserTable';

export default function UserManagementPanel() {
  return (
    <>
      <Accordion multiple defaultValue={['users']}>
        <Accordion.Item value='users' key='users'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Users`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <UserTable />
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value='groups' key='groups'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Groups`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <GroupTable />
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value='settings' key='settings'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Settings`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <GlobalSettingList
              keys={[
                'LOGIN_ENABLE_REG',
                'SIGNUP_GROUP',
                'LOGIN_ENABLE_SSO_REG'
              ]}
            />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </>
  );
}
