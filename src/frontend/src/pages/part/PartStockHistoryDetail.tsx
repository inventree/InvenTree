import { RowDeleteAction, RowEditAction } from '@lib/components/RowActions';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import { apiUrl } from '@lib/functions/Api';
import { AddItemButton } from '@lib/index';
import type { TableColumn } from '@lib/types/Tables';
import { t } from '@lingui/core/macro';
import { type ChartTooltipProps, LineChart } from '@mantine/charts';
import {
  Accordion,
  Center,
  Divider,
  Loader,
  Paper,
  SimpleGrid,
  Text
} from '@mantine/core';
import dayjs from 'dayjs';
import { useCallback, useMemo, useState } from 'react';
import { StylishText } from '../../components/items/StylishText';
import { formatDate, formatPriceRange } from '../../defaults/formatters';
import { partStocktakeFields } from '../../forms/PartForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { useUserState } from '../../states/UserState';
import { DateColumn, DecimalColumn } from '../../tables/ColumnRenderers';
import { InvenTreeTable } from '../../tables/InvenTreeTable';
import { StockTrackingTable } from '../../tables/stock/StockTrackingTable';

/*
 * Render a tooltip for the chart, with correct date information
 */
function ChartTooltip({ label, payload }: Readonly<ChartTooltipProps>) {
  const formattedLabel: string = useMemo(() => {
    if (label && typeof label === 'number') {
      return formatDate(dayjs(label).format('YYYY-MM-DD')) ?? label;
    } else if (!!label) {
      return label.toString();
    } else {
      return '';
    }
  }, [label]);

  if (!payload) {
    return null;
  }

  const quantity = payload.find((item) => item.name == 'quantity');
  const value_min = payload.find((item) => item.name == 'value_min');
  const value_max = payload.find((item) => item.name == 'value_max');

  return (
    <Paper px='md' py='sm' withBorder shadow='md' radius='md'>
      <Text key='title'>{formattedLabel}</Text>
      <Divider />
      <Text key='quantity' fz='sm'>
        {t`Quantity`} : {quantity?.value}
      </Text>
      <Text key='values' fz='sm'>
        {t`Value`} : {formatPriceRange(value_min?.value, value_max?.value)}
      </Text>
    </Paper>
  );
}

export function PartStocktakePanel({ partId }: Readonly<{ partId: number }>) {
  const user = useUserState();
  const table = useTable('part-stocktake');

  const stocktakeFields = useMemo(() => partStocktakeFields(), []);

  const [selectedStocktake, setSelectedStocktake] = useState<
    number | undefined
  >(undefined);

  const editStocktakeEntry = useEditApiFormModal({
    pk: selectedStocktake,
    url: ApiEndpoints.part_stocktake_list,
    title: t`Edit Stocktake Entry`,
    fields: stocktakeFields,
    table: table
  });

  const deleteStocktakeEntry = useDeleteApiFormModal({
    pk: selectedStocktake,
    url: ApiEndpoints.part_stocktake_list,
    title: t`Delete Stocktake Entry`,
    table: table
  });

  const newStocktakeEntry = useCreateApiFormModal({
    title: t`Generate Stocktake Report`,
    url: apiUrl(ApiEndpoints.part_stocktake_generate),
    fields: {
      part: {
        value: partId,
        disabled: true
      },
      generate_entry: {
        value: true,
        hidden: true
      }
    },
    submitText: t`Generate`,
    successMessage: t`Stocktake report scheduled for generation`
  });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      DateColumn({}),
      DecimalColumn({
        accessor: 'item_count',
        title: t`Stock Items`,
        switchable: true,
        sortable: false
      }),
      DecimalColumn({
        accessor: 'quantity',
        title: t`Stock Quantity`,
        sortable: false,
        switchable: false
      }),
      {
        accessor: 'cost',
        title: t`Stock Value`,
        sortable: false,
        render: (record: any) => {
          return formatPriceRange(record.cost_min, record.cost_max, {
            currency: record.cost_min_currency
          });
        }
      }
    ];
  }, []);

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.part) || !user.isSuperuser(),
          onClick: () => {
            setSelectedStocktake(record.pk);
            editStocktakeEntry.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.part),
          onClick: () => {
            setSelectedStocktake(record.pk);
            deleteStocktakeEntry.open();
          }
        })
      ];
    },
    [user]
  );

  const chartData = useMemo(() => {
    const records =
      table.records?.map((record: any) => {
        return {
          date: new Date(record.date).valueOf(),
          quantity: record.quantity,
          value_min: Number.parseFloat(record.cost_min),
          value_max: Number.parseFloat(record.cost_max)
        };
      }) ?? [];

    // Sort records to ensure correct date order
    return records.sort((a, b) => {
      return a < b ? -1 : 1;
    });
  }, [table.records]);

  // Calculate the date limits of the chart
  const chartLimits: number[] = useMemo(() => {
    let min_date = new Date();
    let max_date = new Date();

    if (chartData.length > 0) {
      min_date = new Date(chartData[0].date);
      max_date = new Date(chartData[chartData.length - 1].date);
    }

    // Expand limits by one day on either side
    min_date.setDate(min_date.getDate() - 1);
    max_date.setDate(max_date.getDate() + 1);

    return [min_date.valueOf(), max_date.valueOf()];
  }, [chartData]);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        hidden={!user.hasAddRole(UserRoles.part)}
        key='add-stocktake'
        tooltip={t`Generate Stocktake Entry`}
        onClick={() => newStocktakeEntry.open()}
      />
    ];
  }, [user]);

  return (
    <>
      {newStocktakeEntry.modal}
      {editStocktakeEntry.modal}
      {deleteStocktakeEntry.modal}
      <SimpleGrid cols={{ base: 1, lg: 2 }}>
        <InvenTreeTable
          url={apiUrl(ApiEndpoints.part_stocktake_list)}
          tableState={table}
          columns={tableColumns}
          props={{
            enableSelection: true,
            enableBulkDelete: true,
            enableDownload: true,
            params: {
              part: partId,
              ordering: '-date'
            },
            rowActions: rowActions,
            tableActions: tableActions
          }}
        />
        {table.isLoading ? (
          <Center>
            <Loader />
          </Center>
        ) : (
          <LineChart
            data={chartData}
            mah={'500px'}
            dataKey='date'
            withLegend
            withYAxis
            withRightYAxis
            yAxisLabel={t`Quantity`}
            rightYAxisLabel={t`Stock Value`}
            tooltipProps={{
              content: ({ label, payload }) => (
                <ChartTooltip label={label} payload={payload} />
              )
            }}
            yAxisProps={{
              allowDataOverflow: false
            }}
            rightYAxisProps={{
              allowDataOverflow: false
            }}
            xAxisProps={{
              scale: 'time',
              type: 'number',
              domain: chartLimits,
              tickFormatter: (value: number) => {
                return formatDate(dayjs(value).format('YYYY-MM-DD'));
              }
            }}
            series={[
              {
                name: 'quantity',
                label: t`Quantity`,
                color: 'blue.6',
                yAxisId: 'left'
              },
              {
                name: 'value_min',
                label: t`Minimum Value`,
                color: 'yellow.6',
                yAxisId: 'right'
              },
              {
                name: 'value_max',
                label: t`Maximum Value`,
                color: 'teal.6',
                yAxisId: 'right'
              }
            ]}
          />
        )}
      </SimpleGrid>
    </>
  );
}

export default function PartStockHistoryDetail({
  partId
}: Readonly<{ partId: number }>) {
  return (
    <Accordion multiple defaultValue={['stocktake']}>
      <Accordion.Item value='tracking'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Stock Tracking`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <StockTrackingTable partId={partId} />
        </Accordion.Panel>
      </Accordion.Item>
      <Accordion.Item value='stocktake'>
        <Accordion.Control>
          <StylishText size='lg'>{t`Stocktake Entries`}</StylishText>
        </Accordion.Control>
        <Accordion.Panel>
          <PartStocktakePanel partId={partId} />
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}
