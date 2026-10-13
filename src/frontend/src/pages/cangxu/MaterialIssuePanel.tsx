import { t } from '@lingui/core/macro';
import {
  Alert,
  Button,
  Group,
  NumberInput,
  Paper,
  Select,
  Stack,
  Tabs,
  Text,
  TextInput
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { type FormEvent, useMemo, useRef, useState } from 'react';
import { createRequestId } from '../../functions/requestId';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { useApi } from '../../contexts/ApiContext';

type ApiList<T> = T[] | { results?: T[] };

type BuildOrder = {
  pk: number;
  reference: string;
  title?: string;
  part_detail?: { name?: string; IPN?: string };
  status: number;
  status_text?: string;
  quantity: number | string;
  completed: number | string;
};

type BuildLine = {
  pk: number;
  build: number;
  part: number;
  consumable: boolean;
  trackable: boolean;
  quantity: number | string;
  consumed: number | string;
  part_detail?: { name?: string; IPN?: string };
};

type StockLocation = {
  pk: number;
  name: string;
  external: boolean;
  structural: boolean;
};

type StockItem = {
  pk: number;
  part: number;
  part_detail?: { name?: string; IPN?: string };
  serial?: string | null;
  batch?: string | null;
  quantity: number | string;
  location?: number | null;
  location_detail?: { name?: string } | null;
  status: number;
  in_stock?: boolean;
  allocated?: boolean;
  belongs_to?: number | null;
  consumed_by?: number | null;
  customer?: number | null;
  sales_order?: number | null;
};

type MaterialIssue = {
  id: number;
  build_line: number;
  build_reference: string;
  part_name: string;
  part_code?: string | null;
  stock_item: number;
  quantity: string;
  returned_quantity: string;
  remaining_quantity: string;
};

function listResults<T>(payload: ApiList<T>): T[] {
  return Array.isArray(payload) ? payload : (payload.results ?? []);
}

function issueStockLabel(item: StockItem) {
  return `${item.part_detail?.name ?? t`Stock item ${item.pk}`} · ${item.part_detail?.IPN ?? t`No part code`} · ${t`Quantity`}: ${item.quantity} · ${item.location_detail?.name ?? ''}`;
}

function requestKey() {
  return createRequestId();
}

export default function MaterialIssuePanel() {
  const api = useApi();
  const queryClient = useQueryClient();
  const issueKey = useRef<string | undefined>(undefined);
  const returnKey = useRef<string | undefined>(undefined);
  const [buildId, setBuildId] = useState<string | null>(null);
  const [lineId, setLineId] = useState<string | null>(null);
  const [stockSearch, setStockSearch] = useState('');
  const [stockItemId, setStockItemId] = useState<string | null>(null);
  const [selectedStockSnapshot, setSelectedStockSnapshot] =
    useState<StockItem | null>(null);
  const [issueQuantity, setIssueQuantity] = useState<number | string>('');
  const [issueNotes, setIssueNotes] = useState('');
  const [returnIssueId, setReturnIssueId] = useState<string | null>(null);
  const [returnQuantity, setReturnQuantity] = useState<number | string>('');
  const [returnLocationId, setReturnLocationId] = useState<string | null>(null);
  const [returnNotes, setReturnNotes] = useState('');

  const buildsQuery = useQuery({
    queryKey: ['cangxu-material-builds'],
    queryFn: async () => {
      const response = await api.get(apiUrl(ApiEndpoints.build_order_list), {
        params: { limit: 100, ordering: '-creation_date', part_detail: true }
      });
      return listResults(response.data as ApiList<BuildOrder>).filter(
        (build) =>
          [10, 20, 25].includes(build.status) &&
          Number(build.completed) < Number(build.quantity)
      );
    }
  });

  const linesQuery = useQuery({
    queryKey: ['cangxu-material-build-lines', buildId],
    enabled: Boolean(buildId),
    queryFn: async () => {
      const response = await api.get(apiUrl(ApiEndpoints.build_line_list), {
        params: {
          build: buildId,
          consumable: true,
          limit: 100,
          part_detail: true
        }
      });
      return listResults(response.data as ApiList<BuildLine>).filter(
        (line) =>
          line.consumable &&
          !line.trackable &&
          Number(line.quantity) > Number(line.consumed)
      );
    }
  });

  const locationsQuery = useQuery({
    queryKey: ['cangxu-material-internal-locations'],
    queryFn: async () => {
      const response = await api.get(apiUrl(ApiEndpoints.stock_location_list), {
        params: { limit: 200 }
      });
      return listResults(response.data as ApiList<StockLocation>).filter(
        (location) => !location.external && !location.structural
      );
    }
  });

  const stockQuery = useQuery({
    queryKey: ['cangxu-material-stock-search', stockSearch],
    enabled: !stockItemId && stockSearch.trim().length >= 2,
    queryFn: async () => {
      const response = await api.get(apiUrl(ApiEndpoints.stock_item_list), {
        params: {
          search: stockSearch.trim(),
          limit: 30,
          part_detail: true,
          location_detail: true
        }
      });
      const internalLocations = new Set(
        (locationsQuery.data ?? []).map((location) => location.pk)
      );
      const requiredPart = selectedLine?.part;
      return listResults(response.data as ApiList<StockItem>).filter(
        (item) =>
          item.part === requiredPart &&
          item.status === 10 &&
          item.location != null &&
          internalLocations.has(item.location) &&
          !item.belongs_to &&
          !item.consumed_by &&
          !item.customer &&
          !item.sales_order &&
          !item.allocated &&
          Number(item.quantity) > 0
      );
    }
  });

  const issuesQuery = useQuery({
    queryKey: ['cangxu-material-issues'],
    queryFn: async () => {
      const response = await api.get(
        apiUrl(ApiEndpoints.cangxu_material_issue_list),
        { params: { limit: 100 } }
      );
      return listResults(response.data as ApiList<MaterialIssue>).filter(
        (issue) => Number(issue.remaining_quantity) > 0
      );
    }
  });

  const issueMutation = useMutation({
    mutationFn: async () => {
      let idempotencyKey = issueKey.current;
      if (!idempotencyKey) {
        idempotencyKey = requestKey();
        issueKey.current = idempotencyKey;
      }
      const response = await api.post(
        apiUrl(ApiEndpoints.cangxu_material_issue_list),
        {
          build_line: Number(lineId),
          stock_item: Number(stockItemId),
          quantity: String(issueQuantity),
          idempotency_key: idempotencyKey,
          notes: issueNotes
        }
      );
      return response.data as MaterialIssue;
    },
    onSuccess: async () => {
      notifications.show({
        title: t`Material issued`,
        message: t`The build line and stock history have been updated.`,
        color: 'green'
      });
      issueKey.current = undefined;
      setStockItemId(null);
      setSelectedStockSnapshot(null);
      setStockSearch('');
      setIssueQuantity('');
      setIssueNotes('');
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['cangxu-material-issues'] }),
        queryClient.invalidateQueries({
          queryKey: ['cangxu-material-stock-search']
        }),
        queryClient.invalidateQueries({
          queryKey: ['cangxu-material-build-lines', buildId]
        })
      ]);
    },
    onError: () => {
      notifications.show({
        title: t`Issue failed`,
        message: t`The stock was not issued. Review the selected build line and available stock, then retry.`,
        color: 'red'
      });
    }
  });

  const returnMutation = useMutation({
    mutationFn: async () => {
      let idempotencyKey = returnKey.current;
      if (!idempotencyKey) {
        idempotencyKey = requestKey();
        returnKey.current = idempotencyKey;
      }
      const response = await api.post(
        apiUrl(
          ApiEndpoints.cangxu_material_issue_return,
          Number(returnIssueId)
        ),
        {
          quantity: String(returnQuantity),
          location: Number(returnLocationId),
          idempotency_key: idempotencyKey,
          notes: returnNotes
        }
      );
      return response.data as MaterialIssue;
    },
    onSuccess: async () => {
      notifications.show({
        title: t`Material returned`,
        message: t`The material is back in the selected internal location.`,
        color: 'green'
      });
      returnKey.current = undefined;
      setReturnIssueId(null);
      setReturnQuantity('');
      setReturnLocationId(null);
      setReturnNotes('');
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['cangxu-material-issues'] }),
        queryClient.invalidateQueries({
          queryKey: ['cangxu-material-stock-search']
        }),
        queryClient.invalidateQueries({
          queryKey: ['cangxu-material-build-lines']
        })
      ]);
    },
    onError: () => {
      notifications.show({
        title: t`Return failed`,
        message: t`The return was not recorded. Check the quantity and destination location, then retry.`,
        color: 'red'
      });
    }
  });

  const selectedLine = useMemo(
    () => linesQuery.data?.find((line) => String(line.pk) === lineId),
    [lineId, linesQuery.data]
  );
  const selectedStockItem = useMemo(
    () =>
      selectedStockSnapshot?.pk === Number(stockItemId)
        ? selectedStockSnapshot
        : stockQuery.data?.find((item) => String(item.pk) === stockItemId),
    [selectedStockSnapshot, stockItemId, stockQuery.data]
  );
  const selectedIssue = useMemo(
    () => issuesQuery.data?.find((issue) => String(issue.id) === returnIssueId),
    [issuesQuery.data, returnIssueId]
  );

  function submitIssue(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !lineId ||
      !stockItemId ||
      !Number(issueQuantity) ||
      Number(issueQuantity) <= 0
    ) {
      return;
    }
    issueMutation.mutate();
  }

  function submitReturn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (
      !returnIssueId ||
      !returnLocationId ||
      !Number(returnQuantity) ||
      Number(returnQuantity) <= 0
    ) {
      return;
    }
    returnMutation.mutate();
  }

  const issueStockOptions = (stockQuery.data ?? []).map((item) => ({
    value: String(item.pk),
    label: issueStockLabel(item)
  }));
  const buildOptions = (buildsQuery.data ?? []).map((build) => ({
    value: String(build.pk),
    label: `${build.reference} · ${build.part_detail?.name ?? build.title ?? t`Build order`} · ${build.status_text ?? ''}`
  }));
  const lineOptions = (linesQuery.data ?? []).map((line) => ({
    value: String(line.pk),
    label: `${line.part_detail?.name ?? t`BOM material`} · ${line.part_detail?.IPN ?? t`No part code`} · ${t`Remaining`}: ${Number(line.quantity) - Number(line.consumed)}`
  }));
  const issueOptions = (issuesQuery.data ?? []).map((issue) => ({
    value: String(issue.id),
    label: `${issue.build_reference} · ${issue.part_name} · ${t`Remaining`}: ${issue.remaining_quantity}`
  }));
  const locationOptions = (locationsQuery.data ?? []).map((location) => ({
    value: String(location.pk),
    label: location.name
  }));

  return (
    <Paper p='md' radius='md' withBorder>
      <Stack gap='sm'>
        <div>
          <Text fw={600}>{t`Consumable materials`}</Text>
          <Text size='sm' c='dimmed'>
            {t`Issue material to a build order or return unused quantity to an internal stock location.`}
          </Text>
        </div>
        <Tabs defaultValue='issue'>
          <Tabs.List>
            <Tabs.Tab value='issue'>{t`Issue material`}</Tabs.Tab>
            <Tabs.Tab value='return'>{t`Return unused material`}</Tabs.Tab>
          </Tabs.List>
          <Tabs.Panel value='issue' pt='md'>
            <form onSubmit={submitIssue}>
              <Stack gap='sm'>
                <Select
                  label={t`Build order`}
                  placeholder={t`Select an active build order`}
                  data={buildOptions}
                  value={buildId}
                  onChange={(value) => {
                    issueKey.current = undefined;
                    setBuildId(value);
                    setLineId(null);
                    setStockItemId(null);
                    setSelectedStockSnapshot(null);
                    setStockSearch('');
                    setIssueQuantity('');
                  }}
                  searchable
                  clearable
                  nothingFoundMessage={t`No active build orders were found.`}
                  disabled={buildsQuery.isLoading || buildsQuery.isError}
                  error={
                    buildsQuery.isError
                      ? t`Build orders could not be loaded.`
                      : undefined
                  }
                />
                <Select
                  label={t`Consumable BOM line`}
                  placeholder={t`Select a material required by the build`}
                  data={lineOptions}
                  value={lineId}
                  onChange={(value) => {
                    issueKey.current = undefined;
                    setLineId(value);
                    setStockItemId(null);
                    setSelectedStockSnapshot(null);
                    setStockSearch('');
                    setIssueQuantity('');
                  }}
                  searchable
                  clearable
                  nothingFoundMessage={t`No untracked consumable lines remain on this build.`}
                  disabled={
                    !buildId || linesQuery.isLoading || linesQuery.isError
                  }
                  error={
                    linesQuery.isError
                      ? t`Build materials could not be loaded.`
                      : undefined
                  }
                />
                {selectedLine && (
                  <Text size='xs' c='dimmed'>
                    {t`Remaining BOM requirement`}:{' '}
                    {Number(selectedLine.quantity) -
                      Number(selectedLine.consumed)}
                  </Text>
                )}
                <Select
                  label={t`Available stock`}
                  placeholder={t`Search by part code, serial number, or name`}
                  data={issueStockOptions}
                  value={stockItemId}
                  searchValue={stockSearch}
                  onSearchChange={(value) => {
                    if (
                      stockItemId &&
                      selectedStockSnapshot &&
                      value === issueStockLabel(selectedStockSnapshot)
                    ) {
                      setStockSearch(value);
                      return;
                    }
                    setStockSearch(value);
                    setStockItemId(null);
                    setSelectedStockSnapshot(null);
                    setIssueQuantity('');
                  }}
                  onChange={(value) => {
                    issueKey.current = undefined;
                    setStockItemId(value);
                    setSelectedStockSnapshot(
                      value
                        ? (stockQuery.data?.find(
                            (item) => String(item.pk) === value
                          ) ?? null)
                        : null
                    );
                  }}
                  // Stock search runs on the server and can match batch/SN fields
                  // that are intentionally absent from the visible option label.
                  filter={({ options }) => options}
                  searchable
                  clearable
                  nothingFoundMessage={
                    stockSearch.trim().length < 2
                      ? t`Enter at least two characters to search stock.`
                      : t`No available internal stock matched this search.`
                  }
                  disabled={!lineId || locationsQuery.isLoading}
                  error={
                    stockQuery.isError ? t`Stock search failed.` : undefined
                  }
                />
                {stockQuery.isFetching && (
                  <Text size='xs' c='dimmed'>{t`Searching stock…`}</Text>
                )}
                {selectedStockItem && (
                  <Text size='xs' c='dimmed'>
                    {t`Available quantity`}: {selectedStockItem.quantity}
                  </Text>
                )}
                <Group align='flex-end' grow wrap='wrap'>
                  <NumberInput
                    label={t`Issue quantity`}
                    min={0.00001}
                    max={
                      selectedStockItem && selectedLine
                        ? Math.min(
                            Number(selectedStockItem.quantity),
                            Number(selectedLine.quantity) -
                              Number(selectedLine.consumed)
                          )
                        : undefined
                    }
                    decimalScale={5}
                    value={issueQuantity}
                    onChange={(value) => {
                      issueKey.current = undefined;
                      setIssueQuantity(value);
                    }}
                    disabled={!stockItemId}
                    required
                  />
                  <TextInput
                    label={t`Reason or handoff note`}
                    value={issueNotes}
                    onChange={(event) => {
                      issueKey.current = undefined;
                      setIssueNotes(event.currentTarget.value);
                    }}
                    maxLength={500}
                  />
                </Group>
                {buildsQuery.isError && (
                  <Alert color='red' title={t`Workflow unavailable`}>
                    {t`Build orders are unavailable. Check your access and refresh the page.`}
                  </Alert>
                )}
                <Group justify='flex-end'>
                  <Button
                    type='submit'
                    loading={issueMutation.isPending}
                    disabled={
                      !lineId ||
                      !stockItemId ||
                      !Number(issueQuantity) ||
                      Number(issueQuantity) <= 0
                    }
                  >
                    {t`Confirm issue`}
                  </Button>
                </Group>
              </Stack>
            </form>
          </Tabs.Panel>
          <Tabs.Panel value='return' pt='md'>
            <form onSubmit={submitReturn}>
              <Stack gap='sm'>
                <Select
                  label={t`Original material issue`}
                  placeholder={t`Select an issue with quantity remaining`}
                  data={issueOptions}
                  value={returnIssueId}
                  onChange={(value) => {
                    returnKey.current = undefined;
                    setReturnIssueId(value);
                  }}
                  searchable
                  clearable
                  nothingFoundMessage={t`No material issues are awaiting return.`}
                  disabled={issuesQuery.isLoading || issuesQuery.isError}
                  error={
                    issuesQuery.isError
                      ? t`Material issue history could not be loaded.`
                      : undefined
                  }
                />
                {selectedIssue && (
                  <Text size='xs' c='dimmed'>
                    {t`Issued`}: {selectedIssue.quantity} ·{' '}
                    {t`Already returned`}: {selectedIssue.returned_quantity} ·{' '}
                    {t`Can return`}: {selectedIssue.remaining_quantity}
                  </Text>
                )}
                <Group align='flex-end' grow wrap='wrap'>
                  <NumberInput
                    label={t`Return quantity`}
                    min={0.00001}
                    max={
                      selectedIssue
                        ? Number(selectedIssue.remaining_quantity)
                        : undefined
                    }
                    decimalScale={5}
                    value={returnQuantity}
                    onChange={(value) => {
                      returnKey.current = undefined;
                      setReturnQuantity(value);
                    }}
                    disabled={!returnIssueId}
                    required
                  />
                  <Select
                    label={t`Return to location`}
                    placeholder={t`Select an internal stock location`}
                    data={locationOptions}
                    value={returnLocationId}
                    onChange={(value) => {
                      returnKey.current = undefined;
                      setReturnLocationId(value);
                    }}
                    searchable
                    clearable
                    disabled={
                      locationsQuery.isLoading || locationsQuery.isError
                    }
                    error={
                      locationsQuery.isError
                        ? t`Internal locations could not be loaded.`
                        : undefined
                    }
                  />
                </Group>
                <TextInput
                  label={t`Return condition or note`}
                  value={returnNotes}
                  onChange={(event) => {
                    returnKey.current = undefined;
                    setReturnNotes(event.currentTarget.value);
                  }}
                  maxLength={500}
                />
                <Group justify='flex-end'>
                  <Button
                    type='submit'
                    loading={returnMutation.isPending}
                    disabled={
                      !returnIssueId ||
                      !returnLocationId ||
                      !Number(returnQuantity) ||
                      Number(returnQuantity) <= 0
                    }
                  >
                    {t`Confirm return`}
                  </Button>
                </Group>
              </Stack>
            </form>
          </Tabs.Panel>
        </Tabs>
      </Stack>
    </Paper>
  );
}
