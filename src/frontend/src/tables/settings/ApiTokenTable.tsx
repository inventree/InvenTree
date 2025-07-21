import type { RowAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Badge, Code, Flex, Modal, Paper, Text } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconCircleX } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { api } from '../../App';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { CopyButton } from '../../components/buttons/CopyButton';
import { StylishText } from '../../components/items/StylishText';
import { RenderUser } from '../../components/render/User';
import { showApiErrorMessage } from '../../functions/notifications';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { BooleanColumn } from '../ColumnRenderers';
import { UserFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';

export function ApiTokenTable({
  only_myself = true
}: Readonly<{ only_myself: boolean }>) {
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
    if (only_myself)
      return [
        <AddItemButton
          key={'generate'}
          tooltip={t`Generate Token`}
          onClick={() => generateToken.open()}
        />
      ];
    return [];
  }, [only_myself]);

  const table = useTable('api-tokens', 'id');

  const tableColumns = useMemo(() => {
    const cols = [
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
    if (!only_myself) {
      cols.push({
        accessor: 'user',
        title: t`User`,
        sortable: true,
        render: (record: any) => {
          if (record.user_detail) {
            return <RenderUser instance={record.user_detail} />;
          } else {
            return record.user;
          }
        }
      });
    }
    return cols;
  }, [only_myself]);

  const tableFilters: TableFilter[] = useMemo(() => {
    const filters: TableFilter[] = [
      {
        name: 'revoked',
        label: t`Revoked`,
        description: t`Show revoked tokens`
      }
    ];

    if (!only_myself) {
      filters.push(
        UserFilter({
          name: 'user',
          label: t`User`,
          description: t`Filter by user`
        })
      );
    }
    return filters;
  }, [only_myself]);

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
    let targetUrl = apiUrl(ApiEndpoints.user_tokens, id);
    if (!only_myself) {
      targetUrl += '?all_users=true';
    }
    api
      .delete(targetUrl)
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

  const urlParams = useMemo(() => {
    if (only_myself) return {};
    return { all_users: true };
  }, [only_myself]);

  return (
    <>
      {only_myself && (
        <>
          {generateToken.modal}
          <Modal
            opened={opened}
            onClose={close}
            title={<StylishText size='xl'>{t`Token`}</StylishText>}
            centered
          >
            <Text c='dimmed'>
              <Trans>
                Tokens are only shown once - make sure to note it down.
              </Trans>
            </Text>
            <Paper p='sm'>
              <Flex>
                <Code>{token}</Code>
                <CopyButton value={token} />
              </Flex>
            </Paper>
          </Modal>
        </>
      )}
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.user_tokens)}
        columns={tableColumns}
        props={{
          params: urlParams,
          rowActions: rowActions,
          enableSearch: false,
          enableColumnSwitching: false,
          tableActions: tableActions,
          tableFilters: tableFilters
        }}
      />
    </>
  );
}
