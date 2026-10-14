import { t } from '@lingui/core/macro';
import { Anchor, Group, Paper, Stack } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { DataTable } from 'mantine-datatable';
import { useMemo } from 'react';
import { Link } from 'react-router-dom';

import { ProgressBar } from '@lib/components/ProgressBar';
import { StylishText } from '@lib/components/StylishText';
import type { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { resolveItem } from '@lib/functions/Conversion';
import { formatDecimal } from '@lib/functions/Formatting';
import { useApi } from '../../contexts/ApiContext';
import { RenderPartColumn } from '../tables/ColumnRenderers';

export interface LineItemProgress {
  value: number;
  maximum: number;
}

export interface LineItemOverviewTableProps {
  // API endpoint which returns the line items for this order
  endpoint: ApiEndpoints;
  // Extra query parameters to filter the line item list (e.g. the order pk)
  params?: Record<string, any>;
  // Accessor for the "part" detail object on each line item record
  partAccessor?: string;
  // Accessor for the target quantity on each line item record
  quantityAccessor?: string;
  // Extract progress information from a line item record.
  // If not provided (or returns null for a record), the quantity is shown as plain text
  progress?: (record: any) => LineItemProgress | null;
  // Title for the progress column
  progressLabel?: string;
  // Name of the panel (within the same PanelGroup) which shows the full line item table
  linkToPanel?: string;
  // Maximum number of line items to display
  limit?: number;
  // Optional title, displayed above the table
  title?: string;
}

/**
 * A minimal, read-only overview of an order's line items - not selectable,
 * searchable, sortable or paginated. Intended for embedding in an order's
 * "Details" panel, alongside the full interactive line item table on a separate panel.
 */
export function LineItemOverviewTable({
  endpoint,
  params,
  partAccessor = 'part_detail',
  quantityAccessor = 'quantity',
  progress,
  progressLabel,
  linkToPanel = 'line-items',
  limit = 10,
  title
}: Readonly<LineItemOverviewTableProps>) {
  const api = useApi();

  const { data, isFetching } = useQuery({
    queryKey: ['line-item-overview', endpoint, params, limit],
    queryFn: () =>
      api
        .get(apiUrl(endpoint), {
          params: { ...params, limit, offset: 0 }
        })
        .then((response) => response.data),
    placeholderData: (previous) => previous
  });

  const records: any[] = data?.results ?? [];
  const count: number = data?.count ?? records.length;

  const columns = useMemo(() => {
    return [
      {
        accessor: 'part',
        title: t`Part`,
        render: (record: any) => (
          <RenderPartColumn part={resolveItem(record, partAccessor)} />
        )
      },
      {
        accessor: 'progress',
        title: progressLabel ?? t`Progress`,
        render: (record: any) => {
          const p = progress?.(record);

          if (p) {
            return (
              <ProgressBar progressLabel value={p.value} maximum={p.maximum} />
            );
          }

          return formatDecimal(resolveItem(record, quantityAccessor));
        }
      }
    ];
  }, [partAccessor, quantityAccessor, progress, progressLabel]);

  return (
    <Paper p='xs' withBorder style={{ width: '100%' }}>
      <Stack gap='xs'>
        {title && <StylishText size='lg'>{title}</StylishText>}
        <DataTable
          idAccessor='pk'
          minHeight={records.length ? undefined : 100}
          records={records}
          columns={columns}
          fetching={isFetching}
          noRecordsText={t`No line items`}
        />
        {count > records.length && (
          <Group justify='right'>
            <Anchor component={Link} to={`../${linkToPanel}`} size='sm'>
              {t`View all ${count} line items`}
            </Anchor>
          </Group>
        )}
      </Stack>
    </Paper>
  );
}
