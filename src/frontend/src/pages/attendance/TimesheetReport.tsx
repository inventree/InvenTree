import {
  Alert,
  Card,
  Container,
  Group,
  Loader,
  Select,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { DatePickerInput } from '@mantine/dates';
import { IconCalendar, IconClock, IconUser } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import { useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import useTable from '@lib/hooks/UseTable';
import type { TableFilter } from '@lib/types/Filters';
import type { TableColumn } from '@lib/types/Tables';
import { PageDetail } from '../../components/nav/PageDetail';
import { useApi } from '../../contexts/ApiContext';
import { InvenTreeTable } from '../../tables/InvenTreeTable';

dayjs.extend(utc);

interface ClockEntry {
  pk: number;
  user: number;
  username: string;
  user_full_name: string;
  clock_in: string;
  clock_out: string | null;
  is_clocked_in: boolean;
  duration: string;
  location: string;
  notes: string;
}

interface TimesheetSummary {
  username: string;
  user_full_name: string;
  total_hours: number;
  entry_count: number;
  is_clocked_in: boolean;
}

export default function TimesheetReport() {
  const api = useApi();
  const table = useTable('timesheet-report');

  const [dateFrom, setDateFrom] = useState<string | null>(() => {
    return dayjs().subtract(7, 'day').format('YYYY-MM-DD');
  });
  const [dateTo, setDateTo] = useState<string | null>(
    dayjs().format('YYYY-MM-DD')
  );
  const [selectedUser, setSelectedUser] = useState<string | null>(null);

  const tableParams = useMemo(() => {
    const params: Record<string, any> = {};
    if (dateFrom) {
      params.clock_in_after = dateFrom;
    }
    if (dateTo) {
      params.clock_in_before = dayjs(dateTo).add(1, 'day').format('YYYY-MM-DD');
    }
    if (selectedUser) {
      params.user = selectedUser;
    }
    return params;
  }, [dateFrom, dateTo, selectedUser]);

  const usersQuery = useQuery<{ pk: number; username: string }[]>({
    queryKey: ['user_list'],
    queryFn: () => api.get(apiUrl(ApiEndpoints.user_list)).then((r) => r.data),
    staleTime: 5 * 60 * 1000
  });

  const userOptions = useMemo(() => {
    if (!usersQuery.data) return [];
    return usersQuery.data.map((u: any) => ({
      value: String(u.pk),
      label: u.username
    }));
  }, [usersQuery.data]);

  const summaryQuery = useQuery<TimesheetSummary[]>({
    queryKey: ['timesheet_summary', tableParams],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.attendance_summary), { params: tableParams })
        .then((r) => r.data),
    refetchOnMount: true
  });

  const tableFilters: TableFilter[] = useMemo(() => {
    return [
      {
        name: 'clock_in_after',
        label: 'From',
        type: 'date'
      },
      {
        name: 'clock_in_before',
        label: 'To',
        type: 'date'
      },
      {
        name: 'user',
        label: 'User',
        type: 'api',
        apiUrl: apiUrl(ApiEndpoints.user_list),
        modelRenderer: (instance: any) => instance?.username || String(instance)
      }
    ];
  }, []);

  const tableColumns: TableColumn[] = useMemo(() => {
    return [
      {
        accessor: 'username',
        title: 'User',
        sortable: true
      },
      {
        accessor: 'user_full_name',
        title: 'Full Name',
        sortable: true
      },
      {
        accessor: 'clock_in',
        title: 'Clock In',
        sortable: true,
        render: (record: ClockEntry) =>
          dayjs.utc(record.clock_in).local().format('lll')
      },
      {
        accessor: 'clock_out',
        title: 'Clock Out',
        sortable: true,
        render: (record: ClockEntry) =>
          record.clock_out
            ? dayjs.utc(record.clock_out).local().format('lll')
            : '—'
      },
      {
        accessor: 'duration',
        title: 'Duration',
        sortable: false,
        render: (record: ClockEntry) => {
          if (!record.duration) return '—';
          return record.duration;
        }
      },
      {
        accessor: 'location',
        title: 'Location',
        sortable: true
      },
      {
        accessor: 'notes',
        title: 'Notes',
        sortable: false
      }
    ];
  }, []);

  const totalHours = useMemo(() => {
    if (!summaryQuery.data) return 0;
    return summaryQuery.data.reduce((sum, s) => sum + s.total_hours, 0);
  }, [summaryQuery.data]);

  return (
    <Container size='xl' py='md'>
      <PageDetail title={'Timesheet Report'} />
      <Stack gap='md'>
        <Group grow align='end'>
          <DatePickerInput
            label={'From'}
            leftSection={<IconCalendar size={16} />}
            value={dateFrom}
            onChange={setDateFrom}
            clearable
            maxDate={dateTo || undefined}
          />
          <DatePickerInput
            label={'To'}
            leftSection={<IconCalendar size={16} />}
            value={dateTo}
            onChange={setDateTo}
            clearable
            minDate={dateFrom || undefined}
          />
          <Select
            label={'User'}
            placeholder={'All users'}
            leftSection={<IconUser size={16} />}
            value={selectedUser}
            onChange={setSelectedUser}
            data={userOptions}
            searchable
            clearable
            disabled={usersQuery.isLoading}
          />
        </Group>

        {summaryQuery.isLoading ? (
          <Group gap='sm' justify='center' py='md'>
            <Loader size='sm' />
            <Text c='dimmed'>Loading summary...</Text>
          </Group>
        ) : summaryQuery.isError ? (
          <Alert color='red' title={'Error'}>
            Could not load timesheet summary.
          </Alert>
        ) : (
          <Group grow>
            <Card withBorder radius='md' padding='md'>
              <Stack align='center' gap={4}>
                <IconClock size={24} />
                <Text size='sm' c='dimmed'>
                  Total Hours
                </Text>
                <Title order={2}>{totalHours.toFixed(1)}</Title>
              </Stack>
            </Card>
            <Card withBorder radius='md' padding='md'>
              <Stack align='center' gap={4}>
                <IconUser size={24} />
                <Text size='sm' c='dimmed'>
                  Employees
                </Text>
                <Title order={2}>{summaryQuery.data?.length ?? 0}</Title>
              </Stack>
            </Card>
          </Group>
        )}

        <InvenTreeTable
          url={apiUrl(ApiEndpoints.attendance_entries)}
          tableState={table}
          columns={tableColumns}
          props={{
            params: tableParams,
            enableDownload: true,
            enableSearch: true,
            enableFilters: false,
            defaultSortColumn: 'clock_in',
            tableFilters
          }}
        />
      </Stack>
    </Container>
  );
}
