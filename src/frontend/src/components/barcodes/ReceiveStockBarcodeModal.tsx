import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Alert,
  Anchor,
  Badge,
  Button,
  Divider,
  Group,
  Loader,
  Modal,
  NumberInput,
  Select,
  Stack,
  Table,
  Text
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { getDetailUrl } from '@lib/functions/Navigation';
import type { ApiFormFieldType } from '@lib/types/Forms';
import { showNotification } from '@mantine/notifications';
import {
  IconArrowRight,
  IconExclamationCircle,
  IconTruckDelivery
} from '@tabler/icons-react';
import { api } from '../../App';
import { showApiErrorMessage } from '../../functions/notifications';
import { StandaloneField } from '../forms/StandaloneField';
import { RenderStockItem } from '../render/Stock';
import type { BarcodeScanItem } from './BarcodeScanItem';

const PO_STATUS_PLACED = 20;

interface ReceiveStockBarcodeModalProps {
  opened: boolean;
  onClose: () => void;
  onSuccess: () => void;
  items: BarcodeScanItem[];
}

interface PoLineData {
  pk: number;
  order: number;
  orderReference: string;
  quantity: number;
  received: number;
  part: number;
  part_detail?: any;
  supplier_part_detail?: any;
}

export function ReceiveStockBarcodeModal({
  opened,
  onClose,
  onSuccess,
  items
}: Readonly<ReceiveStockBarcodeModalProps>) {
  const [submitting, setSubmitting] = useState(false);
  const [selectedPoPk, setSelectedPoPk] = useState<string | null>(null);
  const [selectedLinePk, setSelectedLinePk] = useState<number | null>(null);
  const [quantity, setQuantity] = useState<number>(0);
  const [destLocation, setDestLocation] = useState<number | null>(null);

  // Collect unique part PKs from scanned items
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

  // We only support a single part for receiving
  const primaryPartId = partIds.length > 0 ? partIds[0] : null;

  // Find a representative instance for rendering the part
  const representativeInstance = useMemo(() => {
    const partItem = items.find(
      (i) => i.model === ModelType.part && i.instance
    );
    if (partItem) return partItem.instance;

    const stockItem = items.find(
      (i) => i.model === ModelType.stockitem && i.instance?.part_detail
    );
    if (stockItem) return stockItem.instance.part_detail;

    return null;
  }, [items]);

  // Fetch open purchase orders
  const { data: purchaseOrders, isFetching: fetchingPOs } = useQuery({
    queryKey: ['open-pos-for-receive', opened],
    queryFn: async () => {
      if (!opened) return [];
      const r = await api.get(apiUrl(ApiEndpoints.purchase_order_list), {
        params: { outstanding: true, supplier_detail: true }
      });
      const data = r.data;
      return Array.isArray(data) ? data : (data?.results ?? []);
    },
    enabled: opened
  });

  // Fetch line items for the primary part across all PLACED POs
  const { data: matchingLines, isFetching: fetchingLines } = useQuery({
    queryKey: ['po-lines-for-part', primaryPartId, opened],
    queryFn: async () => {
      if (!primaryPartId || !opened) return [];
      const r = await api.get(apiUrl(ApiEndpoints.purchase_order_line_list), {
        params: {
          base_part: primaryPartId,
          order_status: PO_STATUS_PLACED,
          part_detail: true,
          supplier_part_detail: true
        }
      });
      const data = r.data;
      return (
        Array.isArray(data) ? data : (data?.results ?? [])
      ) as PoLineData[];
    },
    enabled: opened && primaryPartId != null
  });

  // Build a set of PO PKs that have a matching line item
  const posWithMatchingPart = useMemo(() => {
    if (!matchingLines) return new Set<number>();
    return new Set(matchingLines.map((l) => l.order));
  }, [matchingLines]);

  // Build the PO select options
  const poOptions = useMemo(() => {
    if (!purchaseOrders) return [];

    const options: Array<{
      value: string;
      label: string;
      hasPart: boolean;
      status: number;
    }> = [];

    purchaseOrders.forEach((po: any) => {
      const hasPart = posWithMatchingPart.has(po.pk);
      const label = `${po.reference} — ${po.supplier_detail?.name ?? po.supplier ?? '?'}`;
      options.push({
        value: String(po.pk),
        label,
        hasPart,
        status: po.status
      });
    });

    // Sort: matching POs first, then by reference
    options.sort((a, b) => {
      if (a.hasPart !== b.hasPart) return a.hasPart ? -1 : 1;
      return a.label.localeCompare(b.label);
    });

    return options;
  }, [purchaseOrders, posWithMatchingPart]);

  // Selected PO object
  const selectedPo = useMemo(() => {
    if (!selectedPoPk || !purchaseOrders) return null;
    return (
      purchaseOrders.find((po: any) => String(po.pk) === selectedPoPk) ?? null
    );
  }, [selectedPoPk, purchaseOrders]);

  // Lines for the selected PO
  const linesForSelectedPo = useMemo(() => {
    if (!selectedPoPk || !matchingLines) return [];
    return matchingLines.filter((l) => String(l.order) === selectedPoPk);
  }, [selectedPoPk, matchingLines]);

  // Selected line item
  const selectedLine = useMemo(() => {
    if (selectedLinePk == null) return null;
    return linesForSelectedPo.find((l) => l.pk === selectedLinePk) ?? null;
  }, [selectedLinePk, linesForSelectedPo]);

  const remaining = selectedLine
    ? Math.max(0, selectedLine.quantity - selectedLine.received)
    : 0;

  // Reset quantity when line changes
  useEffect(() => {
    if (selectedLine) {
      setQuantity(remaining);
    } else if (selectedPo && linesForSelectedPo.length === 0) {
      setQuantity(1);
    }
  }, [selectedLinePk, selectedPoPk]);

  // Reset dependent state when PO changes
  useEffect(() => {
    setSelectedLinePk(null);
    setQuantity(0);
  }, [selectedPoPk]);

  const destLocationField: ApiFormFieldType = useMemo(
    () => ({
      field_type: 'related field',
      api_url: apiUrl(ApiEndpoints.stock_location_list),
      model: ModelType.stocklocation,
      required: true,
      label: t`Location`,
      description: t`Where the received stock will be placed`,
      filters: { structural: false },
      onValueChange: (value: any) => setDestLocation(value ?? null)
    }),
    []
  );

  const handleReceive = useCallback(async () => {
    if (!primaryPartId || quantity <= 0) {
      showNotification({
        title: t`Invalid quantity`,
        message: t`Enter a positive quantity to receive`,
        color: 'orange'
      });
      return;
    }

    setSubmitting(true);

    try {
      if (selectedLine) {
        // Receive against a PO line item
        const payload = {
          items: [
            {
              line_item: selectedLine.pk,
              quantity,
              ...(destLocation ? { location: destLocation } : {})
            }
          ]
        };

        await api.post(
          apiUrl(ApiEndpoints.purchase_order_receive, selectedPo.pk),
          payload
        );

        showNotification({
          title: t`Stock Received`,
          message: t`${quantity} unit(s) received against ${selectedPo.reference}`,
          color: 'green'
        });
      } else {
        // Add stock directly (no PO line match, or no PO selected)
        const payload: any = {
          part: primaryPartId,
          quantity
        };
        if (destLocation) {
          payload.location = destLocation;
        }
        if (selectedPo) {
          payload.purchase_order = selectedPo.pk;
          payload.notes = t`Unexpected receipt — not on original PO line items`;
        }

        await api.post(apiUrl(ApiEndpoints.stock_item_list), payload);

        showNotification({
          title: t`Stock Added`,
          message: selectedPo
            ? t`${quantity} unit(s) added to inventory (linked to ${selectedPo.reference})`
            : t`${quantity} unit(s) added to inventory`,
          color: 'green'
        });
      }

      onSuccess();
      onClose();
    } catch (error) {
      showApiErrorMessage({
        error,
        title: t`Receive Failed`,
        message: t`Failed to receive stock`
      });
    } finally {
      setSubmitting(false);
    }
  }, [
    primaryPartId,
    quantity,
    destLocation,
    selectedLine,
    selectedPo,
    onSuccess,
    onClose
  ]);

  const canSubmit =
    quantity > 0 &&
    (selectedLine ? destLocation != null || !!selectedPo?.destination : true);

  const createPoUrl = '/purchase-order/create/';
  const poDetailUrl = selectedPo
    ? getDetailUrl(ModelType.purchaseorder, selectedPo.pk)
    : null;

  // Render a custom option in the Select dropdown
  const renderPoOption = (option: {
    value: string;
    label: string;
    hasPart: boolean;
    status: number;
  }) => (
    <Group justify='space-between' wrap='nowrap'>
      <Group gap='xs' wrap='nowrap'>
        {option.hasPart && (
          <IconTruckDelivery size={14} color='var(--mantine-color-green-6)' />
        )}
        <Text size='sm'>{option.label}</Text>
      </Group>
      <Badge
        size='xs'
        variant='light'
        color={
          option.status === PO_STATUS_PLACED
            ? 'blue'
            : option.status === 10
              ? 'gray'
              : 'yellow'
        }
      >
        {option.status === PO_STATUS_PLACED
          ? t`Placed`
          : option.status === 10
            ? t`Pending`
            : option.status === 25
              ? t`On Hold`
              : `#${option.status}`}
      </Badge>
    </Group>
  );

  return (
    <Modal opened={opened} onClose={onClose} title={t`Receive Stock`} size='lg'>
      <Stack gap='md'>
        {partIds.length === 0 ? (
          <Alert color='red' icon={<IconExclamationCircle />}>
            <Trans>Select a scanned part to receive stock</Trans>
          </Alert>
        ) : fetchingPOs ? (
          <Group justify='center' py='xl'>
            <Loader />
            <Text c='dimmed'>
              <Trans>Loading purchase orders...</Trans>
            </Text>
          </Group>
        ) : (
          <>
            {/* Part display */}
            {representativeInstance && (
              <RenderStockItem instance={representativeInstance} />
            )}

            <Divider />

            {/* PO Selector */}
            <Select
              label={t`Purchase Order`}
              placeholder={t`Select a purchase order...`}
              data={[
                ...poOptions.map((opt) => ({
                  value: opt.value,
                  label: `${opt.hasPart ? '● ' : ''}${opt.label}`,
                  hasPart: opt.hasPart,
                  status: opt.status
                })),
                {
                  value: '__none__',
                  label: `✚ ${t`Receive without PO (add directly to stock)`}`,
                  hasPart: false,
                  status: -1
                }
              ]}
              value={selectedPoPk}
              onChange={(v) => setSelectedPoPk(v === '__none__' ? null : v)}
              searchable
              clearable
              nothingFoundMessage={t`No open purchase orders found`}
              maxDropdownHeight={300}
              renderOption={({ option }) => {
                if (option.value === '__none__') {
                  return (
                    <Text size='sm' fs='italic' c='dimmed'>
                      {option.label}
                    </Text>
                  );
                }
                return renderPoOption({
                  value: option.value,
                  label: option.label.replace(/^● /, ''),
                  hasPart: (option as any).hasPart,
                  status: (option as any).status
                });
              }}
            />

            {/* No open POs link */}
            {poOptions.length === 0 && !fetchingPOs && (
              <Alert color='blue'>
                <Trans>No open purchase orders.</Trans>{' '}
                <Anchor href={createPoUrl} target='_blank'>
                  <Trans>Create a purchase order</Trans>
                </Anchor>
              </Alert>
            )}

            {/* Selected PO info */}
            {selectedPo && selectedPo.status !== PO_STATUS_PLACED && (
              <Alert color='orange' icon={<IconExclamationCircle />}>
                <Trans>
                  This order is not yet placed. Only placed orders can receive
                  stock.
                </Trans>{' '}
                <Anchor href={poDetailUrl!} target='_blank'>
                  <Trans>View order</Trans>
                </Anchor>
              </Alert>
            )}

            {/* Line item selection (when PO has matching lines) */}
            {selectedPo &&
            selectedPo.status === PO_STATUS_PLACED &&
            fetchingLines ? (
              <Group justify='center' py='sm'>
                <Loader size='sm' />
                <Text size='sm' c='dimmed'>
                  <Trans>Loading line items...</Trans>
                </Text>
              </Group>
            ) : selectedPo &&
              selectedPo.status === PO_STATUS_PLACED &&
              linesForSelectedPo.length > 0 ? (
              <>
                <Divider />
                <Text size='sm' fw={500}>
                  <Trans>Line Items</Trans>
                </Text>

                <Table striped highlightOnHover>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>
                        <Trans>Line</Trans>
                      </Table.Th>
                      <Table.Th>
                        <Trans>Expected</Trans>
                      </Table.Th>
                      <Table.Th>
                        <Trans>Received</Trans>
                      </Table.Th>
                      <Table.Th>
                        <Trans>Remaining</Trans>
                      </Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {linesForSelectedPo.map((line) => {
                      const rem = Math.max(0, line.quantity - line.received);
                      const isSelected = selectedLinePk === line.pk;
                      return (
                        <Table.Tr
                          key={line.pk}
                          onClick={() => {
                            setSelectedLinePk(line.pk);
                            setQuantity(rem);
                          }}
                          style={{
                            cursor: 'pointer',
                            backgroundColor: isSelected
                              ? 'var(--mantine-color-blue-light)'
                              : undefined
                          }}
                        >
                          <Table.Td>
                            <Badge
                              size='sm'
                              variant={isSelected ? 'filled' : 'light'}
                              color={isSelected ? 'blue' : 'gray'}
                            >
                              #{line.pk}
                            </Badge>
                          </Table.Td>
                          <Table.Td>{line.quantity}</Table.Td>
                          <Table.Td>{line.received}</Table.Td>
                          <Table.Td>
                            <Text
                              c={rem > 0 ? 'blue' : 'dimmed'}
                              fw={rem > 0 ? 600 : undefined}
                            >
                              {rem}
                            </Text>
                          </Table.Td>
                        </Table.Tr>
                      );
                    })}
                  </Table.Tbody>
                </Table>
              </>
            ) : selectedPo &&
              selectedPo.status === PO_STATUS_PLACED &&
              linesForSelectedPo.length === 0 &&
              !fetchingLines ? (
              <Alert color='blue' icon={<IconExclamationCircle />}>
                <Text>
                  <Trans>
                    This part is not listed on {selectedPo.reference}.
                  </Trans>
                </Text>
                <Text>
                  <Trans>
                    Stock will be added directly to inventory, linked to this PO
                    with the note "Unexpected receipt — not on original PO line
                    items".
                  </Trans>
                </Text>
                <Anchor
                  href={poDetailUrl!}
                  target='_blank'
                  display='block'
                  mt={4}
                >
                  <Trans>Add line items to this order</Trans>
                </Anchor>
              </Alert>
            ) : null}

            {/* Receive without PO */}
            {!selectedPo && !fetchingPOs && (
              <Alert color='blue'>
                <Text>
                  <Trans>
                    Stock will be added directly to inventory without linking to
                    a purchase order.
                  </Trans>
                </Text>
                <Anchor href={createPoUrl} target='_blank'>
                  <Trans>Create a purchase order</Trans>
                </Anchor>
              </Alert>
            )}

            {/* Quantity and Location */}
            {(selectedPo?.status === PO_STATUS_PLACED || !selectedPo) && (
              <>
                <Group grow>
                  <NumberInput
                    label={t`Quantity to Receive`}
                    description={
                      selectedLine
                        ? t`Remaining on order: ${remaining}`
                        : undefined
                    }
                    value={quantity}
                    onChange={(v) => setQuantity(typeof v === 'number' ? v : 0)}
                    min={1}
                    step={1}
                    styles={{ input: { width: '100%' } }}
                  />
                </Group>

                <StandaloneField
                  fieldDefinition={destLocationField}
                  fieldName='location'
                  defaultValue={selectedPo?.destination ?? undefined}
                />
              </>
            )}

            <Group justify='flex-end'>
              <Button variant='default' onClick={onClose}>
                <Trans>Cancel</Trans>
              </Button>
              <Button
                onClick={handleReceive}
                loading={submitting}
                disabled={
                  !canSubmit ||
                  (!!selectedPo && selectedPo.status !== PO_STATUS_PLACED)
                }
                leftSection={<IconArrowRight size={16} />}
              >
                {selectedLine ? (
                  <Trans>Receive {quantity} unit(s)</Trans>
                ) : selectedPo ? (
                  <Trans>Add {quantity} unit(s) (unexpected)</Trans>
                ) : (
                  <Trans>Add {quantity} unit(s) to stock</Trans>
                )}
              </Button>
            </Group>
          </>
        )}
      </Stack>
    </Modal>
  );
}
