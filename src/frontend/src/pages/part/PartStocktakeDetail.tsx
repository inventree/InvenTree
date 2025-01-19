import { t } from '@lingui/macro';
import { type ChartTooltipProps, LineChart } from '@mantine/charts';
import {
  Center,
  Divider,
  Loader,
  Paper,
  SimpleGrid,
  Text
} from '@mantine/core';
import { useCallback, useMemo, useState } from 'react';

import { AddItemButton } from '../../components/buttons/AddItemButton';
import { formatDate, formatPriceRange } from '../../defaults/formatters';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { UserRoles } from '../../enums/Roles';
import {
  generateStocktakeReportFields,
  partStocktakeFields
} from '../../forms/PartForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useTable } from '../../hooks/UseTable';
import { apiUrl } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import type { TableColumn } from '../../tables/Column';
import { InvenTreeTable } from '../../tables/InvenTreeTable';
import { RowDeleteAction, RowEditAction } from '../../tables/RowActions';

/*
 * Render a tooltip for the chart, with correct date information
 */
function ChartTooltip({ label, payload }: Readonly<ChartTooltipProps>) {
  const formattedLabel: string = useMemo(() => {
    if (label && typeof label === 'number') {
      return formatDate(new Date(label).toISOString()) ?? label;
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

export default function PartStocktakeDetail({
  partId
}: Readonly<{ partId: number }>) {
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

  const generateReport = useCreateApiFormModal({
    url: ApiEndpoints.part_stocktake_report_generate,
    title: t`Generate Stocktake Report`,
    fields: generateStocktakeReportFields(),
    initialData: {
      part: partId
    },
    successMessage: t`Stocktake report scheduled`
  });

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'quantity',
        sortable: true,
        switchable: false
      },
      {
        accessor: 'item_count',
        title: t`Stock Items`,
        switchable: true,
        sortable: true
      },
      {
        accessor: 'cost',
        title: t`Stock Value`,
        render: (record: any) => {
          return formatPriceRange(record.cost_min, record.cost_max, {
            currency: record.cost_min_currency
          });
        }
      },
      {
        accessor: 'date',
        sortable: true
      },
      {
        accessor: 'note'
      }
    ];
  }, []);

  const tableActions = useMemo(() => {
    return [
      <AddItemButton
        key='add'
        tooltip={t`New Stocktake Report`}
        onClick={() => generateReport.open()}
        hidden={!user.hasAddRole(UserRoles.stocktake)}
      />
    ];
  }, [user]);

  const rowActions = useCallback(
    (record: any) => {
      return [
        RowEditAction({
          hidden: !user.hasChangeRole(UserRoles.stocktake),
          onClick: () => {
            setSelectedStocktake(record.pk);
            editStocktakeEntry.open();
          }
        }),
        RowDeleteAction({
          hidden: !user.hasDeleteRole(UserRoles.stocktake),
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
          value_min: record.cost_min,
          value_max: record.cost_max
        };
      }) ?? [];

    // Sort records to ensure correct date order
    records.sort((a, b) => {
      return a < b ? -1 : 1;
    });

    return records;
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

  return (
    <>
      {generateReport.modal}
      {editStocktakeEntry.modal}
      {deleteStocktakeEntry.modal}
      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <InvenTreeTable
          url={apiUrl(ApiEndpoints.part_stocktake_list)}
          tableState={table}
          columns={tableColumns}
          props={{
            params: {
              part: partId
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
            xAxisProps={{
              scale: 'time',
              type: 'number',
              domain: chartLimits,
              tickFormatter: (value: number) => {
                return formatDate(new Date(value).toISOString());
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
