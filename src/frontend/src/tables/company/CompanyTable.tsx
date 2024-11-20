import { t } from '@lingui/macro';
import { Group, Text } from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { Thumbnail } from '../../components/images/Thumbnail';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import { companyFields } from '../../forms/CompanyForms';
import { navigateToLink } from '../../functions/navigation';
import {
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { BooleanColumn, DescriptionColumn } from '../ColumnRenderers';
import type { TableFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowEditAction } from '../RowActions';

/**
 * A table which displays a list of company records,
 * based on the provided filter parameters
 */
export function CompanyTable({
  params,
  path
}: Readonly<{
  params?: any;
  path?: string;
}>) {
  const table = useTable('company');

  const navigate = useNavigate();
  const user = useUserState();

  const columns = useMemo(() => {
    return [
      {
        accessor: 'name',
        sortable: true,
        render: (record: any) => {
          return (
            <Group gap='xs' wrap='nowrap'>
              <Thumbnail
                src={record.thumbnail ?? record.image ?? ''}
                alt={record.name}
                size={24}
              />
              <Text>{record.name}</Text>
            </Group>
          );
        }
      },
      DescriptionColumn({}),
      BooleanColumn({
        accessor: 'active',
        title: t`Active`,
        sortable: true,
        switchable: true
      }),
      {
        accessor: 'website',
        sortable: false
      }
    ];
  }, []);

  const newCompany = useCreateApiFormModal({
    url: ApiEndpoints.company_list,
    title: t`Add Company`,
    fields: companyFields(),
    initialData: params,
    follow: true,
    modelType: ModelType.company
  });

  const [selectedCompany, setSelectedCompany] = useState<number>(0);

  const editCompany = useEditApiFormModal({
    url: ApiEndpoints.company_list,
    pk: selectedCompany,
    title: t`Edit Company`,
    fields: companyFields(),
    onFormSuccess: (record: any) => table.updateRecord(record)
  });

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'active',
        label: t`Active`,
        description: t`Show active companies`
      },
      {
        name: 'is_supplier',
        label: t`Supplier`,
        description: t`Show companies which are suppliers`
      },
      {
        name: 'is_manufacturer',
        label: t`Manufacturer`,
        description: t`Show companies which are manufacturers`
      },
      {
        name: 'is_customer',
        label: t`Customer`,
        description: t`Show companies which are customers`
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    const can_add =
      user.hasAddRole(UserRoles.purchase_order) ||
      user.hasAddRole(UserRoles.sales_order);

    return [
      <AddItemButton
        key='add-company'
        tooltip={t`Add Company`}
        onClick={() => newCompany.open()}
        hidden={!can_add}
      />
    ];
  }, [user]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden:
            !user.hasChangeRole(UserRoles.purchase_order) &&
            !user.hasChangeRole(UserRoles.sales_order),
          onClick: () => {
            setSelectedCompany(record.pk);
            editCompany.open();
          }
        })
      ];
    },
    [user]
  );

  return (
    <>
      {newCompany.modal}
      {editCompany.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.company_list)}
        tableState={table}
        columns={columns}
        props={{
          params: {
            ...params
          },
          onRowClick: (record: any, index: number, event: any) => {
            if (record.pk) {
              const base = path ?? 'company';
              navigateToLink(`/${base}/${record.pk}`, navigate, event);
            }
          },
          modelType: ModelType.company,
          tableFilters: tableFilters,
          tableActions: tableActions,
          enableDownload: true,
          rowActions: rowActions
        }}
      />
    </>
  );
}
