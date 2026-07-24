import {
  type RowAction,
  RowDuplicateAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import type { InvenTreeTableProps } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { IconShoppingCart } from '@tabler/icons-react';
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState
} from 'react';
import { ActionDropdown } from '../../components/items/ActionDropdown';
import { PartCreationMenu } from '../../components/items/PartCreationMenu';
import {
  BooleanColumn,
  CategoryColumn,
  DefaultLocationColumn,
  DescriptionColumn,
  IPNColumn,
  LinkColumn,
  PartColumn
} from '../../components/tables/ColumnRenderers';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { renderPartStockCell } from '../../components/tables/PartStockCell';
import OrderPartsWizard from '../../components/wizards/OrderPartsWizard';
import { formatPriceRange } from '../../defaults/formatters';
import { DuplicateField } from '../../forms/CommonFields';
import { usePartFields } from '../../forms/PartForms';
import { InvenTreeIcon } from '../../functions/icons';
import {
  useBulkEditApiFormModal,
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import { PartTableFilters } from './PartTableFilters';

/**
 * Construct a list of columns for the part table
 */
function partTableColumns(): TableColumn[] {
  return [
    PartColumn({
      part: '',
      accessor: 'name',
      filter: ['active', 'locked', 'starred']
    }),
    IPNColumn({
      accessor: 'IPN'
    }),
    {
      accessor: 'revision',
      sortable: true
    },
    {
      accessor: 'units',
      sortable: true,
      copyable: true,
      filter: 'has_units'
    },
    DescriptionColumn({}),
    CategoryColumn({
      accessor: 'category_detail'
    }),
    DefaultLocationColumn({
      accessor: 'default_location_detail'
    }),
    {
      accessor: 'total_in_stock',
      sortable: true,
      filter: ['has_stock', 'low_stock', 'high_stock'],
      render: renderPartStockCell
    },
    {
      accessor: 'price_range',
      title: t`Price Range`,
      sortable: true,
      ordering: 'pricing_max',
      filter: 'has_pricing',
      defaultVisible: false,
      render: (record: any) =>
        formatPriceRange(record.pricing_min, record.pricing_max)
    },
    BooleanColumn({
      accessor: 'assembly',
      defaultVisible: false
    }),
    BooleanColumn({
      accessor: 'virtual',
      defaultVisible: false
    }),
    BooleanColumn({
      accessor: 'consumable',
      defaultVisible: false
    }),
    LinkColumn({})
  ];
}

/**
 * PartListTable - Displays a list of parts, based on the provided parameters
 * @param {Object} params - The query parameters to pass to the API
 * @returns
 */
export function PartListTable({
  enableImport = true,
  basePartInstance,
  props,
  tableName = 'part-list',
  defaultPartData
}: Readonly<{
  enableImport?: boolean;
  props?: InvenTreeTableProps;
  basePartInstance?: any;
  tableName?: string;
  defaultPartData?: any;
}>) {
  const tableColumns = useMemo(() => partTableColumns(), []);

  const tableFilters = useMemo(() => PartTableFilters(), []);

  const table = useTable(tableName ?? 'part-list', {
    initialFilters: [
      {
        name: 'active',
        value: 'true'
      }
    ]
  });
  const user = useUserState();
  const globalSettings = useGlobalSettingsState();
  const refreshRef = useRef<() => void>(null!);

  useEffect(() => {
    refreshRef.current = table.refreshTable;
  }, [table.refreshTable]);

  const initialPartData = useMemo(() => {
    return defaultPartData ?? props?.params ?? {};
  }, [defaultPartData, props?.params]);

  const [selectedPart, setSelectedPart] = useState<any>({});

  const editPart = useEditApiFormModal({
    url: ApiEndpoints.part_list,
    pk: selectedPart.pk,
    title: t`Edit Part`,
    fields: usePartFields({ create: false }),
    onFormSuccess: table.refreshTable
  });

  const createPartFields = usePartFields({ create: true });

  const duplicatePartFields: ApiFormFieldSet = useMemo(() => {
    return {
      ...createPartFields,
      duplicate: DuplicateField({
        originalId: selectedPart.pk,
        extraFields: {
          copy_image: {
            value: true
          },
          copy_bom: {
            value:
              selectedPart.assembly && globalSettings.isSet('PART_COPY_BOM'),
            hidden: !selectedPart.assembly
          },
          copy_notes: {
            value: true
          },
          copy_parameters: {
            value: globalSettings.isSet('PART_COPY_PARAMETERS')
          },
          copy_tests: {
            value: selectedPart.testable,
            hidden: !selectedPart.testable
          }
        }
      })
    };
  }, [createPartFields, globalSettings, selectedPart]);

  const duplicatePart = useCreateApiFormModal({
    url: ApiEndpoints.part_list,
    title: t`Add Part`,
    fields: duplicatePartFields,
    initialData: {
      ...selectedPart,
      active: true,
      locked: false
    },
    follow: false,
    modelType: ModelType.part,
    onFormSuccess: table.refreshTable
  });

  const setCategory = useBulkEditApiFormModal({
    url: ApiEndpoints.part_list,
    items: table.selectedIds,
    title: t`Set Category`,
    fields: {
      category: {}
    },
    onFormSuccess: table.refreshTable
  });

  const orderPartsWizard = OrderPartsWizard({ parts: table.selectedRecords });

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      const can_edit = user.hasChangePermission(ModelType.part);
      const can_add = user.hasAddPermission(ModelType.part);

      return [
        RowEditAction({
          hidden: !can_edit,
          onClick: () => {
            setSelectedPart(record);
            editPart.open();
          }
        }),
        RowDuplicateAction({
          hidden: !can_add,
          onClick: () => {
            setSelectedPart(record);
            duplicatePart.open();
          }
        })
      ];
    },
    [user, editPart, duplicatePart]
  );

  const tableActions = useMemo(() => {
    return [
      <ActionDropdown
        tooltip={t`Part Actions`}
        icon={<InvenTreeIcon icon='part' />}
        disabled={!table.hasSelectedRecords}
        position='bottom-start'
        actions={[
          {
            name: t`Set Category`,
            icon: <InvenTreeIcon icon='category' />,
            tooltip: t`Set category for selected parts`,
            hidden: !user.hasChangeRole(UserRoles.part),
            disabled: !table.hasSelectedRecords,
            onClick: () => {
              setCategory.open();
            }
          },
          {
            name: t`Order Parts`,
            icon: <IconShoppingCart color='blue' />,
            tooltip: t`Order selected parts`,
            hidden: !user.hasAddRole(UserRoles.purchase_order),
            onClick: () => {
              orderPartsWizard.openWizard();
            }
          }
        ]}
      />,
      <PartCreationMenu
        key='part-creation-menu'
        initialData={initialPartData}
        basePartInstance={basePartInstance}
        enableImport={enableImport}
        refreshRef={refreshRef}
      />
    ];
  }, [user, enableImport, table.hasSelectedRecords]);

  return (
    <>
      {duplicatePart.modal}
      {editPart.modal}
      {setCategory.modal}
      {orderPartsWizard.wizard}
      <InvenTreeTable
        url={apiUrl(ApiEndpoints.part_list)}
        tableState={table}
        columns={tableColumns}
        props={{
          ...props,
          enableDownload: true,
          modelType: ModelType.part,
          tableFilters: tableFilters,
          tableActions: tableActions,
          rowActions: rowActions,
          enableSelection: true,
          enableReports: true,
          enableLabels: true,
          params: {
            ...props?.params,
            category_detail: true,
            location_detail: true
          }
        }}
      />
    </>
  );
}
