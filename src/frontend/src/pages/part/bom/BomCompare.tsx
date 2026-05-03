import { ApiEndpoints, ModelType, StylishText, apiUrl } from '@lib/index';
import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Alert,
  Divider,
  Drawer,
  Group,
  Loader,
  Paper,
  Select,
  SimpleGrid,
  Stack,
  Table,
  Text
} from '@mantine/core';
import {
  IconCircleCheck,
  IconCirclePlus,
  IconCircleX,
  IconStatusChange
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { type ReactNode, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { api } from '../../../App';
import { StandaloneField } from '../../../components/forms/StandaloneField';
import Expand from '../../../components/items/Expand';
import { RenderPartColumn } from '../../../tables/ColumnRenderers';

// Field to check for differences when comparing BOM items
const DELTA_FIELDS = {
  reference: t`Reference`,
  allow_variants: t`Allow Variants`,
  inherited: t`Inherited`,
  optional: t`Optional`,
  consumable: t`Consumable`,
  setup_quantity: t`Setup Quantity`,
  attrition: t`Attrition`,
  rounding_multiple: t`Rounding Multiple`
};

type BomCompareRow = {
  part_detail: any;
  primary: any;
  secondary: any;
  match: boolean;
  deltas: string[];
  key: string;
};

type BomDisplayMode = 'all' | 'different' | 'common';

function getBomDeltas(primary: any, secondary: any): string[] {
  const deltas: string[] = [];

  Object.entries(DELTA_FIELDS).forEach(([field, label]) => {
    if (primary?.[field] != secondary?.[field]) {
      deltas.push(field);
    }
  });

  return deltas;
}

function BomTableRow({
  item,
  primary
}: Readonly<{
  item: BomCompareRow;
  primary: boolean;
}>) {
  const hasPart = primary ? !!item.primary : !!item.secondary;

  const partMatch = !!item.primary && !!item.secondary;

  const quantityMatch =
    partMatch && item.primary.quantity == item.secondary.quantity;

  const data = primary ? item.primary : item.secondary;

  const deltas: any[] = useMemo(() => {
    const fields: any[] = [];

    item.deltas.forEach((delta) => {
      fields.push({
        field: delta,
        label: DELTA_FIELDS[delta as keyof typeof DELTA_FIELDS],
        value: primary ? item.primary?.[delta] : item.secondary?.[delta]
      });
    });

    return fields;
  }, [item, primary]);

  // Determine the appropriate icon to display for this row
  const rowIcon: ReactNode = useMemo(() => {
    if (!!item.primary != !!item.secondary) {
      if (primary == !!item.primary) {
        return (
          <ActionIcon
            variant='transparent'
            size='sm'
            color='var(--mantine-color-yellow-5)'
          >
            <IconCirclePlus />
          </ActionIcon>
        );
      } else {
        return (
          <ActionIcon
            variant='transparent'
            size='sm'
            color='var(--mantine-color-red-5)'
          >
            <IconCircleX />
          </ActionIcon>
        );
      }
    } else if (
      !!item.deltas?.length ||
      item.primary?.quantity != item.secondary?.quantity
    ) {
      // Part exists in both BOMs but has differences
      return (
        <ActionIcon
          variant='transparent'
          size='sm'
          color='var(--mantine-color-blue-5)'
        >
          <IconStatusChange />
        </ActionIcon>
      );
    } else {
      return (
        <ActionIcon
          variant='transparent'
          size='sm'
          color='var(--mantine-color-green-5)'
        >
          <IconCircleCheck />
        </ActionIcon>
      );
    }
  }, [item, primary]);

  return (
    <Table.Tr>
      <Table.Td>
        <Group justify='space-between'>
          {hasPart ? (
            <RenderPartColumn part={item.part_detail} />
          ) : (
            <Text size='sm'>-</Text>
          )}
          {rowIcon}
        </Group>
      </Table.Td>
      <Table.Td>
        <Group gap='xs' justify='space-between'>
          <Text size='sm'>{data?.quantity ?? '-'}</Text>
          {hasPart && item.part_detail?.units && (
            <Text size='xs'>[{item.part_detail.units}]</Text>
          )}
        </Group>
      </Table.Td>
      <Table.Td>
        {partMatch && deltas.length > 0 ? (
          <Stack gap='xs'>
            {deltas.map((delta, index) => (
              <Group key={delta.field} gap='xs' justify='space-between'>
                <Text size='xs'>{delta.label}</Text>
                <Text size='xs'>{delta.value ?? '-'}</Text>
              </Group>
            ))}
          </Stack>
        ) : (
          <Text size='sm'>-</Text>
        )}
      </Table.Td>
    </Table.Tr>
  );
}

function BomTable({
  items,
  primary
}: Readonly<{
  items: BomCompareRow[];
  primary: boolean;
}>) {
  return (
    <Paper p='xs' withBorder>
      <Table>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>{t`Part`}</Table.Th>
            <Table.Th>{t`Quantity`}</Table.Th>
            <Table.Th>{t`Changes`}</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {items.map((item: any, index) => (
            <BomTableRow key={index} item={item} primary={primary} />
          ))}
        </Table.Tbody>
      </Table>
    </Paper>
  );
}

export function BomCompareDrawer({
  opened,
  onClosed,
  compareId,
  partInstance
}: {
  opened: boolean;
  onClosed: () => void;
  compareId?: string;
  partInstance: any;
}) {
  const [displayMode, setDisplayMode] = useState<BomDisplayMode>('all');

  const [searchParam, setSearchParams] = useSearchParams();

  // Fetch entire BOM for the part
  const primaryBom = useQuery({
    queryKey: ['bom-compare-primary', partInstance.pk, opened],
    enabled: opened && !!partInstance.pk,
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.bom_list), {
          params: {
            part: partInstance.pk,
            sub_part_detail: true
          }
        })
        .then((response) => response.data);
    }
  });

  // Secondary part ID
  const [secondaryPartId, setSecondaryPartId] = useState<string>(
    compareId ?? ''
  );

  useEffect(() => {
    setSecondaryPartId(compareId ?? '');
  }, [opened]);

  // Fetch BOM for the secondary part
  const secondaryBom = useQuery({
    queryKey: ['bom-compare-secondary', secondaryPartId, opened],
    enabled: opened && !!secondaryPartId,
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.bom_list), {
          params: {
            part: secondaryPartId,
            sub_part_detail: true
          }
        })
        .then((response) => response.data);
    }
  });

  // Perform comparison against
  const comparedItems: any[] = useMemo(() => {
    let rows: BomCompareRow[] = [];

    const primaryPartIds = new Set();
    const secondaryPartIds = new Set();

    // First, iterate through the "primary" BOM to generate the initial data
    primaryBom.data?.forEach((item: any) => {
      let subPartId = `${item.sub_part}`;

      while (primaryPartIds.has(subPartId)) {
        subPartId += '_dup';
      }

      primaryPartIds.add(subPartId);

      rows.push({
        part_detail: item.sub_part_detail,
        primary: item,
        secondary: null,
        match: false,
        deltas: getBomDeltas(item, null), // Initialize deltas with all fields (since no match yet)
        key: subPartId
      });
    });

    // Next, iterate through the "secondary" BOM to find matches and update the data
    secondaryBom.data?.forEach((item: any) => {
      let subPartId = `${item.sub_part}`;

      while (secondaryPartIds.has(subPartId)) {
        subPartId += '_dup';
      }

      secondaryPartIds.add(subPartId);

      // Try to find a matching part in the primary BOM
      const match = rows.find((row) => row.key == subPartId);

      if (match) {
        // If a match is found, update the existing row
        match.secondary = item;
        match.match = true; // Mark as a match
        match.deltas = getBomDeltas(match.primary, match.secondary); // Update deltas with actual differences
      } else {
        // If no match is found, add a new row for the secondary item
        rows.push({
          part_detail: item.sub_part_detail,
          primary: null,
          secondary: item,
          match: false,
          deltas: getBomDeltas(null, item),
          key: subPartId
        });
      }
    });

    switch (displayMode) {
      case 'different':
        // Show only *different* parts
        rows = rows.filter((row) => !row.match);
        break;
      case 'common':
        // Show only *common* parts
        rows = rows.filter((row) => row.match);
        break;
      default:
      case 'all':
        break;
    }

    // Return rows, sorted by part name
    return rows.sort((a, b) => {
      const nameA = a.part_detail?.name ?? '';
      const nameB = b.part_detail?.name ?? '';

      return nameA.localeCompare(nameB);
    });
  }, [displayMode, primaryBom.data, secondaryBom.data]);

  return (
    <Drawer
      opened={opened}
      onClose={onClosed}
      withCloseButton
      position='bottom'
      size='80%'
      title={
        <StylishText size='lg'>{t`Compare Bill of Materials`}</StylishText>
      }
    >
      <Stack gap='xs'>
        <Divider />
        <Paper p='xs' withBorder>
          <SimpleGrid cols={{ base: 1, sm: 3 }}>
            <Stack gap='xs' justify='flex-start' align='stretch'>
              <Text size='sm'>{t`Primary Assembly`}</Text>
              <Text
                size='xs'
                c='dimmed'
              >{t`Primary assembly for comparison`}</Text>
              <RenderPartColumn part={partInstance} />
            </Stack>
            <Select
              label={t`Display Mode`}
              description={t`Select display mode for BOM comparison`}
              defaultValue={'all'}
              onChange={(value) => setDisplayMode(value as any)}
              style={{
                maxWidth: 350
              }}
              data={[
                { value: 'all', label: t`Show all Parts` },
                { value: 'different', label: t`Show different Parts` },
                { value: 'common', label: t`Show common Parts` }
              ]}
            />
            <Expand>
              <StandaloneField
                fieldName='assembly'
                fieldDefinition={{
                  description: t`Select assembly to compare`,
                  label: t`Secondary Assembly`,
                  field_type: 'related field',
                  value: secondaryPartId,
                  api_url: apiUrl(ApiEndpoints.part_list),
                  model: ModelType.part,
                  required: true,
                  filters: {
                    assembly: true
                  },
                  onValueChange: (value) => {
                    setSecondaryPartId(value);
                    if (opened) {
                      setSearchParams(
                        {
                          compare: value
                        },
                        { replace: true }
                      );
                    }
                  }
                }}
              />
            </Expand>
          </SimpleGrid>
        </Paper>
        {secondaryPartId ? (
          <SimpleGrid cols={{ base: 1, sm: 2 }}>
            {primaryBom.isLoading ? (
              <Loader />
            ) : (
              <BomTable items={comparedItems} primary />
            )}
            {secondaryBom.isLoading ? (
              <Loader />
            ) : (
              <BomTable items={comparedItems} primary={false} />
            )}
          </SimpleGrid>
        ) : (
          <Alert color='yellow'>{t`Select an assembly to view Bill of Materials comparison`}</Alert>
        )}
      </Stack>
    </Drawer>
  );
}
