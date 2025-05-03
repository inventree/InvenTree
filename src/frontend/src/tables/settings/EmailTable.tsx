import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Badge } from '@mantine/core';
import { IconTestPipe } from '@tabler/icons-react';
import { useMemo } from 'react';
import { ActionButton } from '../../components/buttons/ActionButton';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export function EmailTable() {
  const sendTestMail = useCreateApiFormModal({
    url: ApiEndpoints.email_test,
    title: t`Send Test Email`,
    fields: { email: {} },
    successMessage: t`Email sent successfully`,
    onFormSuccess: (data: any) => {
      table.refreshTable();
    }
  });

  const tableActions = useMemo(() => {
    return [
      <ActionButton
        icon={<IconTestPipe />}
        key={'test'}
        tooltip={t`Send Test Email`}
        onClick={() => sendTestMail.open()}
      />
    ];
  }, []);

  const table = useTable('emails', 'id');

  const tableColumns = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`,
        sortable: true
      },
      BooleanColumn({
        accessor: 'active',
        title: t`Active`,
        sortable: false
      }),
      BooleanColumn({
        accessor: 'revoked',
        title: t`Revoked`
      }),
      {
        accessor: 'token',
        title: t`Token`,
        render: (record: any) => {
          return (
            <>
              {record.token}{' '}
              {record.in_use ? (
                <Badge color='green'>
                  <Trans>In Use</Trans>
                </Badge>
              ) : null}
            </>
          );
        }
      },
      {
        accessor: 'last_seen',
        title: t`Last Seen`,
        sortable: true
      },
      {
        accessor: 'expiry',
        title: t`Expiry`,
        sortable: true
      },
      {
        accessor: 'created',
        title: t`Created`,
        sortable: true
      }
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'revoked',
        label: t`Revoked`,
        description: t`Show revoked tokens`
      }
    ];
  }, []);

  return (
    <>
      {sendTestMail.modal}
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.email_list)}
        columns={tableColumns}
        props={{
          enableSearch: true,
          enableColumnSwitching: true,
          tableActions: tableActions,
          tableFilters: tableFilters
        }}
      />
    </>
  );
}
