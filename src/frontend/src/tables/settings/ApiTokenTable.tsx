import { AddItemButton } from '@lib/components/AddItemButton';
import { CopyButton } from '@lib/components/CopyButton';
import type { RowAction } from '@lib/components/RowActions';
import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Badge,
  Button,
  Code,
  Flex,
  Group,
  Modal,
  Paper,
  Text,
  Textarea
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconCircleX } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { api } from '../../App';
import {
  BooleanColumn,
  UserColumn
} from '../../components/tables/ColumnRenderers';
import { UserFilter } from '../../components/tables/Filter';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { showApiErrorMessage } from '../../functions/notifications';
import { useCreateApiFormModal } from '../../hooks/UseForm';

export function ApiTokenTable({
  only_myself = true
}: Readonly<{ only_myself: boolean }>) {
  const [token, setToken] = useState<string>('');
  const [opened, { open, close }] = useDisclosure(false);
  const [revokeTokenId, setRevokeTokenId] = useState<string | null>(null);
  const [revocationReason, setRevocationReason] = useState<string>('');

  const generateToken = useCreateApiFormModal({
    url: ApiEndpoints.user_me_token,
    method: 'GET',
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

  const table = useTable('api-tokens', { idAccessor: 'id' });

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
      },
      UserColumn({
        accessor: 'issued_by_detail',
        title: t`Issued By`,
        filtering: true,
        sortable: true
      }),
      UserColumn({
        accessor: 'revoked_by_detail',
        title: t`Revoked By`,
        filtering: true,
        sortable: true
      }),
      {
        accessor: 'token_version',
        sortable: true
      },
      {
        accessor: 'revocation_reason',
        sortable: false
      }
    ];
    if (!only_myself) {
      cols.push(
        UserColumn({
          accessor: 'user_detail',
          ordering: 'user',
          title: t`User`
        })
      );
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
        }),
        UserFilter({
          name: 'issued_by',
          label: t`Issued By`
        }),
        UserFilter({
          name: 'revoked_by',
          label: t`Revoked By`
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
          setRevokeTokenId(record.id);
        }
      }
    ];
  }, []);

  const revokeToken = async () => {
    if (!revokeTokenId) return;

    let targetUrl = apiUrl(ApiEndpoints.user_tokens, revokeTokenId);
    if (!only_myself) {
      targetUrl += '?all_users=true';
    }
    api
      .delete(targetUrl, { data: { revocation_reason: revocationReason } })
      .then(() => {
        table.refreshTable();
        setRevokeTokenId(null);
        setRevocationReason('');
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
            data-testid='generated-api-token'
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
      <Modal
        opened={revokeTokenId !== null}
        onClose={() => {
          setRevokeTokenId(null);
          setRevocationReason('');
        }}
        title={t`Revoke Token`}
        centered
      >
        <Textarea
          label={t`Revocation Reason`}
          placeholder={t`Enter a reason for revoking this token`}
          value={revocationReason}
          onChange={(event) => setRevocationReason(event.currentTarget.value)}
          autosize
          minRows={3}
        />
        <Group justify='flex-end' mt='md'>
          <Button
            variant='default'
            onClick={() => {
              setRevokeTokenId(null);
              setRevocationReason('');
            }}
          >
            {t`Cancel`}
          </Button>
          <Button color='red' onClick={revokeToken}>
            {t`Revoke`}
          </Button>
        </Group>
      </Modal>
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
