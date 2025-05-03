import { t } from '@lingui/core/macro';
import { Accordion } from '@mantine/core';

import { StylishText } from '../../../../components/items/StylishText';
import { ConfigValueList } from '../../../../components/settings/ConfigValueList';
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
          <ConfigValueList
            key='email_settings'
            keys={[
              'INVENTREE_EMAIL_BACKEND',
              'INVENTREE_EMAIL_HOST',
              'INVENTREE_EMAIL_PORT',
              'INVENTREE_EMAIL_USERNAME',
              'INVENTREE_EMAIL_PASSWORD',
              'INVENTREE_EMAIL_PREFIX',
              'INVENTREE_EMAIL_TLS',
              'INVENTREE_EMAIL_SSL',
              'INVENTREE_EMAIL_SENDER'
            ]}
          />
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
