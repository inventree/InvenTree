import { t } from '@lingui/core/macro';
import { Accordion } from '@mantine/core';

import { StylishText } from '../../../../components/items/StylishText';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { EmailTable } from '../../../../tables/settings/EmailTable';

export default function UserManagementPanel() {
  return (
    <Accordion multiple defaultValue={['emails']}>
      <Accordion.Item value='emails' key='emails'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Email Messages`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <EmailTable />
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value='settings' key='settings'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Settings`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <GlobalSettingList
            keys={['LOGIN_ENABLE_REG', 'SIGNUP_GROUP', 'LOGIN_ENABLE_SSO_REG']}
          />
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
