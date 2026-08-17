import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Alert,
  Divider,
  Grid,
  Group,
  Paper,
  Space,
  Stack,
  Text
} from '@mantine/core';
import { randomId, useListState, useLocalStorage } from '@mantine/hooks';
import { IconAlertCircle, IconQuestionMark } from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { ActionButton } from '@lib/components/ActionButton';
import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { hideNotification, showNotification } from '@mantine/notifications';
import dayjs from 'dayjs';
import { api } from '../../App';
import { BarcodeInput } from '../../components/barcodes/BarcodeInput';
import type { BarcodeScanItem } from '../../components/barcodes/BarcodeScanItem';
import PageTitle from '../../components/nav/PageTitle';
import { InvenTreeIcon } from '../../functions/icons';
import { showApiErrorMessage } from '../../functions/notifications';
import { useCreateApiFormModal } from '../../hooks/UseForm';
import { useUserState } from '../../states/UserState';
import BarcodeScanTable from '../../tables/general/BarcodeScanTable';

function stockCreatePayload(item: Record<string, any>) {
  return {
    quantity: item.quantity,
    ...(item.location ? { location: item.location } : {})
  };
}

export default function Scan() {
  const user = useUserState();
  const [history, historyHandlers] = useListState<BarcodeScanItem>([]);

  const [historyStorage, setHistoryStorage] = useLocalStorage<
    BarcodeScanItem[]
  >({
    key: 'scan-history',
    defaultValue: []
  });

  const [selection, setSelection] = useState<string[]>([]);

  const fetchInstance = useCallback(
    (item: BarcodeScanItem) => {
      if (!item.model || !item.pk) {
        return;
      }

      // Parts may be scanned more than once (each scan is a stock item to create).
      // Other models still de-duplicate — scanning the same stock item twice is noise.
      const isDuplicate =
        item.model !== ModelType.part &&
        history.some((i) => i.model == item.model && i.pk == item.pk);

      if (isDuplicate) {
        hideNotification('duplicate-barcode');
        showNotification({
          id: 'duplicate-barcode',
          title: t`Duplicate`,
          message: t`Item already scanned`,
          color: 'orange'
        });
        return;
      }

      const model_info = ModelInformationDict[item.model];

      api
        .get(apiUrl(model_info.api_endpoint, item.pk))
        .then((response) => {
          item.instance = response.data;
          historyHandlers.append(item);
        })
        .catch((error) => {
          showApiErrorMessage({
            error: error,
            title: t`API Error`,
            message: t`Failed to fetch instance data`
          });
        });
    },
    [history]
  );

  const scanBarcode = useCallback(
    (barcode: string) => {
      api
        .post(apiUrl(ApiEndpoints.barcode), { barcode: barcode })
        .then((response) => {
          const data = response?.data ?? {};

          let match = false;

          for (const model_type of Object.keys(ModelInformationDict)) {
            if (data[model_type]?.pk) {
              match = true;
              fetchInstance({
                id: randomId(),
                barcode: barcode,
                data: data,
                timestamp: dayjs().toDate(),
                source: 'scan',
                model: model_type as ModelType,
                pk: data[model_type]?.pk
              });
            }
          }

          if (!match) {
            historyHandlers.append({
              id: randomId(),
              barcode: barcode,
              data: data,
              timestamp: dayjs().toDate(),
              source: 'scan'
            });
          }
        })
        .catch((error) => {
          showApiErrorMessage({
            error: error,
            message: t`Failed to scan barcode`,
            title: t`Scan Error`,
            field: 'error'
          });
        });
    },
    [fetchInstance]
  );

  useEffect(() => {
    if (history.length === 0) return;
    setHistoryStorage(history);
  }, [history]);

  useEffect(() => {
    historyHandlers.setState(historyStorage);
  }, [historyStorage]);

  const selectedItems: BarcodeScanItem[] = useMemo(() => {
    return history.filter((item) => selection.includes(item.id));
  }, [selection, history]);

  const selectedPartPks = useMemo(
    () =>
      selectedItems
        .filter((item) => item.model === ModelType.part && item.pk)
        .map((item) => item.pk as number),
    [selectedItems]
  );

  const partPksRef = useRef(selectedPartPks);
  partPksRef.current = selectedPartPks;

  const canAddStock = user.hasAddRole(UserRoles.stock);

  const bulkCreateStock = useCreateApiFormModal({
    url: ApiEndpoints.stock_item_list,
    title: t`Create Stock Items`,
    successMessage: null,
    fields: {
      part: {
        value: selectedPartPks[0],
        hidden: true
      },
      quantity: {},
      location: {}
    },
    initialData: {
      part: selectedPartPks[0],
      quantity: 1
    },
    preFormContent:
      selectedPartPks.length > 1 ? (
        <Alert color='blue' mb='sm'>
          <Trans>
            Creating stock items for {selectedPartPks.length} parts with the
            same quantity and location
          </Trans>
        </Alert>
      ) : undefined,
    processFormData: (data) => ({
      ...data,
      part: partPksRef.current[0]
    }),
    onFormSuccess: async (response: any) => {
      const created = Array.isArray(response) ? response[0] : response;
      const template = stockCreatePayload(created);
      const remaining = partPksRef.current.slice(1);

      const results = await Promise.allSettled(
        remaining.map((part) =>
          api.post(apiUrl(ApiEndpoints.stock_item_list), { ...template, part })
        )
      );

      const failed = results.filter((r) => r.status === 'rejected');
      const createdCount = 1 + remaining.length - failed.length;

      if (createdCount > 0) {
        showNotification({
          title: t`Success`,
          message: t`Created ${createdCount} stock item(s)`,
          color: 'green'
        });
      }

      failed.forEach((result) => {
        if (result.status !== 'rejected') return;
        showApiErrorMessage({
          error: result.reason,
          title: t`Failed to create stock item`
        });
      });

      setSelection([]);
    }
  });

  const SelectedActions = useMemo(() => {
    const uniqueObjectTypes = new Set(selectedItems.map((item) => item.model));

    if (uniqueObjectTypes.size === 0) {
      return (
        <Group gap={0}>
          <IconQuestionMark color='orange' />
          <Trans>Selected elements are not known</Trans>
        </Group>
      );
    }

    if (uniqueObjectTypes.size > 1) {
      return (
        <Group gap={0}>
          <IconAlertCircle color='orange' />
          <Trans>Multiple object types selected</Trans>
        </Group>
      );
    }

    if (uniqueObjectTypes.has(ModelType.part) && selectedPartPks.length > 0) {
      return (
        <>
          <Text fz='sm' c='dimmed'>
            <Trans>Create Stock Items</Trans>
          </Text>
          <Group>
            <ActionButton
              icon={<InvenTreeIcon icon='add' />}
              tooltip={t`Create stock items for selected parts`}
              disabled={!canAddStock}
              onClick={() => bulkCreateStock.open()}
            />
          </Group>
        </>
      );
    }

    return (
      <Text fz='sm' c='dimmed'>
        <Trans>Scan parts to create stock items</Trans>
      </Text>
    );
  }, [selectedItems, selectedPartPks, bulkCreateStock, canAddStock]);

  return (
    <>
      <PageTitle title={t`Barcode Scanning`} />
      <Group justify='space-between'>
        <Group justify='left'>
          <StylishText size='xl'>
            <Trans>Barcode Scanning</Trans>
          </StylishText>
        </Group>
      </Group>
      <Space h={'md'} />
      <Grid maw={'100%'}>
        <Grid.Col span={4}>
          <Paper p='sm' shadow='xs'>
            <Stack gap='xs'>
              <StylishText size='lg'>{t`Barcode Input`}</StylishText>
              <Divider />
              <BarcodeInput onScan={scanBarcode} />
            </Stack>
          </Paper>
          <Paper p='sm' shadow='xs'>
            <Stack gap='xs'>
              <StylishText size='lg'>{t`Action`}</StylishText>
              <Divider />
              {selection.length === 0 ? (
                <Alert title={t`No Items Selected`} color='blue'>
                  <Trans>Scan and select items to perform actions</Trans>
                </Alert>
              ) : (
                <>
                  <Text>
                    <Trans>{selection.length} items selected</Trans>
                  </Text>
                  {SelectedActions}
                </>
              )}
            </Stack>
          </Paper>
        </Grid.Col>
        <Grid.Col span={8}>
          <Paper p='sm' shadow='xs'>
            <Stack gap='xs'>
              <Group justify='space-between'>
                <StylishText size='lg'>{t`Scanned Items`}</StylishText>
              </Group>
              <Divider />
              <BarcodeScanTable
                records={history}
                onItemsSelected={(ids: string[]) => {
                  setSelection(ids);
                }}
                onItemsDeleted={(ids: string[]) => {
                  const newHistory = history.filter(
                    (item) => !ids.includes(item.id)
                  );

                  historyHandlers.setState(newHistory);
                  setHistoryStorage(newHistory);
                }}
              />
            </Stack>
          </Paper>
        </Grid.Col>
      </Grid>
      {bulkCreateStock.modal}
    </>
  );
}
