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
import { useCallback, useEffect, useMemo, useState } from 'react';

import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { StockOperationProps } from '@lib/types/Forms';
import { hideNotification, showNotification } from '@mantine/notifications';
import dayjs from 'dayjs';
import { api } from '../../App';
import { BarcodeInput } from '../../components/barcodes/BarcodeInput';
import type { BarcodeScanItem } from '../../components/barcodes/BarcodeScanItem';
import PageTitle from '../../components/nav/PageTitle';
import { showApiErrorMessage } from '../../functions/notifications';
import { useStockAdjustActions } from '../../hooks/UseStockAdjustActions';
import BarcodeScanTable from '../../tables/general/BarcodeScanTable';

export default function Scan() {
  const [history, historyHandlers] = useListState<BarcodeScanItem>([]);

  const [historyStorage, setHistoryStorage] = useLocalStorage<
    BarcodeScanItem[]
  >({
    key: 'scan-history',
    defaultValue: []
  });

  const [selection, setSelection] = useState<string[]>([]);

  // Fetch the instance data for a given scan item
  const fetchInstanceData = useCallback(async (item: BarcodeScanItem) => {
    const model_info = ModelInformationDict[item.model!];

    return api
      .get(apiUrl(model_info.api_endpoint, item.pk), {
        // Stock adjustment forms require location detail for each item
        params:
          item.model == ModelType.stockitem
            ? { part_detail: true, location_detail: true }
            : undefined
      })
      .then((response) => response.data);
  }, []);

  // Fetch model instance based on scan item
  const fetchInstance = useCallback(
    (item: BarcodeScanItem) => {
      if (!item.model || !item.pk) {
        return;
      }

      // Prevent duplicates
      if (history.find((i) => i.model == item.model && i.pk == item.pk)) {
        hideNotification('duplicate-barcode');

        showNotification({
          id: 'duplicate-barcode',
          title: t`Duplicate`,
          message: t`Item already scanned`,
          color: 'orange'
        });
        return;
      }

      fetchInstanceData(item)
        .then((instance) => {
          item.instance = instance;
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
    [fetchInstanceData, history]
  );

  // Barcode scanning callback function
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

          // If no match is found, add an empty result
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

  // save history data to session storage
  useEffect(() => {
    if (history.length === 0) return;
    setHistoryStorage(history);
  }, [history]);

  // load data from session storage on mount
  useEffect(() => {
    historyHandlers.setState(historyStorage);
  }, [historyStorage]);

  // Items selected for action
  const selectedItems: BarcodeScanItem[] = useMemo(() => {
    return history.filter((item) => selection.includes(item.id));
  }, [selection, history]);

  // Reload instance data for the selected items (e.g. after a stock adjustment)
  const refreshSelectedItems = useCallback(() => {
    const items = selectedItems.filter((item) => item.model && item.pk);

    if (items.length == 0) {
      return;
    }

    Promise.all(
      items.map((item) =>
        fetchInstanceData(item)
          .then((instance) => ({ id: item.id, instance: instance }))
          .catch((error) => ({
            id: item.id,
            // The item no longer exists (e.g. it was merged into another item)
            missing: error?.response?.status == 404
          }))
      )
    ).then((results) => {
      historyHandlers.apply((item) => {
        const result: any = results.find((r) => r.id == item.id);

        if (result?.instance) {
          return { ...item, instance: result.instance };
        } else if (result?.missing) {
          return { ...item, instance: undefined };
        }

        // Retain existing data if the item could not be reloaded
        return item;
      });
    });
  }, [fetchInstanceData, selectedItems]);

  // Scan history may be stale, so reload instance data when the selection changes
  useEffect(() => {
    refreshSelectedItems();
  }, [selection]);

  // The single model type shared by all selected items (if any)
  const selectedModelType: ModelType | undefined = useMemo(() => {
    const modelTypes = new Set(selectedItems.map((item) => item.model));

    return modelTypes.size == 1 ? selectedItems[0]?.model : undefined;
  }, [selectedItems]);

  const stockOperationProps: StockOperationProps = useMemo(() => {
    return {
      items:
        selectedModelType == ModelType.stockitem
          ? selectedItems
              .map((item) => item.instance)
              .filter((instance) => !!instance)
          : [],
      refresh: refreshSelectedItems
    };
  }, [selectedModelType, selectedItems, refreshSelectedItems]);

  const stockAdjustActions = useStockAdjustActions({
    formProps: stockOperationProps,
    enabled: selectedModelType == ModelType.stockitem,
    delete: false
  });

  // selected actions component
  const SelectedActions = useMemo(() => {
    const uniqueObjectTypes = new Set(selectedItems.map((item) => item.model));

    if (uniqueObjectTypes.size > 1) {
      return (
        <Group gap={0}>
          <IconAlertCircle color='orange' />
          <Trans>Multiple object types selected</Trans>
        </Group>
      );
    } else if (!selectedModelType) {
      return (
        <Group gap={0}>
          <IconQuestionMark color='orange' />
          <Trans>Selected elements are not known</Trans>
        </Group>
      );
    }

    if (
      selectedModelType != ModelType.stockitem ||
      !stockAdjustActions.hasActions
    ) {
      return (
        <Text fz='sm' c='dimmed'>
          <Trans>No actions available for the selected items</Trans>
        </Text>
      );
    }

    return (
      <Group justify='space-between'>
        <Text fz='sm' c='dimmed'>
          <Trans>Stock Actions</Trans>
        </Text>
        {stockAdjustActions.dropdown}
      </Group>
    );
  }, [selectedItems, selectedModelType, stockAdjustActions]);

  return (
    <>
      {stockAdjustActions.modals.map((modal) => modal.modal)}
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
    </>
  );
}
