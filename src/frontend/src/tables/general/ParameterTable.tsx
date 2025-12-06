import {
  ApiEndpoints,
  ModelType,
  RowDeleteAction,
  RowEditAction,
  YesNoButton,
  apiUrl,
  formatDecimal
} from '@lib/index';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { IconFileUpload, IconPlus } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import ImporterDrawer from '../../components/importer/ImporterDrawer';
import { ActionDropdown } from '../../components/items/ActionDropdown';
import { useParameterFields } from '../../forms/CommonForms';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
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
  modelId,
  allowEdit = true
}: {
  modelType: ModelType;
  modelId: number;
  allowEdit?: boolean;
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

  const [importOpened, setImportOpened] = useState<boolean>(false);

  const [selectedSession, setSelectedSession] = useState<number | undefined>(
    undefined
  );

  const importSessionFields = useMemo(() => {
    const fields = dataImporterSessionFields({
      modelType: ModelType.parameter
    });

    fields.field_overrides.value = {
      model_type: modelType,
      model_id: modelId
    };

    return fields;
  }, [modelType, modelId]);

  const importParameters = useCreateApiFormModal({
    url: ApiEndpoints.import_session_list,
    title: t`Import Parameters`,
    fields: importSessionFields,
    onFormSuccess: (response: any) => {
      setSelectedSession(response.pk);
      setImportOpened(true);
    }
  });

  const newParameter = useCreateApiFormModal({
    url: ApiEndpoints.parameter_list,
    title: t`Add Parameter`,
    fields: useParameterFields({ modelType, modelId }),
    initialData: {
      data: ''
    },
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
      <ActionDropdown
        key='add-parameter-actions'
        tooltip={t`Add Parameters`}
        position='bottom-start'
        icon={<IconPlus />}
        hidden={!user.hasAddPermission(modelType)}
        actions={[
          {
            name: t`Create Parameter`,
            icon: <IconPlus />,
            tooltip: t`Create a new parameter`,
            onClick: () => {
              setSelectedParameter(undefined);
              newParameter.open();
            }
          },
          {
            name: t`Import from File`,
            icon: <IconFileUpload />,
            tooltip: t`Import parameters from a file`,
            onClick: () => {
              importParameters.open();
            }
          }
        ]}
      />
    ];
  }, [allowEdit, user]);

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
      {importParameters.modal}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.parameter_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          enableDownload: true,
          enableBulkDelete: allowEdit != false,
          enableSelection: allowEdit != false,
          rowActions: allowEdit == false ? undefined : rowActions,
          tableActions: allowEdit == false ? undefined : tableActions,
          tableFilters: tableFilters,
          params: {
            model_type: modelType,
            model_id: modelId
          }
        }}
      />
      <ImporterDrawer
        sessionId={selectedSession ?? -1}
        opened={selectedSession !== undefined && importOpened}
        onClose={() => {
          setSelectedSession(undefined);
          setImportOpened(false);
          table.refreshTable();
        }}
      />
    </>
  );
}
