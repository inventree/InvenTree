import {
  type RowAction,
  RowDuplicateAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import type { TableFilter } from '@lib/types/Filters';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import type { TableColumn } from '@lib/types/Tables';
import type { InvenTreeTableProps } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { Group, Text } from '@mantine/core';
import {
  IconFileUpload,
  IconPackageImport,
  IconPlus,
  IconShoppingCart
} from '@tabler/icons-react';
import { type ReactNode, useCallback, useMemo, useState } from 'react';
import ImporterDrawer from '../../components/importer/ImporterDrawer';
import { ActionDropdown } from '../../components/items/ActionDropdown';
import ImportPartWizard from '../../components/wizards/ImportPartWizard';
import OrderPartsWizard from '../../components/wizards/OrderPartsWizard';
import { formatDecimal, formatPriceRange } from '../../defaults/formatters';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
import { usePartFields } from '../../forms/PartForms';
import { InvenTreeIcon } from '../../functions/icons';
import {
  useBulkEditApiFormModal,
  useCreateApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { usePluginsWithMixin } from '../../hooks/UsePlugins';
import { useTable } from '../../hooks/UseTable';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import {
  CategoryColumn,
  DefaultLocationColumn,
  DescriptionColumn,
  LinkColumn,
  PartColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { TableHoverCard } from '../TableHoverCard';

/**
 * Construct a list of columns for the part table
 */
function partTableColumns(): TableColumn[] {
  return [
    PartColumn({
      part: '',
      accessor: 'name'
    }),
    {
      accessor: 'IPN',
      sortable: true
    },
    {
      accessor: 'revision',
      sortable: true
    },
    {
      accessor: 'units',
      sortable: true
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

      render: (record) => {
        const extra: ReactNode[] = [];

        const stock = record?.total_in_stock ?? 0;
        const allocated =
          (record?.allocated_to_build_orders ?? 0) +
          (record?.allocated_to_sales_orders ?? 0);
        const available = Math.max(0, stock - allocated);
        const min_stock = record?.minimum_stock ?? 0;

        let text = String(formatDecimal(stock));

        let color: string | undefined = undefined;

        if (min_stock > stock) {
          extra.push(
            <Text key='min-stock' c='orange'>
              {`${t`Minimum stock`}: ${formatDecimal(min_stock)}`}
            </Text>
          );

          color = 'orange';
        }

        if (record.ordering > 0) {
          extra.push(
            <Text key='on-order'>{`${t`On Order`}: ${formatDecimal(record.ordering)}`}</Text>
          );
        }

        if (record.building) {
          extra.push(
            <Text key='building'>{`${t`Building`}: ${formatDecimal(record.building)}`}</Text>
          );
        }

        if (record.allocated_to_build_orders > 0) {
          extra.push(
            <Text key='bo-allocations'>
              {`${t`Build Order Allocations`}: ${formatDecimal(record.allocated_to_build_orders)}`}
            </Text>
          );
        }

        if (record.allocated_to_sales_orders > 0) {
          extra.push(
            <Text key='so-allocations'>
              {`${t`Sales Order Allocations`}: ${formatDecimal(record.allocated_to_sales_orders)}`}
            </Text>
          );
        }

        if (available != stock) {
          extra.push(
            <Text key='available'>
              {t`Available`}: {formatDecimal(available)}
            </Text>
          );
        }

        if (record.external_stock > 0) {
          extra.push(
            <Text key='external'>
              {t`External stock`}: {formatDecimal(record.external_stock)}
            </Text>
          );
        }

        if (stock <= 0) {
          color = 'red';
          text = t`No stock`;
        } else if (available <= 0) {
          color = 'orange';
        } else if (available < min_stock) {
          color = 'yellow';
        }

        return (
          <TableHoverCard
            value={
              <Group gap='xs' justify='left' wrap='nowrap'>
                <Text c={color}>{text}</Text>
                {record.units && (
                  <Text size='xs' c={color}>
                    [{record.units}]
                  </Text>
                )}
              </Group>
            }
            title={t`Stock Information`}
            extra={extra}
          />
        );
      }
    },
    {
      accessor: 'price_range',
      title: t`Price Range`,
      sortable: true,
      ordering: 'pricing_max',
      defaultVisible: false,
      render: (record: any) =>
        formatPriceRange(record.pricing_min, record.pricing_max)
    },
    LinkColumn({})
  ];
}

/**
 * Construct a set of filters for the part table
 */
function partTableFilters(): TableFilter[] {
  return [
    {
      name: 'active',
      label: t`Active`,
      description: t`Filter by part active status`,
      type: 'boolean'
    },
    {
      name: 'locked',
      label: t`Locked`,
      description: t`Filter by part locked status`,
      type: 'boolean'
    },
    {
      name: 'assembly',
      label: t`Assembly`,
      description: t`Filter by assembly attribute`,
      type: 'boolean'
    },
    {
      name: 'bom_valid',
      label: t`BOM Valid`,
      description: t`Filter by parts with a valid BOM`,
      type: 'boolean'
    },
    {
      name: 'cascade',
      label: t`Include Subcategories`,
      description: t`Include parts in subcategories`,
      type: 'boolean'
    },
    {
      name: 'component',
      label: t`Component`,
      description: t`Filter by component attribute`,
      type: 'boolean'
    },
    {
      name: 'testable',
      label: t`Testable`,
      description: t`Filter by testable attribute`,
      type: 'boolean'
    },
    {
      name: 'trackable',
      label: t`Trackable`,
      description: t`Filter by trackable attribute`,
      type: 'boolean'
    },
    {
      name: 'has_units',
      label: t`Has Units`,
      description: t`Filter by parts which have units`,
      type: 'boolean'
    },
    {
      name: 'has_ipn',
      label: t`Has IPN`,
      description: t`Filter by parts which have an internal part number`,
      type: 'boolean'
    },
    {
      name: 'has_stock',
      label: t`Has Stock`,
      description: t`Filter by parts which have stock`,
      type: 'boolean'
    },
    {
      name: 'low_stock',
      label: t`Low Stock`,
      description: t`Filter by parts which have low stock`,
      type: 'boolean'
    },
    {
      name: 'purchaseable',
      label: t`Purchaseable`,
      description: t`Filter by parts which are purchaseable`,
      type: 'boolean'
    },
    {
      name: 'salable',
      label: t`Salable`,
      description: t`Filter by parts which are salable`,
      type: 'boolean'
    },
    {
      name: 'virtual',
      label: t`Virtual`,
      description: t`Filter by parts which are virtual`,
      type: 'choice',
      choices: [
        { value: 'true', label: t`Virtual` },
        { value: 'false', label: t`Not Virtual` }
      ]
    },
    {
      name: 'is_template',
      label: t`Is Template`,
      description: t`Filter by parts which are templates`,
      type: 'boolean'
    },
    {
      name: 'is_variant',
      label: t`Is Variant`,
      description: t`Filter by parts which are variants`,
      type: 'boolean'
    },
    {
      name: 'is_revision',
      label: t`Is Revision`,
      description: t`Filter by parts which are revisions`
    },
    {
      name: 'has_revisions',
      label: t`Has Revisions`,
      description: t`Filter by parts which have revisions`
    },
    {
      name: 'has_pricing',
      label: t`Has Pricing`,
      description: t`Filter by parts which have pricing information`,
      type: 'boolean'
    },
    {
      name: 'unallocated_stock',
      label: t`Available Stock`,
      description: t`Filter by parts which have available stock`,
      type: 'boolean'
    },
    {
      name: 'starred',
      label: t`Subscribed`,
      description: t`Filter by parts to which the user is subscribed`,
      type: 'boolean'
    }
  ];
}

/**
 * PartListTable - Displays a list of parts, based on the provided parameters
 * @param {Object} params - The query parameters to pass to the API
 * @returns
 */
export function PartListTable({
  enableImport = true,
  props,
  defaultPartData
}: Readonly<{
  enableImport?: boolean;
  props?: InvenTreeTableProps;
  defaultPartData?: any;
}>) {
  const tableColumns = useMemo(() => partTableColumns(), []);
  const tableFilters = useMemo(() => partTableFilters(), []);

  const table = useTable('part-list');
  const user = useUserState();
  const globalSettings = useGlobalSettingsState();

  const [importOpened, setImportOpened] = useState<boolean>(false);

  const [selectedSession, setSelectedSession] = useState<number | undefined>(
    undefined
  );

  const importSessionFields = useMemo(() => {
    const fields = dataImporterSessionFields({
      modelType: ModelType.part
    });

    // Override default field values with provided fields
    fields.field_defaults.value = props?.params ?? {};

    return fields;
  }, [props?.params]);

  const importParts = useCreateApiFormModal({
    url: ApiEndpoints.import_session_list,
    title: t`Import Parts`,
    fields: importSessionFields,
    onFormSuccess: (response: any) => {
      setSelectedSession(response.pk);
      setImportOpened(true);
    }
  });

  const initialPartData = useMemo(() => {
    return defaultPartData ?? props?.params ?? {};
  }, [defaultPartData, props?.params]);

  const newPart = useCreateApiFormModal({
    url: ApiEndpoints.part_list,
    title: t`Add Part`,
    fields: usePartFields({ create: true }),
    initialData: initialPartData,
    follow: true,
    modelType: ModelType.part
  });

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
      duplicate: {
        children: {
          part: {
            value: selectedPart.pk,
            hidden: true
          },
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
      }
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

  const supplierPlugins = usePluginsWithMixin('supplier');
  const importPartWizard = ImportPartWizard({
    categoryId: initialPartData.category
  });

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
      <ActionDropdown
        key='add-parts-actions'
        tooltip={t`Add Parts`}
        position='bottom-start'
        icon={<IconPlus />}
        hidden={!user.hasAddRole(UserRoles.part)}
        actions={[
          {
            name: t`Create Part`,
            icon: <IconPlus />,
            tooltip: t`Create a new part`,
            onClick: () => newPart.open()
          },
          {
            name: t`Import from File`,
            icon: <IconFileUpload />,
            tooltip: t`Import parts from a file`,
            onClick: () => importParts.open(),
            hidden: !enableImport
          },
          {
            name: t`Import from Supplier`,
            icon: <IconPackageImport />,
            tooltip: t`Import parts from a supplier plugin`,
            hidden: !enableImport || supplierPlugins.length === 0,
            onClick: () => importPartWizard.openWizard()
          }
        ]}
      />
    ];
  }, [user, enableImport, table.hasSelectedRecords, supplierPlugins]);

  return (
    <>
      {newPart.modal}
      {duplicatePart.modal}
      {editPart.modal}
      {setCategory.modal}
      {importParts.modal}
      {orderPartsWizard.wizard}
      {importPartWizard.wizard}
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
      <ImporterDrawer
        sessionId={selectedSession ?? -1}
        opened={selectedSession != undefined && importOpened}
        onClose={() => {
          setSelectedSession(undefined);
          setImportOpened(false);
          table.refreshTable();
        }}
      />
    </>
  );
}
