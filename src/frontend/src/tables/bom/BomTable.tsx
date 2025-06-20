import { Alert, Group, Stack, Text, Switch, Tooltip, Loader, Center, Modal, Checkbox, Button } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import {
  IconArrowRight,
  IconCircleCheck,
  IconFileArrowLeft,
  IconLock,
  IconSwitch3,
  IconListTree,
  IconDownload
} from '@tabler/icons-react';
import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { t } from '@lingui/core/macro';
import { useLingui } from '@lingui/react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { navigateToLink } from '@lib/functions/Navigation';
import type { TableFilter } from '@lib/types/Filters';
import { ActionButton } from '../../components/buttons/ActionButton';
import { AddItemButton } from '../../components/buttons/AddItemButton';
import { YesNoButton } from '../../components/buttons/YesNoButton';
import { Thumbnail } from '../../components/images/Thumbnail';
import ImporterDrawer from '../../components/importer/ImporterDrawer';
import { RenderPart } from '../../components/render/Part';
import { useApi } from '../../contexts/ApiContext';
import { formatDecimal, formatPriceRange } from '../../defaults/formatters';
import { bomItemFields, useEditBomSubstitutesForm } from '../../forms/BomForms';
import { dataImporterSessionFields } from '../../forms/ImporterForms';
import {
  useApiFormModal,
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../Column';
import {
  BooleanColumn,
  DescriptionColumn,
  NoteColumn,
  ReferenceColumn
} from '../ColumnRenderers';
import { InvenTreeTable } from '../InvenTreeTable';
import { type RowAction, RowDeleteAction, RowEditAction } from '../RowActions';
import { TableHoverCard } from '../TableHoverCard';
import { ex } from '@fullcalendar/core/internal-common';

interface BomItem {
  pk: number;
  part: number;
  sub_part: number;
  quantity: number;
  reference: string;
  note: string;
  optional: boolean;
  consumable: boolean;
  allow_variants: boolean;
  inherited: boolean;
  validated: boolean;
  available_stock: number;
  available_substitute_stock: number;
  available_variant_stock: number;
  on_order: number;
  building: number;
  can_build: number;
  substitutes: any[];
  sub_part_detail: any;
  part_detail?: any;
  level?: number;
  parent_name?: string;
  total_quantity?: number;
  [key: string]: any;
}

function calculateTotalStock(record: any): number {
  let totalStock = record.available_stock || 0;
  
  totalStock += record?.available_substitute_stock ?? 0;

  if (record.allow_variants) {
    totalStock += record?.available_variant_stock ?? 0;
  }

  return totalStock;
}

export function BomTable({
  partId,
  partLocked,
  params = {}
}: Readonly<{
  partId: number;
  partLocked?: boolean;
  params?: any;
}>) {
  const api = useApi();
  const table = useTable('bom');
  const user = useUserState();
  const navigate = useNavigate();
  const { _, i18n } = useLingui();

  const [importOpened, setImportOpened] = useState<boolean>(false);
  const [selectedSession, setSelectedSession] = useState<number | undefined>(undefined);
  const [showFlat, setShowFlat] = useState<boolean>(false);
  const [flatItems, setFlatItems] = useState<BomItem[]>([]);
  const [directBomItems, setDirectBomItems] = useState<BomItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [exportModal, setExportModal] = useState<boolean>(false);
  const [selectedBomItem, setSelectedBomItem] = useState<any>({});
  const [consolidateExport, setConsolidateExport] = useState<boolean>(false); // AJOUT : Variable manquante
  
  const [selectedColumns, setSelectedColumns] = useState<string[]>([
    'sub_part_detail.full_name',
    'quantity',
    'available_stock'
  ]);

  const availableColumns = useMemo(() => [
    { key: 'sub_part_detail.full_name', label: t`Part Name` },
    { key: 'sub_part_detail.IPN', label: t`Internal Reference` },
    { key: 'sub_part_detail.description', label: t`Description` },
    { key: 'reference', label: t`Reference` },
    { key: 'quantity', label: t`Quantity` },
    { key: 'total_quantity', label: t`Total Quantity` },
    { key: 'sub_part_detail.units', label: t`Units` },
    { key: 'available_stock', label: t`Available Stock` },
    { key: 'on_order', label: t`On Order` },
    { key: 'can_build', label: t`Can Build` },
    { key: 'optional', label: t`Optional` },
    { key: 'consumable', label: t`Consumable` },
    { key: 'validated', label: t`Validated` },
    { key: 'note', label: t`Note` }
  ], []);

  const loadCompleteHierarchy = useCallback(async () => {
    if (!showFlat) return;
    
    console.log('Loading complete BOM for part:', partId);
    setLoading(true);
    
    try {
      const response = await api.get(apiUrl(ApiEndpoints.bom_list), {
        params: {
          part: partId,
          part_detail: true,
          sub_part_detail: true,
          include_pricing: true
        }
      });
      
      const directItems = response.data.results || response.data;
      let allItems = [...directItems];
      allItems = allItems.map(item => ({
        ...item, 
        level: 0, 
        total_quantity: item.quantity
      }));
    
      const processSubAssemblies = async (items: BomItem[], currentLevel: number, parentQuantity: number) => {
        for (const item of items) {
          if (item.sub_part_detail?.assembly) {
            try {
              const childResponse = await api.get(apiUrl(ApiEndpoints.bom_list), { 
                params: {
                  part: item.sub_part,
                  part_detail: true,
                  sub_part_detail: true,
                  include_pricing: true
                }
              });
              
              const children = childResponse.data.results || childResponse.data;
              
              for (const child of children) {
                const totalQuantity = parentQuantity * child.quantity;
                
                const childItem = {
                  ...child,
                  level: currentLevel + 1,
                  parent_name: item.sub_part_detail?.full_name || `Part #${item.sub_part}`,
                  total_quantity: totalQuantity
                };
                
                allItems.push(childItem);
                
                if (child.sub_part_detail?.assembly) {
                  await processSubAssemblies([child], currentLevel + 1, totalQuantity);
                }
              }
            } catch (err) {
              console.log('Error loading sub-components:', err);
            }
          }
        }
      };
      
      await processSubAssemblies(directItems, 0, 1);
      setFlatItems(allItems);
      
    } catch (error) {
      console.error('Error loading BOM:', error);
      showNotification({
        title: _(t`Error`),
        message: _(t`Failed to load BOM data`),
        color: 'red'
      });
    }
    
    setLoading(false);
  }, [api, partId, showFlat, _]);

  const loadDirectItems = useCallback(async () => {
    try {
      const response = await api.get(apiUrl(ApiEndpoints.bom_list), { 
        params: {
          part: partId,
          part_detail: true,
          sub_part_detail: true,
          include_pricing: true
        }
      });
      
      const directItems = response.data.results || response.data;
      setDirectBomItems(directItems);
    } catch (error) {
      console.error('Failed to load direct BOM:', error);
      setDirectBomItems([]);
    }
  }, [api, partId]);

  useEffect(() => {
    if (showFlat) {
      loadCompleteHierarchy();
    } else {
      setFlatItems([]);
      loadDirectItems();
    }
  }, [showFlat, loadCompleteHierarchy, loadDirectItems]);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'sub_part',
        switchable: false,
        sortable: true,
        render: (record: { [key: string]: any }) => {
          const part = record.sub_part_detail;
          const extraInfo: ReactNode[] = [];
          
          let indentation = null;
          if (showFlat && record.level && record.level > 0) {
            indentation = (
              <Group>
                <Text ml={record.level * 20} span c="dimmed">
                  {'│'.repeat(record.level - 1)}
                  {'└─ '}
                </Text>
                <Text size="xs" c="dimmed" style={{ fontStyle: 'italic' }}>
                  {record.parent_name ? `(via ${record.parent_name})` : ''}
                </Text>
              </Group>
            );
          }
          
          if (record.part != partId) {
            extraInfo.push(
              <Text key='different-parent'>{t`This item is defined for a parent: ${record.parent_name || `Unknown`}`}</Text>
            );
          }

          return (
            part && (
              <TableHoverCard
                value={
                  <Stack ml={2}>
                    {indentation}
                    <Group>
                      <Thumbnail
                        src={part.thumbnail || part.image}
                        alt={part.description}
                        text={part.full_name}
                      />
                    </Group>
                  </Stack>
                }
                extra={extraInfo}
                title={t`Part Information`}
              />
            )
          );
        }
      },
      {
        accessor: 'sub_part_detail.IPN',
        title: t`Reference`,
        sortable: true
      },
      DescriptionColumn({
        accessor: 'sub_part_detail.description'
      }),
      ReferenceColumn({
        switchable: true
      }),
      {
        accessor: 'quantity',
        switchable: false,
        sortable: true,
        render: (record: any) => {
          const quantity = formatDecimal(record.quantity);
          const units = record.sub_part_detail?.units;
          
          const totalQuantityDisplay = showFlat && 
                            record.total_quantity !== undefined && 
                            record.total_quantity !== record.quantity ? 
            <Text size="xs" c="dimmed">{t`Total: ${(record.total_quantity)}`}</Text> : null;

          return (
            <Group justify='space-between' grow>
              <Text>{quantity}</Text>
              {totalQuantityDisplay}
              {record.overage && <Text size='xs'>+{record.overage}</Text>}
              {units && <Text size='xs'>{units}</Text>}
            </Group>
          );
        }
      },
      {
        accessor: 'substitutes',
        render: (row) => {
          const substitutes = row.substitutes ?? [];

          return substitutes.length > 0 ? (
            <TableHoverCard
              value={<Text>{substitutes.length}</Text>}
              title={t`Substituts`}
              extra={substitutes.map((sub: any) => (
                <RenderPart instance={sub.part_detail} />
              ))}
            />
          ) : (
            <YesNoButton value={false} />
          );
        }
      },
      BooleanColumn({
        accessor: 'optional'
      }),
      BooleanColumn({
        accessor: 'consumable'
      }),
      BooleanColumn({
        accessor: 'allow_variants'
      }),
      BooleanColumn({
        accessor: 'inherited',
        render: (record) => {
          if (showFlat && record.level && record.level > 0) {
            return <YesNoButton value={true} />;
          }
          return <YesNoButton value={record.inherited} />;
        }
      }),
      BooleanColumn({
        accessor: 'validated'
      }),
      {
        accessor: 'price_range',
        title: t`Unit Price`,
        ordering: 'pricing_max',
        sortable: true,
        switchable: true,
        render: (record: any) =>
          formatPriceRange(record.pricing_min, record.pricing_max)
      },
      {
        accessor: 'total_price',
        title: t`Total Price`,
        ordering: 'pricing_max_total',
        sortable: true,
        switchable: true,
        render: (record: any) =>
          formatPriceRange(record.pricing_min_total, record.pricing_max_total)
      },
      {
        accessor: 'available_stock',
        sortable: true,
        render: (record: { [key: string]: any }) => {
          const extraInfo: ReactNode[] = [];
          const availableStock: number = calculateTotalStock(record);
          const onOrder: number = record?.on_order ?? 0;
          const building: number = record?.building ?? 0;

          // Affichage du stock avec style conditionnel
          const stockDisplay = availableStock <= 0 ? (
              <Text c='red' style={{ fontStyle: 'italic' }}>
                {t`No stock`}
              </Text>
            ) : (
              availableStock
            );

          // Informations supplémentaires sur le stock
          if (record.external_stock > 0) {
            extraInfo.push(
              <Text key='external'>
                {t`External stock`}: {record.external_stock}
              </Text>
            );
          }

          if (record.available_substitute_stock > 0) {
            extraInfo.push(
              <Text key='substitute'>
                {t`Includes substitute stock`}: {record.available_substitute_stock}
              </Text>
            );
          }

          if (record.allow_variants && record.available_variant_stock > 0) {
            extraInfo.push(
              <Text key='variant'>
                {t`Includes variant stock`}: {record.available_variant_stock}
              </Text>
            );
          }

          if (onOrder > 0) {
            extraInfo.push(
              <Text key='on_order'>
                {t`On order`}: {onOrder}
              </Text>
            );
          }

          if (building > 0) {
            extraInfo.push(
              <Text key='building'>
                {t`In production`}: {building}
              </Text>
            );
          }

          return (
            <TableHoverCard
              value={stockDisplay}
              extra={extraInfo}
              title={t`Stock Information`}
            />
          );
        }
      },
      {
        accessor: 'can_build',
        title: t`Can Build`,
        sortable: true,
        render: (record: any) => {
          if (record.can_build === null || record.can_build === undefined) {
            return '-';
          }

          if (!Number.isFinite(record.can_build) || Number.isNaN(record.can_build)) {
            return '-';
          }

          const canBuild = Math.trunc(record.can_build);
          const value = (
            <Text
              fs={record.consumable && 'italic'}
              c={canBuild <= 0 && !record.consumable ? 'red' : undefined}
            >
              {canBuild}
            </Text>
          );

          const extraInfo: ReactNode[] = [];

          if (record.consumable) {
            extraInfo.push(
              <Text key='consumable'>{t`Consumable item`}</Text>
            );
          } else if (canBuild <= 0) {
            extraInfo.push(
              <Text key='no-build' c='red'>
                {t`No stock available`}
              </Text>
            );
          }

          return (
            <TableHoverCard
              value={value}
              extra={extraInfo}
              title={_(t`Can Build`)}
            />
          );
        }
      },
      NoteColumn({})
    ];
  }, [partId, params, showFlat, _]);

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'sub_part_testable',
        label: t`Testable Part`,
        description: t`Show testable items`
      },
      {
        name: 'sub_part_trackable',
        label: t`Trackable Part`,
        description: t`Show trackable items`
      },
      {
        name: 'sub_part_assembly',
        label: t`Assembled Part`,
        description: t`Show assembled items`
      },
      {
        name: 'available_stock',
        label: t`Available Stock`,
        description: t`Show items with available stock`
      },
      {
        name: 'on_order',
        label: t`On Order`,
        description: t`Show items on order`
      },
      {
        name: 'validated',
        label: t`Validated`,
        description: t`Show validated items`
      },
      {
        name: 'inherited',
        label: t`Inherited`,
        description: t`Show inherited items`
      },
      {
        name: 'allow_variants',
        label: t`Allow Variants`,
        description: t`Show items that allow variant substitution`
      },
      {
        name: 'optional',
        label: t`Optional`,
        description: t`Show optional items`
      },
      {
        name: 'consumable',
        label: t`Consumable`,
        description: t`Show consumable items`
      },
      {
        name: 'has_pricing',
        label: t`Has Pricing`,
        description: t`Show items with pricing`
      }
    ];
  }, [partId, params, i18n]);

  const importSessionFields = useMemo(() => {
    const fields = dataImporterSessionFields();
    fields.model_type.hidden = true;
    fields.model_type.value = 'bomitem';
    fields.field_overrides.value = {
      part: partId
    };
    return fields;
  }, [partId]);

  const importBomItem = useCreateApiFormModal({
    url: ApiEndpoints.import_session_list,
    title: t`Import BOM Data`,
    fields: importSessionFields,
    onFormSuccess: (response: any) => {
      setSelectedSession(response.pk);
      setImportOpened(true);
    }
  });

  const newBomItem = useCreateApiFormModal({
    url: ApiEndpoints.bom_list,
    title: t`Add BOM Item`,
    fields: bomItemFields(),
    initialData: {
      part: partId
    },
    successMessage: t`BOM Item Created`,
    table: table
  });

  const editBomItem = useEditApiFormModal({
    url: ApiEndpoints.bom_list,
    pk: selectedBomItem.pk,
    title: t`Edit BOM Item`,
    fields: bomItemFields(),
    successMessage: t`BOM Item Updated`,
    table: table
  });

  const deleteBomItem = useDeleteApiFormModal({
    url: ApiEndpoints.bom_list,
    pk: selectedBomItem.pk,
    title: t`Delete BOM Item`,
    successMessage: t`BOM Item Deleted`,
    table: table
  });

  const editSubstitutes = useEditBomSubstitutesForm({
    bomItemId: selectedBomItem.pk,
    substitutes: selectedBomItem?.substitutes ?? [],
    onClose: () => {
      table.refreshTable();
    }
  });

  const validateBom = useApiFormModal({
    url: ApiEndpoints.bom_validate,
    method: 'PUT',
    fields: {
      valid: {
        hidden: true,
        value: true
      }
    },
    title: t`Validate BOM`,
    pk: partId,
    preFormContent: (
      <Alert color='green' icon={<IconCircleCheck />} title={t`Validate BOM`}>
        <Text>{t`Are you sure you want to validate the BOM for this assembly?`}</Text>
      </Alert>
    ),
    successMessage: t`BOM Validated`,
    onFormSuccess: () => table.refreshTable()
  });

  const validateSingleItem = useCallback((record: any) => {
    const url = apiUrl(ApiEndpoints.bom_item_validate, record.pk);

    api
      .patch(url, { valid: true })
      .then((_response) => {
        showNotification({
          title: _(t`Success`),
          message: _(t`BOM Item Validated`),
          color: 'green'
        });
        table.refreshTable();
      })
      .catch((_error) => {
        showNotification({
          title: _(t`Error`),
          message: _(t`Failed to validate BOM Item`),
          color: 'red'
        });
      });
  }, [api, i18n, table]);

  // Fonction d'export JSON (simple)
  const exportToJson = useCallback(() => {
    if (flatItems.length === 0) {
      showNotification({
        title: _(t`Warning`),
        message: _(t`No data to export`),
        color: 'orange'
      });
      return;
    }

    const exportData = {
      exported_at: new Date().toISOString(),
      part_id: partId,
      type: 'flat_bom',
      items: flatItems.map(item => ({
        id: item.pk,
        part_id: item.part,
        sub_part_id: item.sub_part,
        name: item.sub_part_detail?.full_name || '',
        ipn: item.sub_part_detail?.IPN || '',
        quantity: item.quantity,
        total_quantity: item.total_quantity,
        level: item.level || 0,
        parent: item.parent_name || '',
        reference: item.reference || '',
        description: item.sub_part_detail?.description || '',
        optional: item.optional || false,
        consumable: item.consumable || false,
        validated: item.validated || false,
        stock: item.available_stock || 0
      }))
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `nomenclature_export_${timestamp}.json`;
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    showNotification({
      title: _(t`Export Completed`),
      message: _(t`File saved as ${filename}`),
      color: 'green'
    });
  }, [flatItems, partId, _]);

  const exportCustomCsv = useCallback(() => {
    const dataToExport = showFlat ? flatItems : directBomItems;
    
    if (dataToExport.length === 0) {
      showNotification({
        title: _(t`Warning`),
        message: _(t`No data to export`),
        color: 'orange'
      });
      return;
    }
    
    let processedData = dataToExport;
    
    if (showFlat && consolidateExport) {
      const consolidatedMap = new Map<number, any>();
      
      dataToExport.forEach(item => {
        const partId = item.sub_part;
        
        if (consolidatedMap.has(partId)) {
          const existing = consolidatedMap.get(partId);
          existing.total_quantity = (existing.total_quantity || 0) + (item.total_quantity || item.quantity || 0);
          existing.quantity = (existing.quantity || 0) + (item.quantity || 0);
          existing.available_stock = Math.max(existing.available_stock || 0, item.available_stock || 0);
          
          if (!existing.level || (item.level && item.level < existing.level)) {
            existing.level = item.level;
            existing.parent_name = item.parent_name;
          }
          
          if (item.reference && existing.reference !== item.reference) {
            existing.reference = existing.reference ? 
              `${existing.reference}, ${item.reference}` : item.reference;
          }
        } else {
          consolidatedMap.set(partId, {
            ...item,
            total_quantity: item.total_quantity || item.quantity || 0
          });
        }
      });
      
      processedData = Array.from(consolidatedMap.values());
    }
    
    const csvData = processedData.map(item => {
      const row: { [key: string]: any } = {};
      
      selectedColumns.forEach(columnKey => {
        const columnConfig = availableColumns.find(col => col.key === columnKey);
        if (!columnConfig) return;
        
        let value = '';
        
        switch (columnKey) {
          case 'sub_part_detail.full_name':
            value = item.sub_part_detail?.full_name || '';
            break;
          case 'sub_part_detail.IPN':
            value = item.sub_part_detail?.IPN || '';
            break;
          case 'sub_part_detail.description':
            value = item.sub_part_detail?.description || '';
            break;
          case 'sub_part_detail.units':
            value = item.sub_part_detail?.units || '';
            break;
          case 'total_quantity':
            value = showFlat ? String(item.total_quantity || item.quantity) : String(item.quantity);
            break;
          case 'quantity':
            value = (showFlat && consolidateExport) ? String(item.total_quantity || item.quantity) : String(item.quantity);
            break;
          case 'optional':
          case 'consumable':
          case 'validated':
            value = item[columnKey.split('.').pop()!] ? 'Yes' : 'No';
            break;
          default:
            const key = columnKey.includes('.') ? columnKey.split('.').pop()! : columnKey;
            value = item[key] || '';
        }
        
        row[columnConfig.label] = value;
      });
      
    
    
    if (showFlat && !consolidateExport && item.level && item.level > 0) {
      row['Level'] = item.level;
      row['Parent'] = item.parent_name || '';
    }
    
    return row;
  });

  const headers = Object.keys(csvData[0]);
  const csvContent = [
    headers.join(','),
    ...csvData.map(row => 
      headers.map(header => `"${row[header]}"`).join(',')
    )
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const timestamp = new Date().toISOString().split('T')[0];
  const exportType = showFlat ? (consolidateExport ? '_consolidated' : '_detailed') : '_direct';
  const filename = `bom_export${exportType}_${timestamp}.csv`;

  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);

  showNotification({
    title: _(t`Export Complete`),
    message: _(t`Saved as ${filename}`),
    color: 'green'
  });
  
  setExportModal(false);
}, [flatItems, directBomItems, showFlat, consolidateExport, selectedColumns, availableColumns, partId, _]);

  const rowActions = useCallback(
    (record: any): RowAction[] => {
      if (showFlat && record.level && record.level > 0) {
        return [
          {
            title: t`View BOM`,
            onClick: (event: any) => {
              navigateToLink(`/part/${record.sub_part}/bom/`, navigate, event);
            },
            icon: <IconArrowRight />
          }
        ];
      }
      
      if (record.part && record.part != partId) {
        return [
          {
            title: t`View BOM`,
            onClick: (event: any) => {
              navigateToLink(`/part/${record.part}/bom/`, navigate, event);
            },
            icon: <IconArrowRight />
          }
        ];
      }

      return [
        {
          title: t`Validate BOM Line`,
          color: 'green',
          hidden: partLocked || record.validated || !user.hasChangeRole(UserRoles.part),
          icon: <IconCircleCheck />,
          onClick: () => validateSingleItem(record)
        },
        RowEditAction({
          hidden: partLocked || !user.hasChangeRole(UserRoles.part),
          onClick: () => {
            setSelectedBomItem(record);
            editBomItem.open();
          }
        }),
        {
          title: t`Edit Substitutes`,
          color: 'blue',
          hidden: partLocked || !user.hasAddRole(UserRoles.part),
          icon: <IconSwitch3 />,
          onClick: () => {
            setSelectedBomItem(record);
            editSubstitutes.open();
          }
        },
        RowDeleteAction({
          hidden: partLocked || !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            setSelectedBomItem(record);
            deleteBomItem.open();
          }
        })
      ];
    },
    [partId, partLocked, user, showFlat, navigate, i18n, validateBom, editBomItem, editSubstitutes, deleteBomItem]
  );

  const tableActions = useMemo(() => {
  const actions = [
    <Tooltip key="toggle" label={showFlat ? t`Show Direct BOM` : t`Show Flat BOM`}>
      <Group w={120}>
        <IconListTree size={20} />
        <Switch 
          checked={showFlat}
          onChange={(event) => setShowFlat(event.currentTarget.checked)}
          label={t`Flat BOM`}
          labelPosition="left"
          size="xs"
        />
      </Group>
    </Tooltip>
  ];

  let hasData = showFlat ? flatItems.length > 0 : directBomItems.length > 0;
  
  if (hasData) {
    actions.push(
      <ActionButton
        key='export-custom'
        tooltip={t`Export CSV`}
        icon={<IconDownload />}
        color="teal"
        onClick={() => setExportModal(true)}
      />
    );
  }

  if (showFlat && flatItems.length > 0) {
    actions.push(
      <ActionButton
        key='export-json'
        tooltip={t`Export JSON`}
        icon={<IconDownload />}
        onClick={exportToJson}
      />
    );
  }

  actions.push(
    <ActionButton
      key='validate-bom'
      hidden={partLocked || !user.hasChangeRole(UserRoles.part)}
      tooltip={t`Validate BOM`}
      icon={<IconCircleCheck />}
      onClick={() => validateBom.open()}
    />,
    <AddItemButton
      key='add-bom-item'
      hidden={partLocked || !user.hasAddRole(UserRoles.part)}
      tooltip={t`Add BOM Item`}
      onClick={() => newBomItem.open()}
    />
  );

  return actions;
}, [partLocked, user, showFlat, flatItems.length, directBomItems.length, exportModal, exportCustomCsv])

  const tableData = useMemo(() => {
    if (showFlat) {
      return flatItems;
    }
    return undefined;
  }, [showFlat, flatItems]);

 return (
  <>
    <Stack gap='xs'>
      {partLocked && (
        <Alert
          title={t`Part is Locked`}
          color='orange'
          icon={<IconLock />}
          p='xs'
        >
          <Text>{t`BOM cannot be edited - part is locked`}</Text>
        </Alert>
      )}
      
      {showFlat && (
        <Alert
          title={t`Flat BOM View`}
          color='blue'
          icon={<IconListTree />}
          p='xs'
        >
          <Text>{t`Showing all components at all levels needed to build this part. Quantities shown include multipliers for assemblies.`}</Text>
        </Alert>
      )}
      
      {loading ? (
        <Center p="xl">
          <Loader size="md" />
          <Text ml="md">{t`Loading complete BOM hierarchy...`}</Text>
        </Center>
      ) : (
        <InvenTreeTable
          url={showFlat ? undefined : apiUrl(ApiEndpoints.bom_list)}
          tableState={table}
          columns={tableColumns}
          props={{
            params: {
              ...params,
              part: partId,
              part_detail: true,
              sub_part_detail: true,
              include_pricing: true
            },
            tableActions: tableActions,
            tableFilters: tableFilters,
            rowActions: rowActions
          }}
          tableData={tableData}
        />
      )}
    </Stack>

    <Modal
      opened={exportModal}
      onClose={() => setExportModal(false)}
      title={t`Select Columns to Export`}
      size="md"
    >
      <Stack>
        <Text size="sm" c="dimmed">
          {t`Choose which columns you want to include in your export:`}
        </Text>
        
        <Stack gap="xs">
          {availableColumns.map((column) => (
            <Checkbox
              key={column.key}
              label={column.label}
              checked={selectedColumns.includes(column.key)}
              onChange={(event) => {
                if (event.currentTarget.checked) {
                  setSelectedColumns(prev => [...prev, column.key]);
                } else {
                  setSelectedColumns(prev => prev.filter(col => col !== column.key));
                }
              }}
            />
          ))}
        </Stack>
        {showFlat && (
        <Checkbox
          label={t`Consolidate Identical Parts (Sum Quantities)`}
          checked={consolidateExport}
          onChange={(event) => setConsolidateExport(event.currentTarget.checked)}
          description={t`Groups parts that appear multiple times and sums their quantities`}
          />
        )}
        
        <Group justify="flex-end" mt="md">
          <Button variant="light" onClick={() => setExportModal(false)}>
            {t`Cancel`}
          </Button>
          <Button 
            onClick={exportCustomCsv}
            disabled={selectedColumns.length === 0}
            leftSection={<IconDownload size={16} />}
          >
            {t`Export CSV`}
          </Button>
        </Group>
      </Stack>
    </Modal>
    
    <ImporterDrawer
      sessionId={selectedSession ?? -1}
      opened={selectedSession != undefined && importOpened}
      onClose={() => {
        setSelectedSession(undefined);
        setImportOpened(false);
        table.refreshTable();
      }}
    />

    {importBomItem.modal}
    {newBomItem.modal}
    {editBomItem.modal}
    {deleteBomItem.modal}
    {editSubstitutes.modal}
    {validateBom.modal}
  </>
);
};