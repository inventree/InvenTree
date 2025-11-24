import {
  AddItemButton,
  ApiEndpoints,
  type ModelType,
  RowDeleteAction,
  RowEditAction,
  YesNoButton,
  apiUrl,
  formatDecimal
} from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { useCallback, useMemo, useState } from 'react';
import { useParameterFields } from '../../forms/CommonForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import {
  DateColumn,
  DescriptionColumn,
  NoteColumn,
  UserColumn
} from '../ColumnRenderers';
import { UserFilter } from '../Filter';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

/**
 * Construct a table listing parameters
 */
export function ParameterTable({
  modelType,
  modelId
}: {
  modelType: ModelType;
  modelId: number;
}) {
  const table = useTable('parameters');
  const user = useUserState();

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'template_detail.name',
        switchable: false,
        sortable: true,
        ordering: 'name'
      },
      DescriptionColumn({
        accessor: 'template_detail.description'
      }),
      {
        accessor: 'data',
        switchable: false,
        sortable: true,
        render: (record) => {
          const template = record.template_detail;

          if (template?.checkbox) {
            return <YesNoButton value={record.data} />;
          }

          const extra: any[] = [];

          if (
            template.units &&
            record.data_numeric &&
            record.data_numeric != record.data
          ) {
            const numeric = formatDecimal(record.data_numeric, { digits: 15 });
            extra.push(`${numeric} [${template.units}]`);
          }

          return (
            <TableHoverCard
              value={record.data}
              extra={extra}
              title={t`Internal Units`}
            />
          );
        }
      },
      {
        accessor: 'template_detail.units',
        ordering: 'units',
        sortable: true
      },
      NoteColumn({}),
      DateColumn({
        accessor: 'updated',
        title: t`Last Updated`,
        sortable: true,
        switchable: true
      }),
      UserColumn({
        accessor: 'updated_by_detail',
        ordering: 'updated_by',
        title: t`Updated By`
      })
    ];
  }, [user]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'enabled',
        label: 'Enabled',
        description: t`Show parameters for enabled templates`,
        type: 'boolean'
      },
      UserFilter({
        name: 'updated_by',
        label: t`Updated By`,
        description: t`Filter by user who last updated the parameter`
      })
    ];
  }, []);

  const [selectedParameter, setSelectedParameter] = useState<any | undefined>(
    undefined
  );

  const newParameter = useCreateApiFormModal({
    url: ApiEndpoints.parameter_list,
    title: t`Add Parameter`,
    fields: useParameterFields({ modelType, modelId }),
    table: table
  });

  const editParameter = useEditApiFormModal({
    url: ApiEndpoints.parameter_list,
    pk: selectedParameter?.pk,
    title: t`Edit Parameter`,
    fields: useParameterFields({ modelType, modelId }),
    table: table
  });

  const deleteParameter = useDeleteApiFormModal({
    url: ApiEndpoints.parameter_list,
    pk: selectedParameter?.pk,
    title: t`Delete Parameter`,
    table: table
  });

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add-parameter'
        hidden={!user.hasAddPermission(modelType)}
        onClick={() => {
          setSelectedParameter(undefined);
          newParameter.open();
        }}
      />
    ];
  }, [user]);

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowEditAction({
          tooltip: t`Edit Parameter`,
          onClick: () => {
            setSelectedParameter(record);
            editParameter.open();
          },
          hidden: !user.hasChangePermission(modelType)
        }),
        RowDeleteAction({
          tooltip: t`Delete Parameter`,
          onClick: () => {
            setSelectedParameter(record);
            deleteParameter.open();
          },
          hidden: !user.hasDeletePermission(modelType)
        })
      ];
    },
    [user]
  );

  return (
    <>
      {newParameter.modal}
      {editParameter.modal}
      {deleteParameter.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.parameter_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableDownload: true,
          enableBulkDelete: true,
          enableSelection: true,
          rowActions: rowActions,
          tableActions: tableActions,
          tableFilters: tableFilters,
          params: {
            model_type: modelType,
            model_id: modelId
          }
        }}
      />
    </>
  );
}
