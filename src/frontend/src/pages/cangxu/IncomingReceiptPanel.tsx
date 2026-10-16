import { t } from '@lingui/core/macro';
import {
  Alert,
  Badge,
  Button,
  Group,
  MultiSelect,
  NumberInput,
  Paper,
  Select,
  Stack,
  Table,
  Text,
  TextInput
} from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { useApi } from '../../contexts/ApiContext';
import { AttachmentTable } from '../../tables/general/AttachmentTable';

type ListResponse<T> = T[] | { results?: T[] };
type Receipt = {
  id: number;
  purchase_order_line: number;
  purchase_order_number: string;
  part_name: string;
  part_code: string;
  quantity: string;
  status: number;
  batch_code: string;
  serial_numbers: string[];
  stock_items: number[];
  inspection_id: number | null;
  received_at: string;
};
type StockLocation = {
  pk: number;
  name: string;
  pathstring?: string;
  external: boolean;
};
type Inspection = {
  id: number;
  receipt: number;
  state: string;
  sampling_method: string;
  sampled_quantity: string | null;
  model_result: string;
  quantity_result: string;
  packaging_condition: string;
  appearance_issues: string[];
  other_notes: string;
  warehouse_signer: number | null;
  purchaser_signer: number | null;
};
type Feedback = {
  id: number;
  department: string;
  message: string;
  response: string;
};

function rows<T>(payload: ListResponse<T>): T[] {
  return Array.isArray(payload) ? payload : (payload.results ?? []);
}

export default function IncomingReceiptPanel() {
  const api = useApi();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [debouncedSearch] = useDebouncedValue(search, 250);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [inspection, setInspection] = useState<Partial<Inspection>>({});
  const [feedbackDepartment, setFeedbackDepartment] = useState<string | null>(
    null
  );
  const [feedbackMessage, setFeedbackMessage] = useState('');
  const [feedbackResponses, setFeedbackResponses] = useState<
    Record<number, string>
  >({});
  const [outcome, setOutcome] = useState<string | null>(null);
  const [dispositionNotes, setDispositionNotes] = useState('');
  const [returnLocation, setReturnLocation] = useState<number | string>('');
  const [returnReference, setReturnReference] = useState('');
  const [approvalNotes, setApprovalNotes] = useState('');

  const appearanceChoices = useMemo(
    () =>
      [
        ['scratch', t`Surface scratch`],
        ['structure_deformed', t`Structure deformed`],
        ['gold_finger_scratch', t`Gold finger scratched`],
        ['part_missing', t`Part missing`],
        ['label_abnormal', t`Label abnormal`],
        ['port_damaged', t`Port damaged`],
        ['stain', t`Stain`],
        ['pin_bent', t`Bent pin`],
        ['component_abnormal', t`Electronic component abnormal`],
        ['other', t`Other appearance issue`]
      ].map(([value, label]) => ({ value, label })),
    []
  );

  const locationsQuery = useQuery({
    queryKey: ['cangxu-external-return-locations'],
    queryFn: async () => {
      const response = await api.get(apiUrl(ApiEndpoints.stock_location_list), {
        params: { limit: 1000 }
      });
      return rows(response.data as ListResponse<StockLocation>).filter(
        (location) => location.external
      );
    }
  });

  const receiptsQuery = useQuery({
    queryKey: ['cangxu-incoming-receipts', debouncedSearch],
    queryFn: async () => {
      const response = await api.get(
        apiUrl(ApiEndpoints.cangxu_purchase_receipt_list),
        {
          params: {
            search: debouncedSearch.trim(),
            limit: 100,
            ordering: '-received_at'
          }
        }
      );
      return rows(response.data as ListResponse<Receipt>);
    }
  });
  const receipt = receiptsQuery.data?.find((item) => item.id === selectedId);
  const inspectionQuery = useQuery({
    queryKey: ['cangxu-incoming-inspection', selectedId],
    enabled: selectedId !== null,
    queryFn: async () => {
      const response = await api.get(
        apiUrl(ApiEndpoints.cangxu_receipt_inspection_list),
        { params: { receipt: selectedId, limit: 20 } }
      );
      return rows(response.data as ListResponse<Inspection>)[0] ?? null;
    }
  });
  const feedbackQuery = useQuery({
    queryKey: ['cangxu-incoming-feedback', inspectionQuery.data?.id],
    enabled: Boolean(inspectionQuery.data?.id),
    queryFn: async () => {
      const response = await api.get(
        apiUrl(ApiEndpoints.cangxu_receipt_feedback_list),
        { params: { inspection: inspectionQuery.data?.id, limit: 50 } }
      );
      return rows(response.data as ListResponse<Feedback>);
    }
  });
  const dispositionsQuery = useQuery({
    queryKey: ['cangxu-incoming-dispositions', inspectionQuery.data?.id],
    enabled: Boolean(inspectionQuery.data?.id),
    queryFn: async () => {
      const response = await api.get(
        apiUrl(ApiEndpoints.cangxu_receipt_disposition_list),
        { params: { inspection: inspectionQuery.data?.id, limit: 10 } }
      );
      return rows(response.data as ListResponse<any>);
    }
  });

  useEffect(() => {
    if (inspectionQuery.data) setInspection(inspectionQuery.data);
    else if (selectedId && !inspectionQuery.isFetching) setInspection({});
  }, [inspectionQuery.data, inspectionQuery.isFetching, selectedId]);

  function invalidate() {
    void queryClient.invalidateQueries({
      queryKey: ['cangxu-incoming-receipts']
    });
    void queryClient.invalidateQueries({
      queryKey: ['cangxu-incoming-inspection']
    });
    void queryClient.invalidateQueries({
      queryKey: ['cangxu-incoming-feedback']
    });
    void queryClient.invalidateQueries({
      queryKey: ['cangxu-incoming-dispositions']
    });
  }
  function runAction(action: () => Promise<unknown>, success: string) {
    action()
      .then(() => {
        notifications.show({ message: success, color: 'green' });
        invalidate();
      })
      .catch(() => {
        notifications.show({
          message: t`The incoming receipt action failed. Check access and required fields.`,
          color: 'red'
        });
      });
  }

  const saveInspection = useMutation({
    mutationFn: async () => {
      if (!receipt) throw new Error('Receipt is not selected');
      const payload = {
        receipt: receipt.id,
        sampling_method: inspection.sampling_method,
        sampled_quantity: inspection.sampled_quantity,
        model_result: inspection.model_result,
        quantity_result: inspection.quantity_result,
        packaging_condition: inspection.packaging_condition,
        appearance_issues: inspection.appearance_issues ?? [],
        other_notes: inspection.other_notes ?? ''
      };
      if (inspection.id) {
        return api.patch(
          apiUrl(ApiEndpoints.cangxu_receipt_inspection_detail, inspection.id),
          payload
        );
      }
      return api.post(
        apiUrl(ApiEndpoints.cangxu_receipt_inspection_list),
        payload
      );
    },
    onSuccess: invalidate
  });

  function update(field: keyof Inspection, value: unknown) {
    setInspection((current) => ({ ...current, [field]: value }));
  }

  return (
    <Stack gap='md'>
      <TextInput
        label={t`Search by purchase order, part name, or part code`}
        value={search}
        onChange={(event) => setSearch(event.currentTarget.value)}
      />
      {receiptsQuery.isError && (
        <Alert color='red'>{t`Receipts could not be loaded.`}</Alert>
      )}
      <Paper withBorder radius='md' p='xs'>
        <Table.ScrollContainer minWidth={740}>
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>{t`Purchase order`}</Table.Th>
                <Table.Th>{t`Part`}</Table.Th>
                <Table.Th>{t`Quantity`}</Table.Th>
                <Table.Th>{t`Batch`}</Table.Th>
                <Table.Th>{t`Stock state`}</Table.Th>
                <Table.Th />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {(receiptsQuery.data ?? []).map((item) => (
                <Table.Tr key={item.id}>
                  <Table.Td>{item.purchase_order_number}</Table.Td>
                  <Table.Td>
                    {item.part_name} · {item.part_code}
                  </Table.Td>
                  <Table.Td>{item.quantity}</Table.Td>
                  <Table.Td>{item.batch_code || '—'}</Table.Td>
                  <Table.Td>
                    <Badge color={item.status === 75 ? 'orange' : 'green'}>
                      {item.status === 75 ? t`Quarantined` : t`Available`}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Button
                      size='xs'
                      variant={selectedId === item.id ? 'filled' : 'light'}
                      onClick={() => setSelectedId(item.id)}
                    >{t`Inspect and archive`}</Button>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Table.ScrollContainer>
      </Paper>

      {receipt && (
        <Paper withBorder radius='md' p='md'>
          <Stack>
            <Text fw={700}>
              {receipt.purchase_order_number} · {receipt.part_name} ·{' '}
              {receipt.part_code}
            </Text>
            <Text size='sm' c='dimmed'>
              {t`Received quantity`}: {receipt.quantity} · {t`Serial numbers`}:{' '}
              {receipt.serial_numbers.join(', ') || '—'}
            </Text>
            {inspectionQuery.isError && (
              <Alert color='red'>{t`Inspection record could not be loaded.`}</Alert>
            )}
            {inspectionQuery.data?.state !== 'pass' &&
              inspectionQuery.data?.state !== 'exception' && (
                <>
                  <Group grow>
                    <Select
                      label={t`Inspection method`}
                      data={[
                        { value: 'full', label: t`Full inspection` },
                        { value: 'sample', label: t`Sample inspection` }
                      ]}
                      value={inspection.sampling_method ?? null}
                      onChange={(value) => update('sampling_method', value)}
                    />
                    <NumberInput
                      label={t`Inspected quantity`}
                      value={inspection.sampled_quantity ?? ''}
                      min={0}
                      max={Number(receipt.quantity)}
                      onChange={(value) => update('sampled_quantity', value)}
                    />
                    <Select
                      label={t`Model`}
                      data={[
                        { value: 'match', label: t`Matches` },
                        { value: 'wrong', label: t`Wrong model` },
                        {
                          value: 'other_missing',
                          label: t`Other model missing`
                        }
                      ]}
                      value={inspection.model_result ?? null}
                      onChange={(value) => update('model_result', value)}
                    />
                  </Group>
                  <Group grow>
                    <Select
                      label={t`Quantity`}
                      data={[
                        { value: 'match', label: t`Matches` },
                        { value: 'short', label: t`Shortage` },
                        { value: 'excess', label: t`Excess` }
                      ]}
                      value={inspection.quantity_result ?? null}
                      onChange={(value) => update('quantity_result', value)}
                    />
                    <Select
                      label={t`Packaging`}
                      data={[
                        { value: 'intact', label: t`Intact` },
                        { value: 'damaged', label: t`Damaged` },
                        { value: 'wet', label: t`Wet` },
                        { value: 'deformed', label: t`Deformed` }
                      ]}
                      value={inspection.packaging_condition ?? null}
                      onChange={(value) => update('packaging_condition', value)}
                    />
                  </Group>
                  <MultiSelect
                    label={t`Appearance findings`}
                    data={appearanceChoices}
                    value={inspection.appearance_issues ?? []}
                    onChange={(value) => update('appearance_issues', value)}
                  />
                  <TextInput
                    label={t`Notes`}
                    value={inspection.other_notes ?? ''}
                    onChange={(event) =>
                      update('other_notes', event.currentTarget.value)
                    }
                  />
                  <Group>
                    <Button
                      loading={saveInspection.isPending}
                      onClick={() => saveInspection.mutate()}
                    >{t`Save inspection`}</Button>
                    {inspection.id && (
                      <>
                        <Button
                          variant='light'
                          onClick={() =>
                            runAction(
                              () =>
                                api.post(
                                  apiUrl(
                                    ApiEndpoints.cangxu_receipt_inspection_sign,
                                    inspection.id
                                  ),
                                  { role: 'warehouse' }
                                ),
                              t`Warehouse signed`
                            )
                          }
                        >{t`Warehouse sign`}</Button>
                        <Button
                          variant='light'
                          onClick={() =>
                            runAction(
                              () =>
                                api.post(
                                  apiUrl(
                                    ApiEndpoints.cangxu_receipt_inspection_sign,
                                    inspection.id
                                  ),
                                  { role: 'purchaser' }
                                ),
                              t`Purchaser signed`
                            )
                          }
                        >{t`Purchaser sign`}</Button>
                        <Button
                          color='teal'
                          onClick={() =>
                            runAction(
                              () =>
                                api.post(
                                  apiUrl(
                                    ApiEndpoints.cangxu_receipt_inspection_submit,
                                    inspection.id
                                  ),
                                  {}
                                ),
                              t`Inspection submitted`
                            )
                          }
                        >{t`Submit inspection`}</Button>
                      </>
                    )}
                  </Group>
                </>
              )}
            {inspectionQuery.data && (
              <Badge
                w='fit-content'
                color={
                  inspectionQuery.data.state === 'exception' ? 'red' : 'green'
                }
              >
                {inspectionQuery.data.state}
              </Badge>
            )}
            {inspectionQuery.data?.state === 'exception' && (
              <>
                <Group align='end' grow>
                  <Select
                    label={t`Send feedback to`}
                    data={[
                      { value: 'technical', label: t`Technical support` },
                      { value: 'purchasing', label: t`Purchasing` }
                    ]}
                    value={feedbackDepartment}
                    onChange={setFeedbackDepartment}
                  />
                  <TextInput
                    label={t`Feedback request`}
                    value={feedbackMessage}
                    onChange={(event) =>
                      setFeedbackMessage(event.currentTarget.value)
                    }
                  />
                  <Button
                    disabled={!feedbackDepartment || !feedbackMessage.trim()}
                    onClick={() =>
                      runAction(
                        () =>
                          api.post(
                            apiUrl(ApiEndpoints.cangxu_receipt_feedback_list),
                            {
                              inspection: inspection.id,
                              department: feedbackDepartment,
                              message: feedbackMessage
                            }
                          ),
                        t`Feedback recorded`
                      )
                    }
                  >{t`Record feedback`}</Button>
                </Group>
                {(feedbackQuery.data ?? []).map((item) => (
                  <Group key={item.id} align='end' wrap='wrap'>
                    <Text size='sm' maw={360}>
                      {item.department}: {item.message}
                      {item.response ? ` — ${item.response}` : ''}
                    </Text>
                    {!item.response && (
                      <>
                        <TextInput
                          label={t`Department response`}
                          value={feedbackResponses[item.id] ?? ''}
                          onChange={(event) =>
                            setFeedbackResponses((current) => ({
                              ...current,
                              [item.id]: event.currentTarget.value
                            }))
                          }
                        />
                        <Button
                          disabled={!feedbackResponses[item.id]?.trim()}
                          onClick={() =>
                            runAction(
                              () =>
                                api.post(
                                  apiUrl(
                                    ApiEndpoints.cangxu_receipt_feedback_respond,
                                    item.id
                                  ),
                                  { response: feedbackResponses[item.id] }
                                ),
                              t`Feedback response recorded`
                            )
                          }
                        >{t`Record response`}</Button>
                      </>
                    )}
                  </Group>
                ))}
                <Group align='end' grow>
                  <Select
                    label={t`Disposition`}
                    data={[
                      { value: 'normal', label: t`Normal receipt` },
                      { value: 'concession', label: t`Concession receipt` },
                      { value: 'return', label: t`Return to supplier` }
                    ]}
                    value={outcome}
                    onChange={setOutcome}
                  />
                  <TextInput
                    label={t`Disposition notes`}
                    value={dispositionNotes}
                    onChange={(event) =>
                      setDispositionNotes(event.currentTarget.value)
                    }
                  />
                  {outcome === 'return' && (
                    <>
                      <Select
                        label={t`External return location`}
                        data={(locationsQuery.data ?? []).map((location) => ({
                          value: String(location.pk),
                          label: location.pathstring ?? location.name
                        }))}
                        value={returnLocation ? String(returnLocation) : null}
                        onChange={(value) => setReturnLocation(value ?? '')}
                        searchable
                      />
                      <TextInput
                        label={t`Return shipment reference`}
                        value={returnReference}
                        onChange={(event) =>
                          setReturnReference(event.currentTarget.value)
                        }
                      />
                    </>
                  )}
                  <Button
                    disabled={!outcome || !dispositionNotes.trim()}
                    onClick={() =>
                      runAction(
                        () =>
                          api.post(
                            apiUrl(
                              ApiEndpoints.cangxu_receipt_disposition_list
                            ),
                            {
                              inspection: inspection.id,
                              outcome,
                              request_notes: dispositionNotes,
                              ...(outcome === 'return'
                                ? {
                                    return_location: returnLocation,
                                    return_shipment_reference: returnReference
                                  }
                                : {})
                            }
                          ),
                        t`Disposition submitted`
                      )
                    }
                  >{t`Request disposition`}</Button>
                </Group>
                {(dispositionsQuery.data ?? [])
                  .filter((item) => item.state === 'pending')
                  .map((item) => (
                    <Group key={item.id} align='end'>
                      <Text>
                        {t`Pending`}: {item.outcome}
                      </Text>
                      <TextInput
                        label={t`Approval note`}
                        value={approvalNotes}
                        onChange={(event) =>
                          setApprovalNotes(event.currentTarget.value)
                        }
                      />
                      <Button
                        onClick={() =>
                          runAction(
                            () =>
                              api.post(
                                apiUrl(
                                  ApiEndpoints.cangxu_receipt_disposition_approve,
                                  item.id
                                ),
                                { approved: true, notes: approvalNotes }
                              ),
                            t`Disposition approved`
                          )
                        }
                      >{t`Approve`}</Button>
                      <Button
                        color='red'
                        onClick={() =>
                          runAction(
                            () =>
                              api.post(
                                apiUrl(
                                  ApiEndpoints.cangxu_receipt_disposition_approve,
                                  item.id
                                ),
                                { approved: false, notes: approvalNotes }
                              ),
                            t`Disposition rejected`
                          )
                        }
                      >{t`Reject`}</Button>
                    </Group>
                  ))}
              </>
            )}
            <details>
              <summary>{t`Incoming receipt photos and forms`}</summary>
              <AttachmentTable
                model_type={ModelType.purchasereceipt}
                model_id={receipt.id}
              />
            </details>
          </Stack>
        </Paper>
      )}
    </Stack>
  );
}
