import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '@lib/components/AddItemButton';
import { RowDeleteAction, RowEditAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { RowAction, TableColumn } from '@lib/types/Tables';
import { taxConfigurationFields } from '../../forms/TaxForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { BooleanColumn } from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';

/**
 * Table for displaying list of tax configurations
 */
export default function TaxConfigurationTable() {
  const table = useTable('tax-configurations');

  const user = useUserState();

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true,
        title: t`Name`
      },
      {
        accessor: 'year',
        sortable: true,
        title: t`Year`
      },
      {
        accessor: 'rate',
        sortable: true,
        title: t`Rate (%)`,
        render: (record: any) => `${record.rate}%`
      },
      {
        accessor: 'currency',
        sortable: true,
        title: t`Currency`
      },
      BooleanColumn({
        accessor: 'is_active',
        title: t`Active`
      }),
      BooleanColumn({
        accessor: 'is_inclusive',
        title: t`Inclusive`
      }),
      BooleanColumn({
        accessor: 'applies_to_sales',
        title: t`Sales`
      }),
      BooleanColumn({
        accessor: 'applies_to_purchases',
        title: t`Purchases`
      })
    ];
  }, []);

  const newTaxConfiguration = useCreateApiFormModal({
    url: ApiEndpoints.tax_configuration_list,
    title: t`Add Tax Configuration`,
    fields: taxConfigurationFields(),
    table: table
  });

  const [selectedTaxConfiguration, setSelectedTaxConfiguration] = useState<
    number | undefined
  >(undefined);

  const editTaxConfiguration = useEditApiFormModal({
    url: ApiEndpoints.tax_configuration_list,
    pk: selectedTaxConfiguration,
    title: t`Edit Tax Configuration`,
    fields: taxConfigurationFields(),
    table: table
  });

  const deleteTaxConfiguration = useDeleteApiFormModal({
    url: ApiEndpoints.tax_configuration_list,
    pk: selectedTaxConfiguration,
    title: t`Delete Tax Configuration`,
    table: table
  });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.admin),
          onClick: () => {
            setSelectedTaxConfiguration(record.pk);
            editTaxConfiguration.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.admin),
          onClick: () => {
            setSelectedTaxConfiguration(record.pk);
            deleteTaxConfiguration.open();
          }
        })
      ];
    },
    [user, editTaxConfiguration, deleteTaxConfiguration]
  );

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add'
        onClick={() => newTaxConfiguration.open()}
        tooltip={t`Add tax configuration`}
        hidden={!user.hasAddRole(UserRoles.admin)}
      />
    ];
  }, [user, newTaxConfiguration]);

  return (
    <>
      {newTaxConfiguration.modal}
      {editTaxConfiguration.modal}
      {deleteTaxConfiguration.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.tax_configuration_list)}
        tableState={table}
        columns={columns}
        props={{
          rowActions: rowActions,
          tableActions: tableActions,
          enableSelection: true,
          enableSearch: true,
          enableFilters: true,
          enablePagination: true,
          enableColumnSwitching: true
        }}
      />
    </>
  );
}
