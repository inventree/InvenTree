import { ActionButton } from '@lib/components/ActionButton';
import { RowDeleteAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { t } from '@lingui/core/macro';
import { Badge } from '@mantine/core';
import { IconTestPipe } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
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

  const user = useUserState();

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

  const table = useTable('emails', 'pk');

  const [selectedEmailId, setSelectedEmailId] = useState<string>('');

  const deleteEmail = useDeleteApiFormModal({
    url: ApiEndpoints.email_list,
    pk: selectedEmailId,
    title: t`Delete Email`,
    successMessage: t`Email deleted successfully`,
    table: table
  });

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
              return <Badge color='blue'>{t`Announced`}</Badge>;
            case 'S':
              return <Badge color='blue'>{t`Sent`}</Badge>;
            case 'F':
              return <Badge color='red'>{t`Failed`}</Badge>;
            case 'D':
              return <Badge color='green'>{t`Delivered`}</Badge>;
            case 'R':
              return <Badge color='green'>{t`Read`}</Badge>;
            case 'C':
              return <Badge color='green'>{t`Confirmed`}</Badge>;
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
        switchable: true,
        extra: { showTime: true }
      })
    ];
  }, []);

  const rowactions = useCallback(
    (record: any) => {
      return [
        RowDeleteAction({
          onClick: () => {
            setSelectedEmailId(record.pk);
            deleteEmail.open();
          },
          hidden: !user.isStaff()
        })
      ];
    },
    [user]
  );

  return (
    <>
      {sendTestMail.modal}
      {deleteEmail.modal}
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.email_list)}
        columns={tableColumns}
        props={{
          rowActions: rowactions,
          enableSearch: true,
          enableColumnSwitching: true,
          enableSelection: true,
          enableBulkDelete: true,
          tableActions: tableActions
        }}
      />
    </>
  );
}
