import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Alert,
  Badge,
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
import type { BarcodeScanItem } from './BarcodeScanItem';

interface MoveStockBarcodeModalProps {
  opened: boolean;
  onClose: () => void;
  onSuccess: () => void;
  items: BarcodeScanItem[];
  sourceLocationPk?: number;
  destinationLocationPk?: number;
}

interface LocationStockGroup {
  partPk: number;
  partDetail: any;
  locationPk: number | null;
  locationDetail: any;
  caseQty: number; // the "standard" case size for this part
  caseCount: number; // how many full cases available
  looseQty: number; // total loose (non-case) units available
  caseItems: any[]; // stock items that match the case size
  looseItems: any[]; // stock items that don't match case size
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

  // Determine standard case size per part (most common stock item quantity > 1)
  const partCaseSizes = useMemo(() => {
    const map = new Map<number, number>(); // partPk -> caseQty
    if (!allStockItems) return map;

    // Count frequency of each quantity per part
    const freq = new Map<number, Map<number, number>>();
    allStockItems.forEach((item: any) => {
      const qty = item.quantity ?? 0;
      if (qty <= 1) return; // skip singles
      if (!freq.has(item.part)) freq.set(item.part, new Map());
      const partFreq = freq.get(item.part)!;
      partFreq.set(qty, (partFreq.get(qty) ?? 0) + 1);
    });

    // Pick most common quantity for each part
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

  // Group stock items by part + location, splitting into cases vs loose
  const stockGroups: LocationStockGroup[] = useMemo(() => {
    if (!allStockItems || allStockItems.length === 0) return [];

    const map = new Map<string, LocationStockGroup>();

    allStockItems.forEach((item: any) => {
      const locPk = item.location ?? null;
      const key = `${item.part}_${locPk}`;
      const caseQty = partCaseSizes.get(item.part) ?? 0;
      const isCase = caseQty > 0 && item.quantity === caseQty;

      if (!map.has(key)) {
        map.set(key, {
          partPk: item.part,
          partDetail: item.part_detail,
          locationPk: locPk,
          locationDetail: item.location_detail,
          caseQty,
          caseCount: 0,
          looseQty: 0,
          caseItems: [],
          looseItems: []
        });
      }

      const group = map.get(key)!;
      if (isCase) {
        group.caseCount += 1;
        group.caseItems.push(item);
      } else {
        group.looseQty += item.quantity ?? 0;
        group.looseItems.push(item);
      }
    });

    return [...map.values()];
  }, [allStockItems, partCaseSizes]);

  // Move state: { groupKey: { cases: n, units: n } }
  const [moveState, setMoveState] = useState<
    Record<string, { cases: number; units: number }>
  >({});

  useEffect(() => {
    if (stockGroups.length > 0) {
      const initial: Record<string, { cases: number; units: number }> = {};
      stockGroups.forEach((g) => {
        initial[`${g.partPk}_${g.locationPk}`] = { cases: 0, units: 0 };
      });
      setMoveState(initial);
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

  const handleMove = useCallback(async () => {
    if (!destLocation) return;

    // Build payload: map group moves to individual stock item quantities
    const transferItems: { pk: number; quantity: number }[] = [];

    stockGroups.forEach((group) => {
      if (sourceLocation && group.locationPk !== sourceLocation) return;
      const key = `${group.partPk}_${group.locationPk}`;
      const move = moveState[key];
      if (!move || (move.cases === 0 && move.units === 0)) return;

      // Allocate cases: move full quantity from case items
      let casesRemaining = move.cases;
      for (const caseItem of group.caseItems) {
        if (casesRemaining <= 0) break;
        transferItems.push({ pk: caseItem.pk, quantity: caseItem.quantity });
        casesRemaining--;
      }

      // Allocate loose units: use loose items first, then split from cases
      let unitsRemaining = move.units;
      for (const looseItem of group.looseItems) {
        if (unitsRemaining <= 0) break;
        const take = Math.min(unitsRemaining, looseItem.quantity ?? 0);
        transferItems.push({ pk: looseItem.pk, quantity: take });
        unitsRemaining -= take;
      }

      // If still need units, split from remaining case items
      for (const caseItem of group.caseItems) {
        if (unitsRemaining <= 0) break;
        // Skip case items already fully moved
        if (move.cases > 0 && group.caseItems.indexOf(caseItem) < move.cases)
          continue;
        const take = Math.min(unitsRemaining, caseItem.quantity ?? 0);
        if (take > 0) {
          transferItems.push({ pk: caseItem.pk, quantity: take });
          unitsRemaining -= take;
        }
      }
    });

    if (transferItems.length === 0) {
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
        items: transferItems
      });

      const totalQty = transferItems.reduce((sum, i) => sum + i.quantity, 0);
      showNotification({
        title: t`Stock Moved`,
        message: t`${transferItems.length} stock item(s) (${totalQty} units) moved successfully`,
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
    moveState,
    onSuccess,
    onClose
  ]);

  const { movableCount, movableTotalQty } = useMemo(() => {
    let count = 0;
    let totalQty = 0;
    stockGroups.forEach((group) => {
      if (sourceLocation && group.locationPk !== sourceLocation) return;
      const key = `${group.partPk}_${group.locationPk}`;
      const move = moveState[key];
      if (!move) return;
      const caseUnits = move.cases * group.caseQty;
      const total = caseUnits + move.units;
      if (total > 0) {
        count++;
        totalQty += total;
      }
    });
    return { movableCount: count, movableTotalQty: totalQty };
  }, [stockGroups, moveState, sourceLocation]);

  const filteredGroups = useMemo(() => {
    if (!sourceLocation) return stockGroups;
    return stockGroups.filter((g) => g.locationPk === sourceLocation);
  }, [stockGroups, sourceLocation]);

  return (
    <Modal opened={opened} onClose={onClose} title={t`Move Stock`} size='95%'>
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

            <Table striped highlightOnHover style={{ tableLayout: 'auto' }}>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th style={{ whiteSpace: 'nowrap' }}>
                    <Trans>Part</Trans>
                  </Table.Th>
                  <Table.Th style={{ whiteSpace: 'nowrap' }}>
                    <Trans>Location</Trans>
                  </Table.Th>
                  <Table.Th style={{ whiteSpace: 'nowrap' }}>
                    <Trans>Cases</Trans>
                  </Table.Th>
                  <Table.Th style={{ whiteSpace: 'nowrap' }}>
                    <Trans>Loose Units</Trans>
                  </Table.Th>
                  <Table.Th style={{ whiteSpace: 'nowrap' }}>
                    <Trans>Cases to Move</Trans>
                  </Table.Th>
                  <Table.Th style={{ whiteSpace: 'nowrap' }}>
                    <Trans>Units to Move</Trans>
                  </Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {stockGroups.map((group) => {
                  const groupKey = `${group.partPk}_${group.locationPk}`;
                  const willMove =
                    !sourceLocation || group.locationPk === sourceLocation;
                  const move = moveState[groupKey] ?? { cases: 0, units: 0 };
                  const maxCases = group.caseCount;
                  const maxUnits =
                    group.looseQty +
                    (group.caseCount - move.cases) * group.caseQty;

                  return (
                    <Table.Tr
                      key={groupKey}
                      style={{ opacity: willMove ? 1 : 0.4 }}
                    >
                      <Table.Td>
                        <RenderInstance
                          instance={group.partDetail}
                          model={ModelType.part}
                        />
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
                        {group.caseCount > 0 ? (
                          <Group gap='xs'>
                            <Text fw={700}>{group.caseCount}</Text>
                            <Badge variant='light' color='blue' size='sm'>
                              {group.caseCount} &times; {group.caseQty}
                            </Badge>
                          </Group>
                        ) : (
                          <Text c='dimmed'>-</Text>
                        )}
                      </Table.Td>
                      <Table.Td>
                        {group.looseQty > 0 ? (
                          <Text fw={700}>{group.looseQty}</Text>
                        ) : (
                          <Text c='dimmed'>-</Text>
                        )}
                      </Table.Td>
                      <Table.Td>
                        {willMove && maxCases > 0 ? (
                          <NumberInput
                            value={move.cases}
                            onChange={(v) =>
                              setMoveState((prev) => ({
                                ...prev,
                                [groupKey]: {
                                  ...(prev[groupKey] ?? { cases: 0, units: 0 }),
                                  cases: typeof v === 'number' ? v : 0
                                }
                              }))
                            }
                            min={0}
                            max={maxCases}
                            step={1}
                          />
                        ) : (
                          <Text c='dimmed' size='sm'>
                            {willMove ? '-' : <Trans>Other location</Trans>}
                          </Text>
                        )}
                      </Table.Td>
                      <Table.Td>
                        {willMove && maxUnits > 0 ? (
                          <NumberInput
                            value={move.units}
                            onChange={(v) =>
                              setMoveState((prev) => ({
                                ...prev,
                                [groupKey]: {
                                  ...(prev[groupKey] ?? { cases: 0, units: 0 }),
                                  units: typeof v === 'number' ? v : 0
                                }
                              }))
                            }
                            min={0}
                            max={maxUnits}
                            step={1}
                          />
                        ) : (
                          <Text c='dimmed' size='sm'>
                            {willMove ? '-' : ''}
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
                disabled={!destLocation || movableCount === 0}
                leftSection={<IconArrowRight size={16} />}
              >
                {movableCount === 0 ? (
                  <Trans>Move Stock</Trans>
                ) : (
                  <Trans>
                    Move {movableTotalQty} unit(s) from {movableCount}{' '}
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
