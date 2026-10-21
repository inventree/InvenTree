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
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ActionDropdown } from '../../components/items/ActionDropdown';
import { PartCreationMenu } from '../../components/items/PartCreationMenu';
import {
  BooleanColumn,
  CategoryColumn,
  DecimalColumn,
  DefaultLocationColumn,
  DescriptionColumn,
  IPNColumn,
  LinkColumn,
  PartColumn
} from '../../components/tables/ColumnRenderers';
import { Badge } from '@mantine/core';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { renderPartStockCell } from '../../components/tables/PartStockCell';
import OrderPartsWizard from '../../components/wizards/OrderPartsWizard';
import { formatCurrency, formatPriceRange } from '../../defaults/formatters';
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
    DecimalColumn({
      accessor: 'ordering',
      title: t`On Order`,
      filter: 'on_order',
      sortable: true,
      defaultVisible: false
    }),
    {
      accessor: 'cost',
      title: t`Cost`,
      sortable: true,
      ordering: 'pricing_min',
      defaultVisible: true,
      render: (record: any) => {
        const cost =
          record.cost ??
          record.metadata?.cost ??
          record.pricing_min ??
          null;
        const currency =
          record.cost_currency ??
          record.metadata?.cost_currency ??
          record.pricing_data?.currency;
        return cost != null && cost !== ''
          ? formatCurrency(cost, { currency })
          : '-';
      }
    },
    {
      accessor: 'desired_margin',
      title: t`Margin`,
      sortable: true,
      defaultVisible: true,
      render: (record: any) => {
        let margin =
          record.desired_margin ??
          record.metadata?.desired_margin ??
          null;

        const cost = Number(
          record.cost ??
            record.metadata?.cost ??
            record.pricing_min ??
            0
        );

        let price =
          record.selling_price ??
          record.metadata?.selling_price ??
          null;

        if (
          (price == null || price === 0) &&
          cost > 0 &&
          margin != null &&
          Number(margin) < 100
        ) {
          price = cost / (1 - Number(margin) / 100);
        }

        if (margin == null && cost > 0 && price != null && Number(price) > 0) {
          margin = ((Number(price) - cost) / Number(price)) * 100;
        }

        if (margin == null || isNaN(Number(margin))) {
          return '-';
        }

        const marginVal = Number(margin);
        const color =
          marginVal >= 30
            ? 'teal'
            : marginVal >= 15
            ? 'blue'
            : marginVal > 0
            ? 'yellow'
            : 'red';

        return (
          <Badge color={color} variant='light' size='sm'>
            {marginVal.toFixed(1)}%
          </Badge>
        );
      }
    },
    {
      accessor: 'selling_price',
      title: t`Selling Price`,
      sortable: true,
      ordering: 'pricing_max',
      defaultVisible: true,
      render: (record: any) => {
        const cost = Number(
          record.cost ??
            record.metadata?.cost ??
            record.pricing_min ??
            0
        );
        const margin =
          record.desired_margin ??
          record.metadata?.desired_margin ??
          null;

        let price =
          record.selling_price ??
          record.metadata?.selling_price ??
          null;

        if (
          (price == null || price === 0) &&
          cost > 0 &&
          margin != null &&
          Number(margin) < 100
        ) {
          price = cost / (1 - Number(margin) / 100);
        }

        const currency =
          record.selling_price_currency ??
          record.metadata?.selling_price_currency ??
          record.pricing_data?.currency;

        return price != null && Number(price) > 0
          ? formatCurrency(price, { currency })
          : '-';
      }
    },
    {
      accessor: 'minimum_price',
      title: t`Minimum Price`,
      sortable: true,
      defaultVisible: false,
      render: (record: any) => {
        const price = record.minimum_price ?? null;
        const currency =
          record.minimum_price_currency ??
          record.pricing_data?.currency;
        return price != null && Number(price) > 0
          ? formatCurrency(price, { currency })
          : '-';
      }
    },
    {
      accessor: 'new_cost',
      title: t`New Cost`,
      sortable: true,
      defaultVisible: false,
      render: (record: any) => {
        const cost = record.new_cost ?? null;
        const currency = record.new_cost_currency ?? record.pricing_data?.currency;
        return cost != null && cost !== ''
          ? formatCurrency(cost, { currency })
          : '-';
      }
    },
    {
      accessor: 'customer_part_number',
      title: t`Customer Part Number`,
      sortable: true,
      switchable: true,
      defaultVisible: false
    },
    {
      accessor: 'weight',
      title: t`Weight`,
      sortable: true,
      switchable: true,
      defaultVisible: false,
      render: (record: any) =>
        record.weight ? `${record.weight} ${record.weight_unit || ''}`.trim() : '-'
    },
    {
      accessor: 'volume',
      title: t`Volume`,
      sortable: true,
      switchable: true,
      defaultVisible: false,
      render: (record: any) =>
        record.volume ? `${record.volume} ${record.volume_unit || ''}`.trim() : '-'
    },
    {
      accessor: 'warranty',
      title: t`Warranty`,
      sortable: true,
      switchable: true,
      defaultVisible: false
    },
    BooleanColumn({
      accessor: 'is_taxable',
      title: t`Taxable`,
      switchable: true,
      defaultVisible: false
    }),
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
    onFormSuccess: table.refreshTable,
    size: '95%'
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
