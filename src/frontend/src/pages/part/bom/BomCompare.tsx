import { ApiEndpoints, ModelType, StylishText, apiUrl } from '@lib/index';
import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Alert,
  Divider,
  Drawer,
  Group,
  Paper,
  SegmentedControl,
  Select,
  SimpleGrid,
  Stack,
  Table,
  Text
} from '@mantine/core';
import {
  IconArrowRight,
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
import { RenderPartColumn } from '../../../components/tables/ColumnRenderers';
import { formatDate } from '../../../defaults/formatters';
import { useGlobalSettingsState } from '../../../states/SettingsStates';

// Field to check for differences when comparing BOM items
const DELTA_FIELDS = {
  quantity: t`Quantity`,
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

type BomCompareSource = 'assembly' | 'snapshot';

// Decimal fields are stored as strings in a BOM snapshot, but returned as numbers by the BOM API
const SNAPSHOT_DECIMAL_FIELDS = [
  'quantity',
  'setup_quantity',
  'attrition',
  'rounding_multiple'
];

/**
 * Convert a BOM item stored in a BomSnapshot into the format returned by the BOM API
 */
function snapshotItemToBomItem(item: any): any {
  const bomItem: any = {
    ...item,
    sub_part: item.sub_part?.pk,
    sub_part_detail: {
      ...item.sub_part,
      full_name: item.sub_part?.name
    }
  };

  SNAPSHOT_DECIMAL_FIELDS.forEach((field) => {
    const value = item[field];
    bomItem[field] =
      value === null || value === undefined ? null : Number(value);
  });

  return bomItem;
}

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
  item
}: Readonly<{
  item: BomCompareRow;
}>) {
  const partMatch = !!item.primary && !!item.secondary;

  const quantityMatch =
    partMatch && item.primary.quantity == item.secondary.quantity;

  const deltas: any[] = useMemo(() => {
    const fields: any[] = [];

    item.deltas.forEach((delta) => {
      fields.push({
        field: delta,
        label: DELTA_FIELDS[delta as keyof typeof DELTA_FIELDS],
        primaryValue: item.primary?.[delta] ?? null,
        secondaryValue: item.secondary?.[delta] ?? null
      });
    });

    return fields;
  }, [item]);

  // Determine the appropriate icon to display for this row
  const rowIcon: ReactNode = useMemo(() => {
    if (!!item.primary != !!item.secondary) {
      if (!!item.secondary) {
        // Part was added to the secondary BOM (exists in secondary but not primary)
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
  }, [item]);

  return (
    <Table.Tr>
      <Table.Td>
        <Group gap='xs'>
          {rowIcon}
          <RenderPartColumn part={item.part_detail} />
        </Group>
      </Table.Td>
      <Table.Td>
        <Group gap='xs'>
          <Text size='sm'>
            {item.primary?.quantity ?? item.secondary?.quantity ?? '-'}
          </Text>
          {item.part_detail?.units && (
            <Text size='xs'>[{item.part_detail.units}]</Text>
          )}
        </Group>
      </Table.Td>
      <Table.Td>
        <Group gap='xs'>
          {rowIcon}
          {partMatch && deltas.length > 0 ? (
            <Stack gap='xs'>
              {deltas.map((delta, index) => (
                <Group key={delta.field} gap='xs' justify='space-between'>
                  <Text size='xs'>{delta.label}</Text>
                  <Text size='xs'>{delta.primaryValue ?? '-'}</Text>
                  <ActionIcon size='xs' variant='transparent'>
                    <IconArrowRight />
                  </ActionIcon>
                  <Text size='xs'>{delta.secondaryValue ?? '-'}</Text>
                </Group>
              ))}
            </Stack>
          ) : (
            <Text size='xs'>
              {partMatch
                ? t`No changes`
                : !!item.primary
                  ? t`Part removed from BOM`
                  : t`Part added to BOM`}
            </Text>
          )}
        </Group>
      </Table.Td>
    </Table.Tr>
  );
}

function BomTable({
  items
}: Readonly<{
  items: BomCompareRow[];
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
            <BomTableRow key={index} item={item} />
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
  compareSnapshotId,
  partInstance
}: {
  opened: boolean;
  onClosed: () => void;
  compareId?: string;
  compareSnapshotId?: string;
  partInstance: any;
}) {
  const [displayMode, setDisplayMode] = useState<BomDisplayMode>('all');

  const globalSettings = useGlobalSettingsState();

  const snapshotsEnabled: boolean = globalSettings.isSet('PART_BOM_SNAPSHOT');

  const [selectedSource, setCompareSource] = useState<BomCompareSource>(
    compareSnapshotId ? 'snapshot' : 'assembly'
  );

  // Comparison against BOM snapshots is only available if the feature is enabled
  const compareSource: BomCompareSource = snapshotsEnabled
    ? selectedSource
    : 'assembly';

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

  // Secondary snapshot ID
  const [snapshotId, setSnapshotId] = useState<string>(compareSnapshotId ?? '');

  useEffect(() => {
    setSecondaryPartId(compareId ?? '');
    setSnapshotId(compareSnapshotId ?? '');
    setCompareSource(compareSnapshotId ? 'snapshot' : 'assembly');
  }, [opened]);

  // Fetch the list of available snapshots for the primary part
  const snapshotList = useQuery({
    queryKey: ['bom-compare-snapshots', partInstance.pk, opened],
    enabled: opened && !!partInstance.pk && compareSource == 'snapshot',
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.bom_snapshot_list), {
          params: {
            part: partInstance.pk
          }
        })
        .then((response) => response.data);
    }
  });

  const snapshotOptions = useMemo(() => {
    return (
      snapshotList.data?.map((snapshot: any) => {
        const label = [
          formatDate(snapshot.created, { showTime: true }),
          snapshot.created_by_detail?.username,
          snapshot.note
        ]
          .filter((value) => !!value)
          .join(' · ');

        return {
          value: `${snapshot.pk}`,
          label: label
        };
      }) ?? []
    );
  }, [snapshotList.data]);

  // Fetch the selected snapshot
  const snapshotBom = useQuery({
    queryKey: ['bom-compare-snapshot', snapshotId, opened],
    enabled: opened && !!snapshotId && compareSource == 'snapshot',
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.bom_snapshot_list, snapshotId))
        .then((response) =>
          (response.data?.data?.items ?? []).map(snapshotItemToBomItem)
        );
    }
  });

  const updateSearchParams = (params: Record<string, string>) => {
    if (opened) {
      setSearchParams(params, { replace: true });
    }
  };

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
  const secondaryData: any[] | undefined =
    compareSource == 'snapshot' ? snapshotBom.data : secondaryBom.data;

  const hasSecondary: boolean =
    compareSource == 'snapshot' ? !!snapshotId : !!secondaryPartId;

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
    secondaryData?.forEach((item: any) => {
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
      case 'all':
        break;
      default:
    }

    // Return rows, sorted by part name
    return rows.sort((a, b) => {
      const nameA = a.part_detail?.name ?? '';
      const nameB = b.part_detail?.name ?? '';

      return nameA.localeCompare(nameB);
    });
  }, [displayMode, primaryBom.data, secondaryData]);

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
            <Expand>
              <Stack gap='xs'>
                {snapshotsEnabled && (
                  <SegmentedControl
                    aria-label='bom-compare-source'
                    value={compareSource}
                    onChange={(value) =>
                      setCompareSource(value as BomCompareSource)
                    }
                    data={[
                      { value: 'assembly', label: t`Assembly` },
                      { value: 'snapshot', label: t`Snapshot` }
                    ]}
                  />
                )}
                {compareSource == 'assembly' ? (
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
                        updateSearchParams({ compare: value });
                      }
                    }}
                  />
                ) : (
                  <Select
                    label={t`BOM Snapshot`}
                    aria-label='bom-compare-snapshot'
                    description={t`Select a previously validated BOM to compare`}
                    placeholder={
                      snapshotOptions.length == 0
                        ? t`No snapshots available`
                        : undefined
                    }
                    disabled={snapshotOptions.length == 0}
                    value={snapshotId || null}
                    onChange={(value) => {
                      setSnapshotId(value ?? '');
                      updateSearchParams({ compare_snapshot: value ?? '' });
                    }}
                    data={snapshotOptions}
                  />
                )}
              </Stack>
            </Expand>
            <Select
              label={t`Display Mode`}
              aria-label='bom-compare-display-mode'
              description={t`Select display mode for BOM comparison`}
              defaultValue={'all'}
              onChange={(value) => setDisplayMode(value as any)}
              data={[
                { value: 'all', label: t`Show all Parts` },
                { value: 'different', label: t`Show different Parts` },
                { value: 'common', label: t`Show common Parts` }
              ]}
            />
          </SimpleGrid>
        </Paper>
        {hasSecondary ? (
          <BomTable items={comparedItems} />
        ) : compareSource == 'snapshot' ? (
          <Alert color='yellow'>{t`Select a BOM snapshot to view Bill of Materials comparison`}</Alert>
        ) : (
          <Alert color='yellow'>{t`Select an assembly to view Bill of Materials comparison`}</Alert>
        )}
      </Stack>
    </Drawer>
  );
}
