import { t } from '@lingui/core/macro';
import {
  Alert,
  Badge,
  Button,
  Group,
  NumberInput,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Textarea
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRef, useState } from 'react';
import { createRequestId } from '../../functions/requestId';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { useApi } from '../../contexts/ApiContext';

type ApiList<T> = T[] | { results?: T[] };

type Manifest = {
  id?: number;
  pk?: number;
  package_code: string;
  checked_at?: string | null;
  signed_at?: string | null;
  shipment?: number;
};

type ManifestLine = {
  id?: number;
  pk?: number;
  manifest_line?: number;
  manifest: number;
  stock_item: number;
  quantity: string | number;
  item_role?: string;
  stock_item_detail?: {
    serial?: string | null;
    part_detail?: { name?: string; IPN?: string };
  };
};

type ReceiptValue = {
  quantity: number | string;
  condition: string;
  notes: string;
};

type ReceiptException = {
  id: number;
  kind: 'short' | 'damaged' | 'wrong_item';
  expected_quantity: string;
  received_quantity: string;
  notes: string;
};

function listResults<T>(payload: ApiList<T>): T[] {
  return Array.isArray(payload) ? payload : (payload.results ?? []);
}

function recordId(value: { id?: number; pk?: number }) {
  return value.id ?? value.pk ?? 0;
}

function idempotencyKey() {
  return createRequestId();
}

export default function ShipmentReceiptPanel({
  shipmentId,
  shipped
}: {
  shipmentId: number;
  shipped: boolean;
}) {
  const api = useApi();
  const queryClient = useQueryClient();
  const requestKey = useRef<string | undefined>(undefined);
  const [manifestId, setManifestId] = useState<string | null>(null);
  const [recipientName, setRecipientName] = useState('');
  const [notes, setNotes] = useState('');
  const [isFinal, setIsFinal] = useState(true);
  const [values, setValues] = useState<Record<number, ReceiptValue>>({});
  const [resolutions, setResolutions] = useState<Record<number, string>>({});

  const manifestsQuery = useQuery({
    queryKey: ['cangxu-shipment-manifests', shipmentId],
    enabled: shipped,
    queryFn: async () => {
      const response = await api.get(
        apiUrl(ApiEndpoints.cangxu_manifest_list),
        { params: { shipment: shipmentId, limit: 100 } }
      );
      return listResults(response.data as ApiList<Manifest>);
    }
  });

  const manifests = (manifestsQuery.data ?? []).filter(
    (manifest) => manifest.checked_at
  );
  const openManifests = manifests.filter((manifest) => !manifest.signed_at);
  const selectedManifest = manifests.find(
    (manifest) => String(recordId(manifest)) === manifestId
  );

  const linesQuery = useQuery({
    queryKey: ['cangxu-manifest-lines', manifestId],
    enabled: Boolean(manifestId),
    queryFn: async () => {
      const response = await api.get(
        apiUrl(ApiEndpoints.cangxu_manifest_line_list),
        { params: { manifest: manifestId, limit: 200 } }
      );
      return listResults(response.data as ApiList<ManifestLine>);
    }
  });

  const exceptionsQuery = useQuery({
    queryKey: ['cangxu-receipt-exceptions', shipmentId],
    enabled: shipped,
    queryFn: async () => {
      const response = await api.get(
        apiUrl(ApiEndpoints.cangxu_receipt_exception_list),
        {
          params: {
            receipt_line__receipt__manifest__shipment: shipmentId,
            state: 'open',
            limit: 100
          }
        }
      );
      return listResults(response.data as ApiList<ReceiptException>);
    }
  });

  const resolveMutation = useMutation({
    mutationFn: async ({
      id,
      resolution
    }: { id: number; resolution: string }) => {
      await api.post(
        apiUrl(ApiEndpoints.cangxu_receipt_exception_resolve, id),
        { resolution }
      );
    },
    onSuccess: async () => {
      notifications.show({
        title: t`Delivery difference closed`,
        message: t`The follow-up resolution was recorded.`,
        color: 'green'
      });
      await queryClient.invalidateQueries({
        queryKey: ['cangxu-receipt-exceptions', shipmentId]
      });
    },
    onError: () => {
      notifications.show({
        title: t`Could not close delivery difference`,
        message: t`Enter a resolution and check your sales order permission.`,
        color: 'red'
      });
    }
  });

  const receiptMutation = useMutation({
    mutationFn: async () => {
      const key = requestKey.current ?? idempotencyKey();
      requestKey.current = key;
      const lines = (linesQuery.data ?? []).map((line) => {
        const lineId = recordId(line);
        const value = values[lineId] ?? {
          quantity: line.quantity,
          condition: 'ok',
          notes: ''
        };
        return {
          manifest_line: lineId,
          quantity_received: String(value.quantity),
          condition: value.condition,
          notes: value.notes
        };
      });
      const response = await api.post(
        apiUrl(ApiEndpoints.cangxu_shipment_receipt_list),
        {
          manifest: Number(manifestId),
          idempotency_key: key,
          recipient_name: recipientName,
          is_final: isFinal,
          notes,
          lines
        }
      );
      return response.data;
    },
    onSuccess: async () => {
      notifications.show({
        title: isFinal ? t`Receipt completed` : t`Partial receipt recorded`,
        message: t`The receipt and any delivery differences were recorded. Stock balances were not changed.`,
        color: 'green'
      });
      requestKey.current = undefined;
      setValues({});
      setNotes('');
      setManifestId(null);
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: ['cangxu-shipment-manifests', shipmentId]
        }),
        queryClient.invalidateQueries({
          queryKey: ['cangxu-manifest-lines', manifestId]
        }),
        queryClient.invalidateQueries({
          queryKey: ['cangxu-receipt-exceptions', shipmentId]
        })
      ]);
    },
    onError: () => {
      notifications.show({
        title: t`Receipt was not confirmed`,
        message: t`Keep this form open and retry. The same request key will prevent a duplicate receipt.`,
        color: 'red'
      });
    }
  });

  function updateLine(lineId: number, update: Partial<ReceiptValue>) {
    const line = (linesQuery.data ?? []).find(
      (candidate) => recordId(candidate) === lineId
    );
    if (!line) return;
    setValues((current) => ({
      ...current,
      [lineId]: {
        quantity: current[lineId]?.quantity ?? line.quantity,
        condition: current[lineId]?.condition ?? 'ok',
        notes: current[lineId]?.notes ?? '',
        ...update
      }
    }));
  }

  if (!shipped) return null;

  return (
    <Paper withBorder radius='md' p='md'>
      <Stack>
        <Group justify='space-between'>
          <Text fw={600}>{t`Customer receipt`}</Text>
          {selectedManifest?.signed_at && (
            <Badge color='green'>{t`Receipt finalized`}</Badge>
          )}
        </Group>
        {manifestsQuery.isError && (
          <Alert color='red' title={t`Could not load package manifests`}>
            {t`Check your sales order access and reload this page.`}
          </Alert>
        )}
        {manifests.length === 0 && !manifestsQuery.isFetching && (
          <Text c='dimmed' size='sm'>
            {t`No verified package manifest is available for this shipment.`}
          </Text>
        )}
        {manifests.length > 0 && openManifests.length === 0 && (
          <Text c='dimmed' size='sm'>
            {t`All verified packages have a final receipt.`}
          </Text>
        )}
        {openManifests.length > 0 && (
          <>
            <Select
              label={t`Verified package`}
              placeholder={t`Select a package to record receipt`}
              data={openManifests.map((manifest) => ({
                value: String(recordId(manifest)),
                label: manifest.package_code
              }))}
              value={manifestId}
              onChange={(value) => {
                setManifestId(value);
                setValues({});
                requestKey.current = undefined;
              }}
            />
            {manifestId && (
              <>
                {linesQuery.isError && (
                  <Alert color='red' title={t`Could not load package contents`}>
                    {t`Reload the shipment page and try again.`}
                  </Alert>
                )}
                {!!linesQuery.data?.length && (
                  <Table.ScrollContainer minWidth={680}>
                    <Table verticalSpacing='sm'>
                      <Table.Thead>
                        <Table.Tr>
                          <Table.Th>{t`Expected item`}</Table.Th>
                          <Table.Th>{t`Packed`}</Table.Th>
                          <Table.Th>{t`Received`}</Table.Th>
                          <Table.Th>{t`Condition`}</Table.Th>
                          <Table.Th>{t`Notes`}</Table.Th>
                        </Table.Tr>
                      </Table.Thead>
                      <Table.Tbody>
                        {linesQuery.data.map((line) => {
                          const lineId = recordId(line);
                          const current = values[lineId];
                          return (
                            <Table.Tr key={lineId}>
                              <Table.Td>
                                <Stack gap={0}>
                                  <Text size='sm'>
                                    {line.stock_item_detail?.part_detail
                                      ?.name ??
                                      t`Stock item ${line.stock_item}`}
                                  </Text>
                                  <Text size='xs' c='dimmed'>
                                    {line.stock_item_detail?.serial ??
                                      line.item_role ??
                                      ''}
                                  </Text>
                                </Stack>
                              </Table.Td>
                              <Table.Td>{line.quantity}</Table.Td>
                              <Table.Td>
                                <NumberInput
                                  aria-label={t`Received quantity for item ${line.stock_item}`}
                                  min={0}
                                  max={Number(line.quantity)}
                                  decimalScale={5}
                                  value={current?.quantity ?? line.quantity}
                                  onChange={(quantity) => {
                                    requestKey.current = undefined;
                                    updateLine(lineId, { quantity });
                                  }}
                                />
                              </Table.Td>
                              <Table.Td>
                                <Select
                                  aria-label={t`Condition for item ${line.stock_item}`}
                                  data={[
                                    { value: 'ok', label: t`As expected` },
                                    { value: 'short', label: t`Short` },
                                    { value: 'damaged', label: t`Damaged` },
                                    {
                                      value: 'wrong_item',
                                      label: t`Wrong item`
                                    }
                                  ]}
                                  value={current?.condition ?? 'ok'}
                                  onChange={(condition) => {
                                    if (condition) {
                                      requestKey.current = undefined;
                                      updateLine(lineId, { condition });
                                    }
                                  }}
                                />
                              </Table.Td>
                              <Table.Td>
                                <TextInput
                                  aria-label={t`Notes for item ${line.stock_item}`}
                                  placeholder={t`Required for a discrepancy`}
                                  value={current?.notes ?? ''}
                                  onChange={(event) => {
                                    requestKey.current = undefined;
                                    updateLine(lineId, {
                                      notes: event.currentTarget.value
                                    });
                                  }}
                                />
                              </Table.Td>
                            </Table.Tr>
                          );
                        })}
                      </Table.Tbody>
                    </Table>
                  </Table.ScrollContainer>
                )}
                <Group grow>
                  <TextInput
                    label={t`Recipient`}
                    value={recipientName}
                    onChange={(event) => {
                      requestKey.current = undefined;
                      setRecipientName(event.currentTarget.value);
                    }}
                  />
                  <Select
                    label={t`Receipt stage`}
                    data={[
                      { value: 'partial', label: t`Partial receipt` },
                      { value: 'final', label: t`Final receipt` }
                    ]}
                    value={isFinal ? 'final' : 'partial'}
                    onChange={(value) => {
                      requestKey.current = undefined;
                      setIsFinal(value === 'final');
                    }}
                  />
                </Group>
                <TextInput
                  label={t`Receipt notes`}
                  value={notes}
                  onChange={(event) => {
                    requestKey.current = undefined;
                    setNotes(event.currentTarget.value);
                  }}
                />
                <Button
                  onClick={() => receiptMutation.mutate()}
                  loading={receiptMutation.isPending}
                  disabled={
                    !manifestId ||
                    !linesQuery.data?.length ||
                    receiptMutation.isPending
                  }
                >
                  {isFinal ? t`Finalize receipt` : t`Record partial receipt`}
                </Button>
              </>
            )}
          </>
        )}
        {!!exceptionsQuery.data?.length && (
          <Stack gap='sm'>
            <Text fw={600}>{t`Open delivery differences`}</Text>
            {exceptionsQuery.data.map((exception) => (
              <Paper key={exception.id} withBorder radius='sm' p='sm'>
                <Stack gap='xs'>
                  <Group justify='space-between'>
                    <Text fw={500}>
                      {exception.kind === 'short'
                        ? t`Short received`
                        : exception.kind === 'damaged'
                          ? t`Damaged on arrival`
                          : t`Unexpected item received`}
                    </Text>
                    <Text size='sm' c='dimmed'>
                      {t`Expected`}: {exception.expected_quantity} ·{' '}
                      {t`Received`}: {exception.received_quantity}
                    </Text>
                  </Group>
                  {exception.notes && (
                    <Text size='sm' c='dimmed'>
                      {exception.notes}
                    </Text>
                  )}
                  <Textarea
                    label={t`Resolution`}
                    value={resolutions[exception.id] ?? ''}
                    onChange={(event) =>
                      setResolutions((current) => ({
                        ...current,
                        [exception.id]: event.currentTarget.value
                      }))
                    }
                  />
                  <Button
                    variant='light'
                    loading={resolveMutation.isPending}
                    disabled={!resolutions[exception.id]?.trim()}
                    onClick={() =>
                      resolveMutation.mutate({
                        id: exception.id,
                        resolution: resolutions[exception.id]?.trim() ?? ''
                      })
                    }
                  >
                    {t`Close difference`}
                  </Button>
                </Stack>
              </Paper>
            ))}
          </Stack>
        )}
      </Stack>
    </Paper>
  );
}
