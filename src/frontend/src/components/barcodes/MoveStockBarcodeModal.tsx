import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Alert,
  Button,
  Group,
  Loader,
  Modal,
  NumberInput,
  Stack,
  Table,
  Text
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldType } from '@lib/types/Forms';
import { showNotification } from '@mantine/notifications';
import { IconArrowRight, IconExclamationCircle } from '@tabler/icons-react';
import { api } from '../../App';
import { showApiErrorMessage } from '../../functions/notifications';
import { StandaloneField } from '../forms/StandaloneField';
import { RenderInstance } from '../render/Instance';
import { RenderStockItem } from '../render/Stock';
import type { BarcodeScanItem } from './BarcodeScanItem';

interface MoveStockBarcodeModalProps {
  opened: boolean;
  onClose: () => void;
  onSuccess: () => void;
  items: BarcodeScanItem[];
  sourceLocationPk?: number;
  destinationLocationPk?: number;
}

interface StockGroup {
  partPk: number;
  partName: string;
  partDetail: any;
  locationPk: number | null;
  locationName: string;
  locationDetail: any;
  totalQty: number;
  representativeItem: any;
}

export function MoveStockBarcodeModal({
  opened,
  onClose,
  onSuccess,
  items,
  sourceLocationPk,
  destinationLocationPk
}: Readonly<MoveStockBarcodeModalProps>) {
  const [submitting, setSubmitting] = useState(false);
  const [sourceLocation, setSourceLocation] = useState<number | null>(
    sourceLocationPk ?? null
  );
  const [destLocation, setDestLocation] = useState<number | null>(
    destinationLocationPk ?? null
  );

  // Collect unique part PKs from scanned items (both parts and stock items)
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

  // Fetch ALL stock items for the relevant parts
  const { data: allStockItems, isFetching } = useQuery({
    queryKey: ['stock-for-move', partIds, opened],
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
                location_detail: true
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

  // Group stock items by part + location
  const stockGroups: StockGroup[] = useMemo(() => {
    if (!allStockItems || allStockItems.length === 0) return [];

    const map = new Map<string, StockGroup>();

    allStockItems.forEach((item: any) => {
      const locPk = item.location ?? null;
      const key = `${item.part}_${locPk}`;

      const existing = map.get(key);
      if (existing) {
        existing.totalQty += item.quantity;
      } else {
        map.set(key, {
          partPk: item.part,
          partName:
            item.part_detail?.name ??
            item.part_detail?.full_name ??
            `Part ${item.part}`,
          partDetail: item.part_detail,
          locationPk: locPk,
          locationName:
            item.location_detail?.pathstring ??
            item.location_detail?.name ??
            '-',
          locationDetail: item.location_detail,
          totalQty: item.quantity,
          representativeItem: item
        });
      }
    });

    return [...map.values()];
  }, [allStockItems]);

  // Per-group move quantities, keyed by group key
  const [quantities, setQuantities] = useState<Record<string, number>>({});

  // Initialize quantities when groups change
  useEffect(() => {
    if (stockGroups.length > 0) {
      const initial: Record<string, number> = {};
      stockGroups.forEach((group) => {
        const key = `${group.partPk}_${group.locationPk}`;
        initial[key] = 0;
      });
      setQuantities(initial);
    }
  }, [stockGroups]);

  const sourceLocationField: ApiFormFieldType = useMemo(
    () => ({
      field_type: 'related field',
      api_url: apiUrl(ApiEndpoints.stock_location_list),
      model: ModelType.stocklocation,
      required: false,
      label: t`Source Location`,
      description: t`Show only stock in this location`,
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
      description: t`Stock items will be moved to this location`,
      filters: { structural: false },
      onValueChange: (value: any) => setDestLocation(value ?? null)
    }),
    []
  );

  const setQuantity = useCallback((groupKey: string, value: number) => {
    setQuantities((prev) => ({ ...prev, [groupKey]: value }));
  }, []);

  const handleMove = useCallback(async () => {
    if (!destLocation) return;

    // Build payload from groups with non-zero quantities
    const itemsToMove = stockGroups
      .filter((group) => {
        if (sourceLocation && group.locationPk !== sourceLocation) return false;
        const key = `${group.partPk}_${group.locationPk}`;
        const qty = quantities[key];
        return qty != null && qty > 0;
      })
      .map((group) => ({
        pk: group.representativeItem.pk,
        quantity: quantities[`${group.partPk}_${group.locationPk}`]
      }));

    if (itemsToMove.length === 0) {
      showNotification({
        title: t`No Items`,
        message: t`Enter a quantity to move`,
        color: 'orange'
      });
      return;
    }

    setSubmitting(true);

    try {
      await api.post(apiUrl(ApiEndpoints.stock_transfer), {
        location: destLocation,
        items: itemsToMove
      });

      const totalQty = itemsToMove.reduce((sum, i) => sum + i.quantity, 0);

      showNotification({
        title: t`Stock Moved`,
        message: t`${itemsToMove.length} group(s) (${totalQty} units) moved successfully`,
        color: 'green'
      });

      onSuccess();
      onClose();
    } catch (error) {
      showApiErrorMessage({
        error,
        title: t`Move Failed`,
        message: t`Failed to move stock items`
      });
    } finally {
      setSubmitting(false);
    }
  }, [
    sourceLocation,
    destLocation,
    stockGroups,
    quantities,
    onSuccess,
    onClose
  ]);

  // Compute totals for the button label
  const { movableGroupCount, movableTotalQty } = useMemo(() => {
    let count = 0;
    let totalQty = 0;
    stockGroups.forEach((group) => {
      if (sourceLocation && group.locationPk !== sourceLocation) return;
      const key = `${group.partPk}_${group.locationPk}`;
      const qty = quantities[key];
      if (qty != null && qty > 0) {
        count++;
        totalQty += qty;
      }
    });
    return { movableGroupCount: count, movableTotalQty: totalQty };
  }, [stockGroups, quantities, sourceLocation]);

  const filteredGroups = useMemo(() => {
    if (!sourceLocation) return stockGroups;
    return stockGroups.filter((g) => g.locationPk === sourceLocation);
  }, [stockGroups, sourceLocation]);

  return (
    <Modal opened={opened} onClose={onClose} title={t`Move Stock`} size='xl'>
      <Stack gap='md'>
        {partIds.length === 0 ? (
          <Alert color='red' icon={<IconExclamationCircle />}>
            <Trans>Select a scanned part or stock item to move</Trans>
          </Alert>
        ) : isFetching ? (
          <Group justify='center' py='xl'>
            <Loader />
            <Text c='dimmed'>
              <Trans>Loading stock for selected parts...</Trans>
            </Text>
          </Group>
        ) : stockGroups.length === 0 ? (
          <Alert color='red' icon={<IconExclamationCircle />}>
            <Trans>No stock found for the selected parts</Trans>
          </Alert>
        ) : (
          <>
            <StandaloneField
              fieldDefinition={sourceLocationField}
              fieldName='source_location'
              defaultValue={sourceLocationPk}
            />

            {sourceLocation && filteredGroups.length === 0 && (
              <Alert color='orange' icon={<IconExclamationCircle />}>
                <Trans>No stock found in the selected source location.</Trans>
              </Alert>
            )}

            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>
                    <Trans>Part</Trans>
                  </Table.Th>
                  <Table.Th>
                    <Trans>Location</Trans>
                  </Table.Th>
                  <Table.Th>
                    <Trans>Available</Trans>
                  </Table.Th>
                  <Table.Th style={{ width: '160px' }}>
                    <Trans>Qty to Move</Trans>
                  </Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {stockGroups.map((group) => {
                  const groupKey = `${group.partPk}_${group.locationPk}`;
                  const willMove =
                    !sourceLocation || group.locationPk === sourceLocation;
                  const moveQty = quantities[groupKey] ?? 0;
                  const isValidQty = moveQty > 0 && moveQty <= group.totalQty;

                  return (
                    <Table.Tr
                      key={groupKey}
                      style={{ opacity: willMove ? 1 : 0.4 }}
                    >
                      <Table.Td>
                        <RenderStockItem instance={group.representativeItem} />
                      </Table.Td>
                      <Table.Td>
                        {group.locationDetail ? (
                          <RenderInstance
                            instance={group.locationDetail}
                            model={ModelType.stocklocation}
                          />
                        ) : (
                          <Text c='dimmed'>-</Text>
                        )}
                      </Table.Td>
                      <Table.Td>
                        <Text
                          c={
                            willMove && moveQty < group.totalQty
                              ? 'orange'
                              : undefined
                          }
                        >
                          {group.totalQty}
                        </Text>
                      </Table.Td>
                      <Table.Td>
                        {willMove ? (
                          <NumberInput
                            value={moveQty}
                            onChange={(v) =>
                              setQuantity(
                                groupKey,
                                typeof v === 'number' ? v : 0
                              )
                            }
                            min={0}
                            max={group.totalQty}
                            step={1}
                            error={
                              !isValidQty && moveQty !== 0
                                ? t`Max ${group.totalQty}`
                                : undefined
                            }
                            styles={{
                              input: { width: '140px' }
                            }}
                          />
                        ) : (
                          <Text c='dimmed' size='sm'>
                            <Trans>Other location</Trans>
                          </Text>
                        )}
                      </Table.Td>
                    </Table.Tr>
                  );
                })}
              </Table.Tbody>
            </Table>

            <StandaloneField
              fieldDefinition={destLocationField}
              fieldName='dest_location'
              defaultValue={destinationLocationPk}
            />

            <Group justify='flex-end'>
              <Button variant='default' onClick={onClose}>
                <Trans>Cancel</Trans>
              </Button>
              <Button
                onClick={handleMove}
                loading={submitting}
                disabled={!destLocation || movableGroupCount === 0}
                leftSection={<IconArrowRight size={16} />}
              >
                {movableGroupCount === 0 ? (
                  <Trans>Move Stock</Trans>
                ) : (
                  <Trans>
                    Move {movableTotalQty} unit(s) from {movableGroupCount}{' '}
                    location(s)
                  </Trans>
                )}
              </Button>
            </Group>
          </>
        )}
      </Stack>
    </Modal>
  );
}
