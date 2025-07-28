import { ActionButton } from '@lib/components/ActionButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { t } from '@lingui/core/macro';
import { IconTestPipe } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { DateColumn } from '../ColumnRenderers';
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
        accessor: 'subject',
        title: t`Subject`,
        sortable: true
      },
      {
        accessor: 'to',
        title: t`To`,
        sortable: true
      },
      {
        accessor: 'sender',
        title: t`Sender`,
        sortable: true
      },
      {
        accessor: 'status',
        title: t`Status`,
        sortable: true,
        render: (record: any) => {
          switch (record.status) {
            case 'A':
              return t`Announced`;
            case 'S':
              return t`Sent`;
            case 'F':
              return t`Failed`;
            case 'D':
              return t`Delivered`;
            case 'R':
              return t`Read`;
            case 'C':
              return t`Confirmed`;
          }
          return '-';
        },
        switchable: true
      },
      {
        accessor: 'direction',
        title: t`Direction`,
        sortable: true,
        render: (record: any) => {
          return record.direction === 'incoming' ? t`Incoming` : t`Outgoing`;
        },
        switchable: true
      },
      DateColumn({
        accessor: 'timestamp',
        title: t`Timestamp`,
        sortable: true,
        switchable: true
      })
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
          tableActions: tableActions
        }}
      />
    </>
  );
}
