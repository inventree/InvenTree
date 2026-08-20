import { AddItemButton } from '@lib/components/AddItemButton';
import { type RowAction, RowDeleteAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { Alert, Text } from '@mantine/core';
import { IconInfoCircle } from '@tabler/icons-react';
import { type ReactNode, useCallback, useMemo, useState } from 'react';
import { AttachmentLink } from '../../components/items/AttachmentLink';
import { DescriptionColumn } from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal
} from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';

export type AssetI = {
  pk: number;
  asset: string;
  description: string;
};

export default function AssetTable() {
  const table = useTable('report-asset');
  const user = useUserState();

  const columns: TableColumn<AssetI>[] = useMemo(() => {
    return [
      {
        accessor: 'asset',
        title: t`Asset`,
        sortable: false,
        switchable: false,
        render: (record: AssetI) => {
          if (!record.asset) {
            return '-';
          }

          return <AttachmentLink attachment={record.asset} />;
        },
        noContext: true
      },
      DescriptionColumn({
        accessor: 'description',
        sortable: false,
        switchable: false
      })
    ];
  }, []);

  const [selectedAsset, setSelectedAsset] = useState<number>(-1);

  const rowActions = useCallback(
    (record: AssetI): RowAction[] => {
      return [
        RowDeleteAction({
          hidden: !user.isStaff(),
          onClick: () => {
            setSelectedAsset(record.pk);
            deleteAsset.open();
          }
        })
      ];
    },
    [user]
  );

  const newAssetFields: ApiFormFieldSet = useMemo(() => {
    return {
      asset: {},
      description: {}
    };
  }, []);

  const deleteAsset = useDeleteApiFormModal({
    url: ApiEndpoints.report_asset,
    pk: selectedAsset,
    title: t`Delete Asset`,
    table: table
  });

  const newAsset = useCreateApiFormModal({
    url: ApiEndpoints.report_asset,
    title: t`Add Asset`,
    fields: newAssetFields,
    table: table
  });

  const tableActions: ReactNode[] = useMemo(() => {
    return [
      <AddItemButton
        key='add-asset'
        onClick={() => newAsset.open()}
        tooltip={t`Add asset`}
        hidden={!user.isStaff()}
      />
    ];
  }, [user]);

  return (
    <>
      {newAsset.modal}
      {deleteAsset.modal}
      <Alert icon={<IconInfoCircle />} title={t`Assets`}>
        <Text>{t`Assets are files (such as images) which can be used when rendering reports and labels.`}</Text>
      </Alert>
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.report_asset)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          enableSearch: false,
          enableFilters: false
        }}
      />
    </>
  );
}
