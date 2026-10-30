import { t } from '@lingui/core/macro';
import { Accordion, Alert, Stack } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';

import { StylishText } from '@lib/components/StylishText';
import { GlobalSettingList } from '../../../../components/settings/SettingList';
import { useGlobalSettingsState } from '../../../../states/SettingsStates';
import { AuditLogTable } from '../../../../tables/general/AuditLogTable';

export default function AuditLogManagementPanel() {
  const globalSettings = useGlobalSettingsState();

  return (
    <Stack gap='xs'>
      {!globalSettings.isSet('AUDIT_LOG_ENABLED', true) && (
        <Alert
          color='yellow'
          icon={<IconInfoCircle />}
          title={t`Audit Log Disabled`}
        >
          {t`Changes are not currently being recorded in the audit log`}
        </Alert>
      )}
      <Accordion multiple defaultValue={['auditlog']}>
        <Accordion.Item value='auditlog'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Audit Log`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <AuditLogTable />
          </Accordion.Panel>
        </Accordion.Item>
        <Accordion.Item value='settings'>
          <Accordion.Control>
            <StylishText size='lg'>{t`Audit Log Settings`}</StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <GlobalSettingList
              keys={[
                'AUDIT_LOG_ENABLED',
                'AUDIT_LOG_DELETE_OLD_ENTRIES',
                'AUDIT_LOG_DELETE_DAYS',
                'AUDIT_LOG_DELETE_KEEP_SUMMARY'
              ]}
            />
          </Accordion.Panel>
        </Accordion.Item>
      </Accordion>
    </Stack>
  );
}
