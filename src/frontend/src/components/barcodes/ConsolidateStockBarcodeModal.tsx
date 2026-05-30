import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Alert,
  Badge,
  Button,
  Checkbox,
  Group,
  Loader,
  Modal,
  Paper,
  Radio,
  Stack,
  Table,
  Text,
  Tooltip
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldType } from '@lib/types/Forms';
import { showNotification } from '@mantine/notifications';
import { IconArrowMerge, IconExclamationCircle } from '@tabler/icons-react';
import { api } from '../../App';
import { showApiErrorMessage } from '../../functions/notifications';
import { StandaloneField } from '../forms/StandaloneField';
import { RenderInstance } from '../render/Instance';
import type { BarcodeScanItem } from './BarcodeScanItem';

interface ConsolidateStockBarcodeModalProps {
  opened: boolean;
  onClose: () => void;
  onSuccess: () => void;
  items: BarcodeScanItem[];
}

interface StockItemRow {
  pk: number;
  partPk: number;
  partDetail: any;
  quantity: number;
  locationPk: number | null;
  locationDetail: any;
  supplierPartPk: number | null;
  supplierPartDetail: any;
  status: number;
  statusLabel: string;
  purchasePrice: string | null;
  purchasePriceCurrency: string | null;
  batch: string | null;
  packaging: string | null;
  isPackage: boolean;
  packageSize: number;
  // Constraints that would block merging
  unmergeableReason: string | null;
}

interface PartGroup {
  partPk: number;
  partDetail: any;
  packageSize: number;
  items: StockItemRow[];
}

export function ConsolidateStockBarcodeModal({
  opened,
  onClose,
  onSuccess,
  items
}: Readonly<ConsolidateStockBarcodeModalProps>) {
  const [submitting, setSubmitting] = useState(false);
  const [sourceLocation, setSourceLocation] = useState<number | null>(null);
  const [destLocation, setDestLocation] = useState<number | null>(null);
  // Per-part target selection: partPk -> stock item pk
  const [targetPks, setTargetPks] = useState<Record<number, number>>({});
  // Which items to include in merge: Set of stock item pks
  const [selectedPks, setSelectedPks] = useState<Set<number>>(new Set());
  const [allowMismatchedSuppliers, setAllowMismatchedSuppliers] =
    useState(false);
  const [allowMismatchedStatus, setAllowMismatchedStatus] = useState(false);

  // Reset all internal state when the modal opens
  useEffect(() => {
    if (opened) {
      setSourceLocation(null);
      setTargetPks({});
      setSelectedPks(new Set());
      setAllowMismatchedSuppliers(false);
      setAllowMismatchedStatus(false);
    }
  }, [opened]);

  // Extract part IDs from scanned items
  const partIds = useMemo(() => {
    const ids = new Set<number>();
    items.forEach((item) => {
      if (item.model === ModelType.part && item.instance?.pk) {
        ids.add(item.instance.pk);
      } else if (
        item.model === ModelType.stockitem &&
        item.instance?.part != null
      ) {
        ids.add(item.instance.part);
      }
    });
    return [...ids];
  }, [items]);

  // Extract specific stock item PKs from scanned items (if they scanned stock items directly)
  const scannedStockItemPks = useMemo(() => {
    const pks = new Set<number>();
    items.forEach((item) => {
      if (item.model === ModelType.stockitem && item.instance?.pk) {
        pks.add(item.instance.pk);
      }
    });
    return pks;
  }, [items]);

  // Fetch all in-stock items for the relevant parts
  const { data: allStockItems, isFetching } = useQuery({
    queryKey: ['stock-for-consolidate', partIds, opened],
    queryFn: async () => {
      if (partIds.length === 0 || !opened) return [];
      const results = await Promise.all(
        partIds.map((partId) =>
          api
            .get(apiUrl(ApiEndpoints.stock_item_list), {
              params: {
                part: partId,
                in_stock: true,
                part_detail: true,
                location_detail: true,
                supplier_part_detail: true
              }
            })
            .then((r) => {
              const data = r.data;
              return Array.isArray(data) ? data : (data?.results ?? []);
            })
        )
      );
      return results.flat();
    },
    enabled: opened && partIds.length > 0
  });

  // Detect package size per part (most common quantity > 1)
  const partPackageSizes = useMemo(() => {
    const map = new Map<number, number>();
    if (!allStockItems) return map;

    const freq = new Map<number, Map<number, number>>();
    allStockItems.forEach((item: any) => {
      const qty = item.quantity ?? 0;
      if (qty <= 1) return;
      const part = item.part ?? item.part_detail?.pk;
      if (!part) return;
      if (!freq.has(part)) freq.set(part, new Map());
      const partFreq = freq.get(part)!;
      partFreq.set(qty, (partFreq.get(qty) ?? 0) + 1);
    });

    freq.forEach((qtyMap, partPk) => {
      let bestQty = 0;
      let bestCount = 0;
      qtyMap.forEach((count, qty) => {
        if (count > bestCount || (count === bestCount && qty > bestQty)) {
          bestCount = count;
          bestQty = qty;
        }
      });
      if (bestQty > 0) map.set(partPk, bestQty);
    });

    return map;
  }, [allStockItems]);

  // Check if a stock item is mergeable and why not
  const checkUnmergeable = useCallback((item: any): string | null => {
    if (item.serialized || item.serial) return t`Serialized item`;
    if (item.sales_order) return t`Assigned to a sales order`;
    if (item.belongs_to) return t`Installed in another item`;
    if (item.customer) return t`Assigned to a customer`;
    if (item.is_building) return t`Currently in production`;
    // Check for installed items count
    if (item.installed_item_count && item.installed_item_count > 0)
      return t`Contains sub-items`;
    return null;
  }, []);

  // Build structured item rows grouped by part
  const partGroups: PartGroup[] = useMemo(() => {
    if (!allStockItems || allStockItems.length === 0) return [];

    const groupMap = new Map<number, StockItemRow[]>();

    allStockItems.forEach((item: any) => {
      const partPk = item.part ?? item.part_detail?.pk;
      if (!partPk) return;

      // Apply source location filter
      if (
        sourceLocation &&
        item.location !== sourceLocation &&
        (item.location_detail?.pk ?? item.location) !== sourceLocation
      )
        return;

      const packageSize = partPackageSizes.get(partPk) ?? 0;
      const row: StockItemRow = {
        pk: item.pk,
        partPk,
        partDetail: item.part_detail,
        quantity: item.quantity ?? 0,
        locationPk: item.location ?? item.location_detail?.pk ?? null,
        locationDetail: item.location_detail,
        supplierPartPk:
          item.supplier_part ?? item.supplier_part_detail?.pk ?? null,
        supplierPartDetail: item.supplier_part_detail,
        status: item.status ?? 0,
        statusLabel: item.status_label ?? '',
        purchasePrice: item.purchase_price ?? null,
        purchasePriceCurrency: item.purchase_price_currency ?? null,
        batch: item.batch ?? null,
        packaging: item.packaging ?? null,
        isPackage: packageSize > 0 && item.quantity === packageSize,
        packageSize,
        unmergeableReason: null
      };

      row.unmergeableReason = checkUnmergeable(item);

      if (!groupMap.has(partPk)) {
        groupMap.set(partPk, []);
      }
      groupMap.get(partPk)!.push(row);
    });

    // Sort items within each group: packages first (desc qty), then loose (desc qty)
    const groups: PartGroup[] = [];
    groupMap.forEach((rows, partPk) => {
      rows.sort((a, b) => {
        if (a.isPackage !== b.isPackage) return a.isPackage ? -1 : 1;
        return b.quantity - a.quantity;
      });

      const firstRow = rows[0];
      groups.push({
        partPk,
        partDetail: firstRow.partDetail,
        packageSize: firstRow.packageSize,
        items: rows
      });
    });

    return groups;
  }, [allStockItems, partPackageSizes, sourceLocation, checkUnmergeable]);

  // Initialize target and selection state when groups change
  useEffect(() => {
    if (partGroups.length === 0) return;

    const newTargetPks: Record<number, number> = {};
    const newSelectedPks = new Set<number>();

    partGroups.forEach((group) => {
      if (group.items.length === 0) return;

      // Default target: first item the user scanned, or first item
      let targetPk = group.items[0].pk;

      // Prefer a scanned stock item as the target
      for (const item of group.items) {
        if (scannedStockItemPks.has(item.pk)) {
          targetPk = item.pk;
          break;
        }
      }

      newTargetPks[group.partPk] = targetPk;
    });

    setTargetPks(newTargetPks);
    setSelectedPks(new Set());
  }, [partGroups, scannedStockItemPks]);

  // Toggle all mergeable items in a group
  const toggleSelectAll = useCallback(
    (group: PartGroup) => {
      const mergeablePks = group.items
        .filter((item) => !item.unmergeableReason)
        .map((item) => item.pk);

      const allSelected = mergeablePks.every((pk) => selectedPks.has(pk));

      setSelectedPks((prev) => {
        const next = new Set(prev);
        if (allSelected) {
          mergeablePks.forEach((pk) => next.delete(pk));
        } else {
          mergeablePks.forEach((pk) => next.add(pk));
        }
        return next;
      });
    },
    [selectedPks]
  );

  // Check for conflicts within a group relative to the target
  const getConflicts = useCallback(
    (group: PartGroup) => {
      const target = group.items.find((i) => i.pk === targetPks[group.partPk]);
      if (!target)
        return { hasSupplierConflict: false, hasStatusConflict: false };

      let hasSupplierConflict = false;
      let hasStatusConflict = false;

      group.items.forEach((item) => {
        if (item.pk === target.pk) return;
        if (!selectedPks.has(item.pk)) return;
        if (item.unmergeableReason) return;

        if (item.supplierPartPk !== target.supplierPartPk) {
          hasSupplierConflict = true;
        }
        if (item.status !== target.status) {
          hasStatusConflict = true;
        }
      });

      return { hasSupplierConflict, hasStatusConflict };
    },
    [targetPks, selectedPks]
  );

  // Compute result preview per group
  const getResultPreview = useCallback(
    (group: PartGroup) => {
      const target = group.items.find((i) => i.pk === targetPks[group.partPk]);
      if (!target) return null;

      let totalQty = target.quantity;
      const pricingData: { price: number; qty: number }[] = [];

      if (target.purchasePrice) {
        pricingData.push({
          price: Number.parseFloat(target.purchasePrice),
          qty: target.quantity
        });
      }

      let mergedCount = 0;
      group.items.forEach((item) => {
        if (item.pk === target.pk) return;
        if (!selectedPks.has(item.pk)) return;
        if (item.unmergeableReason) return;

        totalQty += item.quantity;
        mergedCount++;

        if (item.purchasePrice) {
          pricingData.push({
            price: Number.parseFloat(item.purchasePrice),
            qty: item.quantity
          });
        }
      });

      let avgPrice: string | null = null;
      if (pricingData.length > 0) {
        let totalPrice = 0;
        let totalPriceQty = 0;
        pricingData.forEach(({ price, qty }) => {
          totalPrice += price * qty;
          totalPriceQty += qty;
        });
        if (totalPriceQty > 0) {
          avgPrice = (totalPrice / totalPriceQty).toFixed(6);
        }
      }

      return { totalQty, mergedCount, avgPrice };
    },
    [targetPks, selectedPks]
  );

  const sourceLocationField: ApiFormFieldType = useMemo(
    () => ({
      field_type: 'related field',
      api_url: apiUrl(ApiEndpoints.stock_location_list),
      model: ModelType.stocklocation,
      required: false,
      label: t`Source Location`,
      description: t`Show only stock items in this location`,
      filters: { structural: false },
      onValueChange: (value: any) => setSourceLocation(value ?? null)
    }),
    []
  );

  const destLocationField: ApiFormFieldType = useMemo(
    () => ({
      field_type: 'related field',
      api_url: apiUrl(ApiEndpoints.stock_location_list),
      model: ModelType.stocklocation,
      required: true,
      label: t`Destination Location`,
      description: t`Consolidated stock will be moved to this location`,
      filters: { structural: false },
      onValueChange: (value: any) => setDestLocation(value ?? null)
    }),
    []
  );

  // Auto-detect a default destination location:
  // If ALL mergeable items across all part groups share the same location, default to it.
  // If items span multiple locations, leave blank to force an explicit choice.
  const defaultDestLocation = useMemo(() => {
    const locations = new Set<number>();
    partGroups.forEach((group) => {
      group.items.forEach((item) => {
        if (!item.unmergeableReason && item.locationPk != null) {
          locations.add(item.locationPk);
        }
      });
    });
    if (locations.size === 1) {
      return [...locations][0];
    }
    return undefined;
  }, [partGroups]);

  // Auto-populate destination location when all mergeable items share the same location.
  // When items span multiple locations, explicitly set to null so the operator must choose.
  useEffect(() => {
    if (opened) {
      setDestLocation(defaultDestLocation ?? null);
    }
  }, [opened, defaultDestLocation]);

  // Total mergeable count
  const totalMergeCount = useMemo(() => {
    let count = 0;
    partGroups.forEach((group) => {
      const target = targetPks[group.partPk];
      group.items.forEach((item) => {
        if (item.pk === target) return;
        if (selectedPks.has(item.pk) && !item.unmergeableReason) {
          count++;
        }
      });
    });
    return count;
  }, [partGroups, selectedPks, targetPks]);

  const handleConsolidate = useCallback(async () => {
    if (!destLocation) return;

    // Build one merge payload per part group
    const mergePayloads: any[] = [];

    for (const group of partGroups) {
      const targetPk = targetPks[group.partPk];
      if (!targetPk) continue;

      const target = group.items.find((i) => i.pk === targetPk);
      if (!target) continue;

      const mergeItemPks: number[] = [];
      group.items.forEach((item) => {
        if (item.pk === targetPk) return;
        if (!selectedPks.has(item.pk)) return;
        if (item.unmergeableReason) return;
        mergeItemPks.push(item.pk);
      });

      if (mergeItemPks.length === 0) continue;

      const conflicts = getConflicts(group);

      mergePayloads.push({
        items: [
          { item: targetPk },
          ...mergeItemPks.map((pk) => ({ item: pk }))
        ],
        location: destLocation,
        notes: t`Consolidated via bulk scanning`,
        allow_mismatched_suppliers:
          conflicts.hasSupplierConflict && allowMismatchedSuppliers,
        allow_mismatched_status:
          conflicts.hasStatusConflict && allowMismatchedStatus
      });
    }

    if (mergePayloads.length === 0) {
      showNotification({
        title: t`No Items`,
        message: t`Select items to consolidate`,
        color: 'orange'
      });
      return;
    }

    setSubmitting(true);

    try {
      // Execute merges sequentially (one per part)
      for (const payload of mergePayloads) {
        await api.post(apiUrl(ApiEndpoints.stock_merge), payload);
      }

      const totalItems = mergePayloads.reduce(
        (sum, p) => sum + p.items.length - 1,
        0
      );
      showNotification({
        title: t`Stock Consolidated`,
        message: t`${totalItems} stock item(s) consolidated successfully`,
        color: 'green'
      });

      onSuccess();
      onClose();
    } catch (error) {
      showApiErrorMessage({
        error,
        title: t`Consolidation Failed`,
        message: t`Failed to consolidate stock items`
      });
    } finally {
      setSubmitting(false);
    }
  }, [
    partGroups,
    targetPks,
    selectedPks,
    destLocation,
    getConflicts,
    allowMismatchedSuppliers,
    allowMismatchedStatus,
    onSuccess,
    onClose
  ]);

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={t`Consolidate Stock`}
      size='95%'
    >
      <Stack gap='md'>
        {partIds.length === 0 ? (
          <Alert color='red' icon={<IconExclamationCircle />}>
            <Trans>
              Select a scanned part or stock item to consolidate stock
            </Trans>
          </Alert>
        ) : isFetching ? (
          <Group justify='center' py='xl'>
            <Loader />
            <Text c='dimmed'>
              <Trans>Loading stock for selected parts...</Trans>
            </Text>
          </Group>
        ) : partGroups.length === 0 ? (
          <Alert color='red' icon={<IconExclamationCircle />}>
            <Trans>No stock found for the selected parts</Trans>
          </Alert>
        ) : (
          <>
            <StandaloneField
              key={`source-loc-${opened}`}
              fieldDefinition={sourceLocationField}
              fieldName='source_location'
            />

            {sourceLocation &&
              partGroups.every((g) => g.items.length === 0) && (
                <Alert color='orange' icon={<IconExclamationCircle />}>
                  <Trans>No stock found in the selected source location.</Trans>
                </Alert>
              )}

            {partGroups.map((group) => {
              const target = group.items.find(
                (i) => i.pk === targetPks[group.partPk]
              );
              const conflicts = getConflicts(group);
              const preview = getResultPreview(group);

              return (
                <Stack key={group.partPk} gap='xs'>
                  <Group gap='xs'>
                    <Text fw={700}>
                      <RenderInstance
                        instance={group.partDetail}
                        model={ModelType.part}
                      />
                    </Text>
                    {group.packageSize > 0 && (
                      <Badge variant='light' color='blue' size='sm'>
                        <Trans>Package size: {group.packageSize}</Trans>
                      </Badge>
                    )}
                  </Group>

                  <Button
                    variant='light'
                    size='compact-sm'
                    onClick={() => toggleSelectAll(group)}
                    styles={{ root: { alignSelf: 'flex-start' } }}
                  >
                    {group.items
                      .filter((i) => !i.unmergeableReason)
                      .every((i) => selectedPks.has(i.pk))
                      ? t`Deselect All`
                      : t`Select All`}
                  </Button>

                  <Table striped highlightOnHover>
                    <Table.Thead>
                      <Table.Tr>
                        <Table.Th style={{ width: 40 }}>
                          <Trans>Target</Trans>
                        </Table.Th>
                        <Table.Th style={{ width: 40 }}>
                          <Trans>Merge</Trans>
                        </Table.Th>
                        <Table.Th>
                          <Trans>Stock Item</Trans>
                        </Table.Th>
                        <Table.Th>
                          <Trans>Quantity</Trans>
                        </Table.Th>
                        <Table.Th>
                          <Trans>Location</Trans>
                        </Table.Th>
                        <Table.Th>
                          <Trans>Supplier Part</Trans>
                        </Table.Th>
                        <Table.Th>
                          <Trans>Status</Trans>
                        </Table.Th>
                        <Table.Th>
                          <Trans>Unit Price</Trans>
                        </Table.Th>
                        <Table.Th>
                          <Trans>Warnings</Trans>
                        </Table.Th>
                      </Table.Tr>
                    </Table.Thead>
                    <Table.Tbody>
                      {group.items.map((item) => {
                        const isTarget = item.pk === targetPks[group.partPk];
                        const isSelected = selectedPks.has(item.pk);
                        const isUnmergeable = !!item.unmergeableReason;

                        // Conflict detection relative to target
                        let supplierConflict = false;
                        let statusConflict = false;
                        if (
                          !isTarget &&
                          isSelected &&
                          !isUnmergeable &&
                          target
                        ) {
                          if (item.supplierPartPk !== target.supplierPartPk) {
                            supplierConflict = true;
                          }
                          if (item.status !== target.status) {
                            statusConflict = true;
                          }
                        }

                        return (
                          <Table.Tr
                            key={item.pk}
                            style={{
                              opacity: isUnmergeable ? 0.5 : 1
                            }}
                          >
                            <Table.Td>
                              <Radio
                                checked={isTarget}
                                onChange={() =>
                                  setTargetPks((prev) => ({
                                    ...prev,
                                    [group.partPk]: item.pk
                                  }))
                                }
                                disabled={isUnmergeable}
                                aria-label={t`Select as target`}
                              />
                            </Table.Td>
                            <Table.Td>
                              <Checkbox
                                checked={isSelected}
                                onChange={() =>
                                  setSelectedPks((prev) => {
                                    const next = new Set(prev);
                                    if (next.has(item.pk)) {
                                      next.delete(item.pk);
                                    } else {
                                      next.add(item.pk);
                                    }
                                    return next;
                                  })
                                }
                                disabled={isUnmergeable}
                                aria-label={t`Include in merge`}
                              />
                            </Table.Td>
                            <Table.Td>
                              <Group gap='xs'>
                                <RenderInstance
                                  instance={item}
                                  model={ModelType.stockitem}
                                />
                                {item.batch && (
                                  <Badge
                                    variant='outline'
                                    color='gray'
                                    size='xs'
                                  >
                                    {item.batch}
                                  </Badge>
                                )}
                              </Group>
                            </Table.Td>
                            <Table.Td>
                              <Group gap='xs'>
                                <Text fw={700}>{item.quantity}</Text>
                                {item.isPackage && (
                                  <Badge variant='light' color='blue' size='sm'>
                                    <Trans>Package</Trans>
                                  </Badge>
                                )}
                                {!item.isPackage && group.packageSize > 0 && (
                                  <Badge
                                    variant='light'
                                    color='orange'
                                    size='sm'
                                  >
                                    <Trans>Loose</Trans>
                                  </Badge>
                                )}
                              </Group>
                            </Table.Td>
                            <Table.Td>
                              {item.locationDetail ? (
                                <RenderInstance
                                  instance={item.locationDetail}
                                  model={ModelType.stocklocation}
                                />
                              ) : (
                                <Text c='dimmed'>-</Text>
                              )}
                            </Table.Td>
                            <Table.Td>
                              {item.supplierPartDetail ? (
                                <RenderInstance
                                  instance={item.supplierPartDetail}
                                  model={ModelType.supplierpart}
                                />
                              ) : (
                                <Text c='dimmed'>-</Text>
                              )}
                            </Table.Td>
                            <Table.Td>
                              <Badge
                                variant='light'
                                color={item.status === 10 ? 'green' : 'orange'}
                                size='sm'
                              >
                                {item.statusLabel || item.status}
                              </Badge>
                            </Table.Td>
                            <Table.Td>
                              {item.purchasePrice ? (
                                <Text size='sm'>
                                  {Number.parseFloat(
                                    item.purchasePrice
                                  ).toFixed(2)}{' '}
                                  {item.purchasePriceCurrency || ''}
                                </Text>
                              ) : (
                                <Text c='dimmed' size='sm'>
                                  -
                                </Text>
                              )}
                            </Table.Td>
                            <Table.Td>
                              <Group gap='xs'>
                                {item.unmergeableReason && (
                                  <Tooltip label={item.unmergeableReason}>
                                    <Badge color='red' size='sm'>
                                      <Trans>Cannot merge</Trans>
                                    </Badge>
                                  </Tooltip>
                                )}
                                {supplierConflict && (
                                  <Tooltip
                                    label={t`Supplier part differs from target`}
                                  >
                                    <Badge color='orange' size='sm'>
                                      <Trans>Supplier</Trans>
                                    </Badge>
                                  </Tooltip>
                                )}
                                {statusConflict && (
                                  <Tooltip
                                    label={t`Status differs from target`}
                                  >
                                    <Badge color='orange' size='sm'>
                                      <Trans>Status</Trans>
                                    </Badge>
                                  </Tooltip>
                                )}
                                {!item.unmergeableReason &&
                                  !supplierConflict &&
                                  !statusConflict && (
                                    <Text c='dimmed' size='sm'>
                                      -
                                    </Text>
                                  )}
                              </Group>
                            </Table.Td>
                          </Table.Tr>
                        );
                      })}
                    </Table.Tbody>
                  </Table>

                  {/* Conflict resolution toggles */}
                  {(conflicts.hasSupplierConflict ||
                    conflicts.hasStatusConflict) && (
                    <Paper p='sm' withBorder>
                      <Stack gap='xs'>
                        <Text fw={500} size='sm'>
                          <Trans>Conflict Resolution</Trans>
                        </Text>
                        {conflicts.hasSupplierConflict && (
                          <Checkbox
                            checked={allowMismatchedSuppliers}
                            onChange={(e) =>
                              setAllowMismatchedSuppliers(
                                e.currentTarget.checked
                              )
                            }
                            label={t`Allow mismatched suppliers (items with different supplier parts will be merged anyway)`}
                            size='sm'
                          />
                        )}
                        {conflicts.hasStatusConflict && (
                          <Checkbox
                            checked={allowMismatchedStatus}
                            onChange={(e) =>
                              setAllowMismatchedStatus(e.currentTarget.checked)
                            }
                            label={t`Allow mismatched status (items with different status codes will be merged anyway)`}
                            size='sm'
                          />
                        )}
                      </Stack>
                    </Paper>
                  )}

                  {/* Result preview */}
                  {preview && preview.mergedCount > 0 && (
                    <Paper p='sm' withBorder>
                      <Stack gap='xs'>
                        <Text fw={500} size='sm'>
                          <Trans>Result Preview</Trans>
                        </Text>
                        <Group gap='lg'>
                          <Text size='sm'>
                            <Trans>
                              Combined quantity:{' '}
                              <strong>{preview.totalQty}</strong>
                            </Trans>
                          </Text>
                          {preview.avgPrice && (
                            <Text size='sm'>
                              <Trans>
                                Weighted avg price:{' '}
                                <strong>{preview.avgPrice}</strong>
                              </Trans>
                            </Text>
                          )}
                          <Text size='sm'>
                            <Trans>
                              Merging <strong>{preview.mergedCount}</strong>{' '}
                              item(s)
                            </Trans>
                          </Text>
                        </Group>
                        <Text size='xs' c='orange'>
                          <Trans>
                            Note: Batch codes and packaging info from merged
                            items will be lost. The target item&apos;s batch and
                            packaging will be kept.
                          </Trans>
                        </Text>
                      </Stack>
                    </Paper>
                  )}
                </Stack>
              );
            })}

            <StandaloneField
              key={`dest-loc-${opened}`}
              fieldDefinition={destLocationField}
              fieldName='dest_location'
              defaultValue={defaultDestLocation}
            />

            <Group justify='flex-end'>
              <Button variant='default' onClick={onClose}>
                <Trans>Cancel</Trans>
              </Button>
              <Button
                onClick={handleConsolidate}
                loading={submitting}
                disabled={!destLocation || totalMergeCount === 0}
                leftSection={<IconArrowMerge size={16} />}
                color='orange'
              >
                {totalMergeCount === 0 ? (
                  <Trans>Consolidate Stock</Trans>
                ) : (
                  <Trans>Consolidate {totalMergeCount} item(s)</Trans>
                )}
              </Button>
            </Group>
          </>
        )}
      </Stack>
    </Modal>
  );
}
