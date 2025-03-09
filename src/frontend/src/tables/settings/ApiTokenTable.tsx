import { Trans, t } from '@lingui/macro';
import { Badge, Code, Modal, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconCircleX } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { api } from '../../App';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { showApiErrorMessage } from '../../functions/notifications';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import type { RowAction } from '../../tables/RowActions';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

export function ApiTokenTable({
  only_myself = true
}: { only_myself: boolean }) {
  const [token, setToken] = useState<string>('');
  const [opened, { open, close }] = useDisclosure(false);

  const generateToken = useCreateApiFormModal({
    url: ApiEndpoints.user_tokens,
    title: t`Generate Token`,
    fields: { name: {} },
    successMessage: t`Token generated`,
    onFormSuccess: (data: any) => {
      setToken(data.token);
      open();
      table.refreshTable();
    }
  });
  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        tooltip={t`Generate Token`}
        onClick={() => generateToken.open()}
      />
    ];
  }, []);

  const table = useTable('api-tokens', 'id');

  const tableColumns = useMemo(() => {
    return [
      {
        accessor: 'name',
        title: t`Name`
      },
      BooleanColumn({
        accessor: 'active',
        title: t`Active`
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
        title: t`Last Seen`
      },
      {
        accessor: 'expiry',
        title: t`Expiry`
      },
      {
        accessor: 'created',
        title: t`Created`
      }
    ];
  }, []);

  const rowActions = useCallback((record: any): RowAction[] => {
    return [
      {
        title: t`Revoke`,
        color: 'red',
        hidden: !record.active || record.in_use,
        icon: <IconCircleX />,
        onClick: () => {
          revokeToken(record.id);
        }
      }
    ];
  }, []);

  const revokeToken = async (id: string) => {
    api
      .delete(apiUrl(ApiEndpoints.user_tokens, id))
      .then(() => {
        table.refreshTable();
      })
      .catch((error) => {
        showApiErrorMessage({
          error: error,
          title: t`Error revoking token`
        });
      });
  };

  return (
    <>
      {generateToken.modal}
      <Modal opened={opened} onClose={close} title={t`Token`} centered>
        <Text c='dimmed'>
          <Trans>Tokens are only shown once - make sure to note it down.</Trans>
        </Text>
        <Code>{token}</Code>
      </Modal>
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.user_tokens)}
        columns={tableColumns}
        props={{
          rowActions: rowActions,
          enableSearch: false,
          enableColumnSwitching: false,
          tableActions: tableActions
        }}
      />
    </>
  );
}
