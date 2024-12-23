import { t } from '@lingui/macro';
import {
  ActionIcon,
  Alert,
  Anchor,
  Container,
  ScrollArea,
  Stack,
  Table,
  Text,
  Tooltip
} from '@mantine/core';
import { IconMailCheck } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';

import { api } from '../../../App';
import { formatDate } from '../../../defaults/formatters';
import { ApiEndpoints } from '../../../enums/ApiEndpoints';
import { apiUrl } from '../../../states/ApiState';
import { useUserState } from '../../../states/UserState';
import { StylishText } from '../../items/StylishText';

/**
 * Render a link to an external news item
 */
function NewsLink({ item }: Readonly<{ item: any }>) {
  let link: string = item.link;

  if (link?.startsWith('/')) {
    link = `https://inventree.org${link}`;
  }

  if (link) {
    return (
      <Anchor href={link} target='_blank'>
        {item.title}
      </Anchor>
    );
  } else {
    return <Text>{item.title}</Text>;
  }
}

function NewsItem({
  item,
  onMarkRead
}: Readonly<{
  item: any;
  onMarkRead: (id: number) => void;
}>) {
  const date: string = item.published?.split(' ')[0] ?? '';
  return (
    <Table.Tr>
      <Table.Td>{formatDate(date)}</Table.Td>
      <Table.Td>
        <NewsLink item={item} />
      </Table.Td>
      <Table.Td>
        <Tooltip label={t`Mark as read`}>
          <ActionIcon
            size='sm'
            color='green'
            variant='transparent'
            onClick={() => onMarkRead(item.pk)}
          >
            <IconMailCheck />
          </ActionIcon>
        </Tooltip>
      </Table.Td>
    </Table.Tr>
  );
}

/**
 * A widget which displays a list of news items on the dashboard
 */
export default function NewsWidget() {
  const user = useUserState();

  const newsItems = useQuery({
    queryKey: ['news-items'],
    queryFn: () =>
      api
        .get(apiUrl(ApiEndpoints.news), {
          params: {
            read: false
          }
        })
        .then((response: any) => response.data)
        .catch(() => [])
  });

  const markRead = useCallback(
    (id: number) => {
      api
        .patch(apiUrl(ApiEndpoints.news, id), {
          read: true
        })
        .then(() => {
          newsItems.refetch();
        })
        .catch(() => {});
    },
    [newsItems]
  );

  const hasNews = useMemo(
    () => (newsItems.data?.length ?? 0) > 0,
    [newsItems.data]
  );

  if (!user.isSuperuser()) {
    return (
      <Alert color='red' title={t`Requires Superuser`}>
        <Text>{t`This widget requires superuser permissions`}</Text>
      </Alert>
    );
  }

  return (
    <Stack>
      <StylishText size='xl'>{t`News Updates`}</StylishText>
      <ScrollArea h={400}>
        <Container>
          <Table>
            <Table.Tbody>
              {hasNews ? (
                newsItems.data?.map((item: any) => (
                  <NewsItem key={item.pk} item={item} onMarkRead={markRead} />
                ))
              ) : (
                <Alert color='green' title={t`No News`}>
                  <Text>{t`There are no unread news items`}</Text>
                </Alert>
              )}
            </Table.Tbody>
          </Table>
        </Container>
      </ScrollArea>
    </Stack>
  );
}
