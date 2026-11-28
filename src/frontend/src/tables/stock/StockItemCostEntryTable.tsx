import { t } from '@lingui/core/macro';
import { Badge, Tooltip } from '@mantine/core';
import { IconFileUpload } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { ActionButton } from '@lib/components/ActionButton';
import { AddItemButton } from '@lib/components/AddItemButton';
import {
  type RowAction,
  RowDeleteAction,
  RowEditAction
} from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { RenderCostRange } from '../../components/render/Pricing';
import { StatusRenderer } from '../../components/render/StatusRenderer';
import {
  DateColumn,
  NoteColumn,
  UserColumn
} from '../../components/tables/ColumnRenderers';
import { StatusFilterOptions } from '../../components/tables/Filter';
import { InvenTreeTable } from '../../components/tables/InvenTreeTable';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
import {
  isCostRange,
  useStockItemCostEntryFields
} from '../../forms/PricingForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useImporterState } from '../../states/ImporterState';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';

// Name of the backend status class which defines the available cost types
const COST_TYPE_STATUS = 'CostType';

// Model type used for importing cost entries from a file
const COST_ENTRY_MODEL_TYPE = 'stockitemcostentry';

/**
 * Table displaying the cost entries for a single stock item.
 *
 * Requires the 'pricing' view role (the API also requires the 'stock' view role).
 * Adding, editing or removing entries requires the matching 'pricing' role permission,
 * plus the 'stock' change permission.
 */
export default function StockItemCostEntryTable({
  stockItem,
  onCostsChanged
}: Readonly<{
  stockItem: any;
  onCostsChanged?: () => void;
}>) {
  const user = useUserState();
  const table = useTable('stock-item-cost-entries');

  const [selectedEntry, setSelectedEntry] = useState<number | undefined>(
    undefined
  );

  const canChangeStock: boolean = useMemo(
    () => user.hasChangeRole(UserRoles.stock),
    [user]
  );

  // Note: Shared by the create and edit forms (only one is open at a time)
  const costEntryForm = useStockItemCostEntryFields({
    stockItemId: stockItem.pk
  });

  const onFormSuccess = useCallback(() => {
    table.refreshTable();
    onCostsChanged?.();
  }, [table, onCostsChanged]);

  const newCostEntry = useCreateApiFormModal({
    url: apiUrl(ApiEndpoints.stock_cost_entry_list),
    title: t`Add Item Cost`,
    fields: costEntryForm.fields,
    processFormData: costEntryForm.processFormData,
    onFormSuccess: onFormSuccess
  });

  const editCostEntry = useEditApiFormModal({
    url: apiUrl(ApiEndpoints.stock_cost_entry_list),
    pk: selectedEntry,
    title: t`Edit Item Cost`,
    fields: costEntryForm.fields,
    processFormData: costEntryForm.processFormData,
    onFormSuccess: onFormSuccess
  });

  const globalSettings = useGlobalSettingsState();
  const openImporter = useImporterState((state) => state.openImporter);

  // Import cost entries from a file - always against *this* stock item
  const importSessionFields = useMemo(() => {
    const fields = dataImporterSessionFields({
      modelType: COST_ENTRY_MODEL_TYPE
    });

    fields.field_overrides.value = {
      stock_item: stockItem.pk
    };

    fields.field_defaults.value = {
      currency:
        globalSettings.getSetting('INVENTREE_DEFAULT_CURRENCY') || undefined
    };

    return fields;
  }, [stockItem.pk, globalSettings]);

  const importCostEntries = useCreateApiFormModal({
    url: ApiEndpoints.import_session_list,
    title: t`Import Item Costs`,
    fields: importSessionFields,
    onFormSuccess: (response: any) => {
      openImporter(response.pk, {
        onClose: () => {
          table.refreshTable();
          onCostsChanged?.();
        }
      });
    }
  });

  const deleteCostEntry = useDeleteApiFormModal({
    url: apiUrl(ApiEndpoints.stock_cost_entry_list),
    pk: selectedEntry,
    title: t`Delete Item Cost`,
    onFormSuccess: onFormSuccess
  });

  const columns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'cost_type',
        title: t`Cost Type`,
        sortable: true,
        switchable: false,
        render: (record: any) => (
          <StatusRenderer status={record.cost_type} type={COST_TYPE_STATUS} />
        )
      },
      {
        accessor: 'min_cost',
        title: t`Unit Cost`,
        sortable: false,
        switchable: false,
        render: (record: any) => (
          <RenderCostRange
            minCost={record.min_cost}
            maxCost={record.max_cost}
            currency={record.currency}
          />
        )
      },
      {
        accessor: 'converted_min_cost',
        title: t`Converted Unit Cost`,
        sortable: true,
        render: (record: any) => {
          if (
            !record.converted_currency ||
            record.converted_min_cost == null ||
            record.converted_max_cost == null
          ) {
            return (
              <Tooltip
                label={t`This cost could not be converted to the default currency, and is not included in the total`}
              >
                <Badge color='orange' size='xs' variant='light'>
                  {t`Not converted`}
                </Badge>
              </Tooltip>
            );
          }

          return (
            <RenderCostRange
              minCost={record.converted_min_cost}
              maxCost={record.converted_max_cost}
              currency={record.converted_currency}
            />
          );
        }
      },
      {
        accessor: 'source',
        title: t`Source`,
        sortable: true,
        // Display the human readable label, with the stored value as a tooltip
        render: (record: any) => (
          <Tooltip label={record.source} openDelay={500}>
            <span>{record.source_text || record.source}</span>
          </Tooltip>
        )
      },
      NoteColumn({}),
      UserColumn({}),
      DateColumn({
        accessor: 'date',
        title: t`Last Updated`,
        sortable: true
      })
    ];
  }, []);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'cost_type',
        label: t`Cost Type`,
        description: t`Filter by cost type`,
        choiceFunction: StatusFilterOptions(COST_TYPE_STATUS)
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <ActionButton
        key='import-cost-entries'
        icon={<IconFileUpload />}
        tooltip={t`Import Costs`}
        onClick={() => importCostEntries.open()}
        // The importer requires 'change' permission for the pricing role
        hidden={
          !user.hasAddRole(UserRoles.pricing) ||
          !user.hasChangeRole(UserRoles.pricing) ||
          !canChangeStock
        }
      />,
      <AddItemButton
        key='add-cost-entry'
        tooltip={t`Add Cost`}
        onClick={() => {
          costEntryForm.setEstimate(false);
          newCostEntry.open();
        }}
        hidden={!user.hasAddRole(UserRoles.pricing) || !canChangeStock}
      />
    ];
  }, [user, canChangeStock, costEntryForm.setEstimate]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.pricing) || !canChangeStock,
          onClick: () => {
            // An entry with a range of costs is an estimate
            costEntryForm.setEstimate(isCostRange(record));
            setSelectedEntry(record.pk);
            editCostEntry.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.pricing) || !canChangeStock,
          onClick: () => {
            setSelectedEntry(record.pk);
            deleteCostEntry.open();
          }
        })
      ];
    },
    [user, canChangeStock, costEntryForm.setEstimate]
  );

  return (
    <>
      {importCostEntries.modal}
      {newCostEntry.modal}
      {editCostEntry.modal}
      {deleteCostEntry.modal}
      <InvenTreeTable
        tableState={table}
        url={apiUrl(ApiEndpoints.stock_cost_entry_list)}
        columns={columns}
        props={{
          params: {
            stock_item: stockItem.pk,
            user_detail: true
          },
          tableActions: tableActions,
          tableFilters: tableFilters,
          rowActions: rowActions,
          enableDownload: true
        }}
      />
    </>
  );
}
