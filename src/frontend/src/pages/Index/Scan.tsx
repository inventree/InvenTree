import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  ActionIcon,
  Alert,
  Button,
  Divider,
  Grid,
  Group,
  Paper,
  Space,
  Stack,
  Text
} from '@mantine/core';
import { randomId, useListState, useLocalStorage } from '@mantine/hooks';
import {
  IconAlertCircle,
  IconArrowMerge,
  IconArrowRight,
  IconNumber,
  IconQuestionMark,
  IconTruckDelivery
} from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { StylishText } from '@lib/components/StylishText';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelInformationDict } from '@lib/enums/ModelInformation';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import { notYetImplemented } from '@lib/functions/Notification';
import { hideNotification, showNotification } from '@mantine/notifications';
import dayjs from 'dayjs';
import { api } from '../../App';
import { BarcodeInput } from '../../components/barcodes/BarcodeInput';
import type { BarcodeScanItem } from '../../components/barcodes/BarcodeScanItem';
import { ConsolidateStockBarcodeModal } from '../../components/barcodes/ConsolidateStockBarcodeModal';
import { MoveStockBarcodeModal } from '../../components/barcodes/MoveStockBarcodeModal';
import { ReceiveStockBarcodeModal } from '../../components/barcodes/ReceiveStockBarcodeModal';
import PageTitle from '../../components/nav/PageTitle';
import { showApiErrorMessage } from '../../functions/notifications';
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
  const [moveModalOpen, setMoveModalOpen] = useState<boolean>(false);
  const [receiveModalOpen, setReceiveModalOpen] = useState<boolean>(false);
  const [consolidateModalOpen, setConsolidateModalOpen] =
    useState<boolean>(false);
  const [clearSelectionToken, setClearSelectionToken] = useState<number>(0);

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

      const model_info = ModelInformationDict[item.model];

      // Request location_detail for stock items (used by move action)
      const params =
        item.model === ModelType.stockitem
          ? { location_detail: true, part_detail: true }
          : {};

      api
        .get(apiUrl(model_info.api_endpoint, item.pk), { params })
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
    [api, history]
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

  // Extract scanned stock locations from history (for move action)
  const scannedLocations = useMemo(() => {
    return history.filter(
      (item) =>
        item.model === ModelType.stocklocation && item.instance?.pk != null
    );
  }, [history]);

  // selected actions component
  const SelectedActions = useMemo(() => {
    const uniqueObjectTypes = new Set(selectedItems.map((item) => item.model));

    if (uniqueObjectTypes.size === 0) {
      return (
        <Group gap={0}>
          <IconQuestionMark color='orange' />
          <Trans>Selected elements are not known</Trans>
        </Group>
      );
    } else if (uniqueObjectTypes.size > 1) {
      return (
        <Group gap={0}>
          <IconAlertCircle color='orange' />
          <Trans>Multiple object types selected</Trans>
        </Group>
      );
    }

    const modelType = [...uniqueObjectTypes][0];
    const canMove =
      modelType === ModelType.stockitem || modelType === ModelType.part;
    const canReceive =
      modelType === ModelType.part || modelType === ModelType.stockitem;

    return (
      <>
        <Text fz='sm' c='dimmed'>
          <Trans>Actions ... </Trans>
        </Text>
        <Group>
          {canMove && (
            <Button
              onClick={() => setMoveModalOpen(true)}
              leftSection={<IconArrowRight size={16} />}
              color='blue'
            >
              <Trans>Move Stock</Trans>
            </Button>
          )}
          {canReceive && (
            <Button
              onClick={() => setReceiveModalOpen(true)}
              leftSection={<IconTruckDelivery size={16} />}
              color='green'
            >
              <Trans>Receive Stock</Trans>
            </Button>
          )}
          {modelType === ModelType.stockitem && (
            <Button
              onClick={() => setConsolidateModalOpen(true)}
              leftSection={<IconArrowMerge size={16} />}
              color='orange'
            >
              <Trans>Consolidate Stock</Trans>
            </Button>
          )}
          {modelType === ModelType.stockitem && (
            <ActionIcon
              onClick={notYetImplemented}
              title={t`Count`}
              variant='default'
            >
              <IconNumber />
            </ActionIcon>
          )}
        </Group>
      </>
    );
  }, [selectedItems]);

  // Determine source and destination locations from scanned locations
  const sourceLocationPk = useMemo(() => {
    return scannedLocations.length > 0
      ? scannedLocations[0].instance.pk
      : undefined;
  }, [scannedLocations]);

  const destLocationPk = useMemo(() => {
    return scannedLocations.length > 1
      ? scannedLocations[1].instance.pk
      : undefined;
  }, [scannedLocations]);

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
                clearSelectionToken={clearSelectionToken}
              />
            </Stack>
          </Paper>
        </Grid.Col>
      </Grid>
      <ConsolidateStockBarcodeModal
        opened={consolidateModalOpen}
        onClose={() => setConsolidateModalOpen(false)}
        onSuccess={() => {
          setSelection([]);
          setClearSelectionToken((t) => t + 1);
        }}
        items={selectedItems}
      />
      <MoveStockBarcodeModal
        opened={moveModalOpen}
        onClose={() => setMoveModalOpen(false)}
        onSuccess={() => {
          setSelection([]);
          setClearSelectionToken((t) => t + 1);
        }}
        items={selectedItems}
        sourceLocationPk={sourceLocationPk}
        destinationLocationPk={destLocationPk}
      />
      <ReceiveStockBarcodeModal
        opened={receiveModalOpen}
        onClose={() => setReceiveModalOpen(false)}
        onSuccess={() => {
          setSelection([]);
          setClearSelectionToken((t) => t + 1);
        }}
        items={selectedItems}
      />
    </>
  );
}
