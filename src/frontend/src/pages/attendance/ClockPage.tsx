import { t } from '@lingui/core/macro';
import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Container,
  Group,
  Loader,
  Stack,
  Text,
  TextInput,
  Title
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { IconClock, IconClockCheck, IconClockX } from '@tabler/icons-react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import utc from 'dayjs/plugin/utc';
import { useCallback, useEffect, useMemo, useState } from 'react';

dayjs.extend(utc);

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { PageDetail } from '../../components/nav/PageDetail';
import { useApi } from '../../contexts/ApiContext';

interface ClockStatus {
  clocked_in: boolean;
  current_entry: ClockEntry | null;
  last_entry: ClockEntry | null;
}

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

export default function ClockPage() {
  const api = useApi();
  const queryClient = useQueryClient();
  const [location, setLocation] = useState('');
  const [notes, setNotes] = useState('');
  const [showDetails, { toggle: toggleDetails }] = useDisclosure(false);

  const statusQuery = useQuery<ClockStatus>({
    queryKey: ['attendance_status'],
    queryFn: () =>
      api.get(apiUrl(ApiEndpoints.attendance_status)).then((r) => r.data),
    refetchOnMount: true
  });

  const clockMutation = useMutation({
    mutationFn: (action: 'in' | 'out') =>
      api.post(apiUrl(ApiEndpoints.attendance_clock), {
        action,
        location: location || undefined,
        notes: notes || undefined
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['attendance_status'] });
      setNotes('');
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail || error?.message;
      notifications.show({
        title: t`Clock Action Failed`,
        message: detail || t`An error occurred`,
        color: 'red'
      });
    }
  });

  const [elapsed, setElapsed] = useState('');

  useEffect(() => {
    if (!statusQuery.data?.clocked_in || !statusQuery.data?.current_entry) {
      setElapsed('');
      return;
    }

    const update = () => {
      const start = dayjs.utc(statusQuery.data!.current_entry!.clock_in);
      const diff = dayjs().diff(start, 'second');
      const h = Math.floor(diff / 3600);
      const m = Math.floor((diff % 3600) / 60);
      const s = diff % 60;
      setElapsed(
        `${h}h ${String(m).padStart(2, '0')}m ${String(s).padStart(2, '0')}s`
      );
    };

    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [statusQuery.data]);

  const handleClockAction = useCallback(() => {
    if (statusQuery.data?.clocked_in) {
      clockMutation.mutate('out');
    } else {
      clockMutation.mutate('in');
    }
  }, [statusQuery.data?.clocked_in, clockMutation]);

  const status = statusQuery.data;
  const isLoading = statusQuery.isLoading;
  const isError = statusQuery.isError;

  const buttonIcon = useMemo(() => {
    if (clockMutation.isPending) return <Loader size='sm' color='white' />;
    return status?.clocked_in ? (
      <IconClockX size={24} />
    ) : (
      <IconClock size={24} />
    );
  }, [clockMutation.isPending, status?.clocked_in]);

  return (
    <Container size='xs' py='xl'>
      <PageDetail title={t`Attendance`} />
      <Center>
        <Card maw={480} w='100%' padding='xl' radius='md' withBorder>
          <Stack align='center' gap='lg'>
            <Stack align='center' gap={4}>
              <Title order={3}>{dayjs().format('dddd, MMMM D, YYYY')}</Title>
              <Text c='dimmed' size='sm'>
                {dayjs().format('h:mm A')}
              </Text>
            </Stack>

            {isLoading && (
              <Stack align='center' gap='sm'>
                <Loader />
                <Text c='dimmed' size='sm'>
                  {t`Loading status...`}
                </Text>
              </Stack>
            )}

            {isError && (
              <Alert color='red' title={t`Error`}>
                {t`Could not load clock status. Please try again.`}
              </Alert>
            )}

            {!isLoading && !isError && (
              <>
                <Badge
                  size='xl'
                  radius='sm'
                  variant='filled'
                  color={status?.clocked_in ? 'green' : 'gray'}
                  leftSection={
                    status?.clocked_in ? (
                      <IconClockCheck size={18} />
                    ) : (
                      <IconClock size={18} />
                    )
                  }
                >
                  {status?.clocked_in ? t`Clocked In` : t`Clocked Out`}
                </Badge>

                {status?.clocked_in && status?.current_entry && (
                  <Stack align='center' gap={2}>
                    <Text size='sm' c='dimmed'>
                      {t`Clocked in at`}{' '}
                      {dayjs
                        .utc(status.current_entry.clock_in)
                        .local()
                        .format('h:mm A')}
                    </Text>
                    {status.current_entry.location && (
                      <Text size='sm' c='dimmed'>
                        {t`Location`}: {status.current_entry.location}
                      </Text>
                    )}
                    <Text size='xl' fw={700} ff='monospace'>
                      {elapsed}
                    </Text>
                  </Stack>
                )}

                {!status?.clocked_in && status?.last_entry && (
                  <Stack align='center' gap={2}>
                    <Text size='sm' c='dimmed'>
                      {t`Last clock out`}:{' '}
                      {dayjs
                        .utc(status.last_entry.clock_out)
                        .local()
                        .format('h:mm A')}
                    </Text>
                    {status.last_entry.duration && (
                      <Text size='sm' c='dimmed'>
                        {t`Session`}: {status.last_entry.duration}
                      </Text>
                    )}
                  </Stack>
                )}

                {!status?.clocked_in && !status?.last_entry && (
                  <Text size='sm' c='dimmed'>
                    {t`Welcome! Clock in to get started.`}
                  </Text>
                )}

                <Button
                  fullWidth
                  size='lg'
                  color={status?.clocked_in ? 'red' : 'green'}
                  onClick={handleClockAction}
                  loading={clockMutation.isPending}
                  leftSection={buttonIcon}
                >
                  {status?.clocked_in ? t`Clock Out` : t`Clock In`}
                </Button>

                <Group w='100%' justify='center'>
                  <Button
                    variant='subtle'
                    size='compact-sm'
                    onClick={toggleDetails}
                  >
                    {showDetails ? t`Hide details` : t`Add location / notes`}
                  </Button>
                </Group>

                {showDetails && (
                  <Stack w='100%' gap='sm'>
                    <TextInput
                      label={t`Location`}
                      placeholder={t`Stand or area`}
                      value={location}
                      onChange={(e) => setLocation(e.currentTarget.value)}
                    />
                    <TextInput
                      label={t`Notes`}
                      placeholder={t`Optional note`}
                      value={notes}
                      onChange={(e) => setNotes(e.currentTarget.value)}
                    />
                  </Stack>
                )}
              </>
            )}
          </Stack>
        </Card>
      </Center>
    </Container>
  );
}
