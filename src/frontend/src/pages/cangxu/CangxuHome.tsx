import { t } from '@lingui/core/macro';
import {
  Alert,
  Anchor,
  Badge,
  Button,
  Card,
  Group,
  Loader,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  Title
} from '@mantine/core';
import {
  IconBuildingFactory2,
  IconClipboardCheck,
  IconPackages,
  IconSearch,
  IconShoppingCart,
  IconTruckDelivery
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type FormEvent, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { apiUrl } from '@lib/functions/Api';
import { api } from '../../App';
import PageTitle from '../../components/nav/PageTitle';
import IncomingReceiptPanel from './IncomingReceiptPanel';
import MaterialIssuePanel from './MaterialIssuePanel';

type StockSearchResult = {
  pk: number;
  serial?: string | null;
  part_detail?: { name?: string; IPN?: string; full_name?: string };
  location_detail?: { name?: string } | null;
  belongs_to?: number | null;
  quantity?: number;
  status_text?: string;
};

export default function CangxuHome() {
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [search, setSearch] = useState('');
  const workflowCards = [
    {
      title: t`Receiving and purchasing`,
      description: t`Review purchase orders, expected stock, and received items.`,
      href: '/purchasing/index/',
      icon: <IconShoppingCart size={22} />
    },
    {
      title: t`Production and assembly`,
      description: t`Open build orders, allocate components, and record finished units.`,
      href: '/manufacturing/index/',
      icon: <IconBuildingFactory2 size={22} />
    },
    {
      title: t`Warehouse and stock`,
      description: t`Find stock, locations, and internal transfer orders.`,
      href: '/stock/',
      icon: <IconPackages size={22} />
    },
    {
      title: t`Delivery and returns`,
      description: t`Review sales shipments, packing, and customer returns.`,
      href: '/sales/index/',
      icon: <IconTruckDelivery size={22} />
    }
  ];

  const stockQuery = useQuery({
    queryKey: ['cangxu-trace-search', search],
    enabled: search.length > 0,
    queryFn: async () => {
      const response = await api.get(apiUrl(ApiEndpoints.stock_item_list), {
        params: {
          search,
          limit: 25,
          part_detail: true,
          location_detail: true
        }
      });
      const payload = response.data;
      return (payload.results ?? payload) as StockSearchResult[];
    }
  });

  function submitSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSearch(input.trim());
  }

  return (
    <Stack gap='lg'>
      <PageTitle title={t`Cangxu Workshop`} />
      <Paper p='lg' radius='md' withBorder>
        <Group justify='space-between' align='flex-start' wrap='wrap'>
          <Stack gap={4}>
            <Badge
              variant='light'
              leftSection={<IconClipboardCheck size={14} />}
            >
              {t`AI server production and warehousing`}
            </Badge>
            <Title order={2}>{t`Cangxu Workshop`}</Title>
            <Text c='dimmed' maw={720}>
              {t`Start common receiving, production, stock, and delivery work here. Search a serial number or part code to open its InvenTree stock history.`}
            </Text>
          </Stack>
          <Button
            variant='light'
            leftSection={<IconSearch size={16} />}
            onClick={() => navigate('/scan/')}
          >
            {t`Scan barcode`}
          </Button>
        </Group>
      </Paper>

      <section>
        <Title order={4} mb='sm'>
          {t`Incoming inspection and archive`}
        </Title>
        <IncomingReceiptPanel />
      </section>

      <section>
        <Title order={4} mb='sm'>
          {t`Common workflows`}
        </Title>
        <SimpleGrid cols={{ base: 1, sm: 2, xl: 4 }}>
          {workflowCards.map((card) => (
            <Card
              key={card.href}
              component={Link}
              to={card.href}
              withBorder
              radius='md'
              padding='md'
              style={{ cursor: 'pointer' }}
            >
              <Stack gap='sm'>
                <Group c='blue' gap='xs'>
                  {card.icon}
                  <Text fw={600} c='var(--mantine-color-text)'>
                    {card.title}
                  </Text>
                </Group>
                <Text size='sm' c='dimmed'>
                  {card.description}
                </Text>
                <Anchor size='sm' underline='never'>
                  {t`Open workflow`} →
                </Anchor>
              </Stack>
            </Card>
          ))}
        </SimpleGrid>
      </section>

      <section>
        <Title order={4} mb='sm'>
          {t`Material issue and return`}
        </Title>
        <MaterialIssuePanel />
      </section>

      <section>
        <Title order={4} mb='sm'>
          {t`Trace a part or unit`}
        </Title>
        <Paper p='md' radius='md' withBorder>
          <form onSubmit={submitSearch}>
            <Group align='flex-end' wrap='wrap'>
              <TextInput
                label={t`Serial number or part code`}
                placeholder={t`Enter a serial number, internal part code, or name`}
                value={input}
                onChange={(event) => setInput(event.currentTarget.value)}
                leftSection={<IconSearch size={16} />}
                style={{ flex: 1 }}
              />
              <Button
                type='submit'
                disabled={!input.trim()}
                loading={stockQuery.isFetching}
              >
                {t`Search stock history`}
              </Button>
            </Group>
          </form>

          {stockQuery.isFetching && <Loader size='sm' mt='md' />}
          {stockQuery.isError && (
            <Alert color='red' mt='md' title={t`Search failed`}>
              {t`The stock search could not be completed. Check your access and try again.`}
            </Alert>
          )}
          {stockQuery.data && stockQuery.data.length === 0 && (
            <Text c='dimmed' mt='md'>
              {t`No matching stock items were found.`}
            </Text>
          )}
          {!!stockQuery.data?.length && (
            <Stack gap='xs' mt='md'>
              <Text size='sm' c='dimmed'>
                {t`${stockQuery.data.length} matching stock items (up to 25)`}
              </Text>
              {stockQuery.data.map((item) => (
                <Card
                  key={item.pk}
                  withBorder
                  padding='sm'
                  radius='sm'
                  onClick={() => navigate(`/stock/item/${item.pk}/`)}
                  style={{ cursor: 'pointer' }}
                >
                  <Group justify='space-between' wrap='wrap'>
                    <Stack gap={2}>
                      <Text fw={600}>
                        {item.part_detail?.full_name ??
                          item.part_detail?.name ??
                          t`Stock item ${item.pk}`}
                      </Text>
                      <Text size='sm' c='dimmed'>
                        {item.part_detail?.IPN
                          ? `${t`Part code`}: ${item.part_detail.IPN}`
                          : ''}
                        {item.serial ? ` · ${t`Serial`}: ${item.serial}` : ''}
                      </Text>
                    </Stack>
                    <Stack align='flex-end' gap={2}>
                      <Text size='sm'>
                        {item.location_detail?.name ??
                          t`Installed or unavailable`}
                      </Text>
                      {item.belongs_to && (
                        <Anchor
                          component={Link}
                          to={`/stock/item/${item.belongs_to}/`}
                          size='xs'
                          onClick={(event) => event.stopPropagation()}
                        >
                          {t`Parent unit`} #{item.belongs_to}
                        </Anchor>
                      )}
                    </Stack>
                  </Group>
                </Card>
              ))}
            </Stack>
          )}
        </Paper>
      </section>
    </Stack>
  );
}
