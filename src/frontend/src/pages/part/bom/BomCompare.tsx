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
  piece_count: t`Piece Count`,
  reference: t`Reference`,
  allow_variants: t`Allow Variants`,
  inherited: t`Inherited`,
  optional: t`Optional`,
  consumable: t`Consumable`,
  setup_quantity: t`Setup Quantity`,
  attrition: t`Attrition`,
  rounding_multiple: t`Rounding Multiple`,
  substitutes: t`Substitutes`
};

// Fields which are compared (and displayed) using a derived value
const DELTA_COMPARE_KEYS: Record<string, string> = {
  substitutes: 'substitute_ids'
};

const DELTA_DISPLAY_KEYS: Record<string, string> = {
  substitutes: 'substitutes_text'
};

/**
 * A single row in the BOM comparison.
 * The comparison is from the "before" BOM to the "after" BOM:
 * - When comparing against another assembly, "before" is the primary assembly
 * - When comparing against a snapshot, "before" is the (older) snapshot
 */
type BomCompareRow = {
  part_detail: any;
  before: any;
  after: any;
  match: boolean;
  deltas: string[];
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
 * Add derived substitute fields to a BOM item, for comparison
 */
function withSubstitutes(item: any, substitutes: any[]): any {
  const sorted = [...substitutes].sort((a: any, b: any) => a.pk - b.pk);

  return {
    ...item,
    substitute_ids: sorted.map((sub: any) => sub.pk).join(','),
    substitutes_text: sorted.map((sub: any) => sub.name).join(', ')
  };
}

/**
 * Convert a BOM item returned by the BOM API into the format used for comparison
 */
function apiItemToBomItem(item: any): any {
  return withSubstitutes(
    item,
    (item.substitutes ?? []).map((sub: any) => ({
      pk: sub.part,
      name: sub.part_detail?.name
    }))
  );
}

/**
 * Convert a BOM item stored in a BomSnapshot into the format used for comparison
 *
 * @param partDetails - Current details for parts which still exist, keyed by part ID
 */
function snapshotItemToBomItem(item: any, partDetails: any): any {
  const bomItem: any = withSubstitutes(
    {
      ...item,
      sub_part: item.sub_part?.pk,
      // Use current part details (e.g. thumbnail) if the part still exists
      sub_part_detail: partDetails?.[`${item.sub_part?.pk}`] ?? {
        ...item.sub_part,
        full_name: item.sub_part?.name
      }
    },
    item.substitutes ?? []
  );

  SNAPSHOT_DECIMAL_FIELDS.forEach((field) => {
    const value = item[field];
    bomItem[field] =
      value === null || value === undefined ? null : Number(value);
  });

  return bomItem;
}

/**
 * Format a BOM item field value for display in the comparison
 */
function formatDeltaValue(value: any): string {
  if (value === true) {
    return t`Yes`;
  } else if (value === false) {
    return t`No`;
  } else if (value === null || value === undefined || value === '') {
    return '-';
  }

  return `${value}`;
}

function getBomDeltas(before: any, after: any): string[] {
  const deltas: string[] = [];

  Object.keys(DELTA_FIELDS).forEach((field) => {
    const key = DELTA_COMPARE_KEYS[field] ?? field;

    if (before?.[key] != after?.[key]) {
      deltas.push(field);
    }
  });

  return deltas;
}

/**
 * Match the BOM items from two BOMs, and calculate the differences between them
 *
 * @param beforeItems - BOM items in the "before" BOM
 * @param afterItems - BOM items in the "after" BOM
 * @param matchByPk - Match BOM lines by ID first (for comparing two versions of the same BOM)
 */
function compareBomItems(
  beforeItems: any[],
  afterItems: any[],
  matchByPk: boolean
): BomCompareRow[] {
  const rows: BomCompareRow[] = beforeItems.map((item: any) => ({
    part_detail: item.sub_part_detail,
    before: item,
    after: null,
    match: false,
    deltas: []
  }));

  const unmatched: any[] = [];

  // First, match the same BOM line (where the line still refers to the same part)
  afterItems.forEach((item: any) => {
    const row = matchByPk
      ? rows.find(
          (r) =>
            !r.match &&
            r.before.pk == item.pk &&
            r.before.sub_part == item.sub_part
        )
      : undefined;

    if (row) {
      row.after = item;
      row.match = true;
    } else {
      unmatched.push(item);
    }
  });

  // Next, match any remaining lines by part
  unmatched.forEach((item: any) => {
    const row = rows.find(
      (r) => !r.match && !!r.before && r.before.sub_part == item.sub_part
    );

    if (row) {
      row.after = item;
      row.match = true;
    } else {
      rows.push({
        part_detail: item.sub_part_detail,
        before: null,
        after: item,
        match: false,
        deltas: []
      });
    }
  });

  rows.forEach((row) => {
    if (row.match) {
      row.deltas = getBomDeltas(row.before, row.after);
    }
  });

  return rows;
}

function BomTableRow({
  item,
  currentSide
}: Readonly<{
  item: BomCompareRow;
  currentSide: 'before' | 'after';
}>) {
  const partMatch = !!item.before && !!item.after;

  // Display the quantity from the current BOM of the primary assembly
  const current = currentSide == 'before' ? item.before : item.after;
  const other = currentSide == 'before' ? item.after : item.before;

  const deltas: any[] = useMemo(() => {
    const fields: any[] = [];

    item.deltas.forEach((delta) => {
      const key = DELTA_DISPLAY_KEYS[delta] ?? delta;

      fields.push({
        field: delta,
        label: DELTA_FIELDS[delta as keyof typeof DELTA_FIELDS],
        beforeValue: item.before?.[key] ?? null,
        afterValue: item.after?.[key] ?? null
      });
    });

    return fields;
  }, [item]);

  // Determine the appropriate icon to display for this row
  const rowIcon: ReactNode = useMemo(() => {
    if (!!item.before != !!item.after) {
      if (!!item.after) {
        // Part was added (exists in the "after" BOM but not the "before" BOM)
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
    } else if (!!item.deltas?.length) {
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
          <Text size='sm'>{current?.quantity ?? other?.quantity ?? '-'}</Text>
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
              {deltas.map((delta) => (
                <Group key={delta.field} gap='xs' justify='space-between'>
                  <Text size='xs'>{delta.label}</Text>
                  <Text size='xs'>{formatDeltaValue(delta.beforeValue)}</Text>
                  <ActionIcon size='xs' variant='transparent'>
                    <IconArrowRight />
                  </ActionIcon>
                  <Text size='xs'>{formatDeltaValue(delta.afterValue)}</Text>
                </Group>
              ))}
            </Stack>
          ) : (
            <Text size='xs'>
              {partMatch
                ? t`No changes`
                : !!item.before
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
  items,
  currentSide
}: Readonly<{
  items: BomCompareRow[];
  currentSide: 'before' | 'after';
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
            <BomTableRow key={index} item={item} currentSide={currentSide} />
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
            sub_part_detail: true,
            substitutes: true
          }
        })
        .then((response) => response.data?.map(apiItemToBomItem));
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
          (response.data?.data?.items ?? []).map((item: any) =>
            snapshotItemToBomItem(item, response.data?.part_details)
          )
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
            sub_part_detail: true,
            substitutes: true
          }
        })
        .then((response) => response.data?.map(apiItemToBomItem));
    }
  });

  const hasSecondary: boolean =
    compareSource == 'snapshot' ? !!snapshotId : !!secondaryPartId;

  // When comparing against a snapshot, show the changes *from* the snapshot *to* the current BOM
  const currentSide: 'before' | 'after' =
    compareSource == 'snapshot' ? 'after' : 'before';

  const comparedItems: any[] = useMemo(() => {
    let rows: BomCompareRow[] =
      compareSource == 'snapshot'
        ? compareBomItems(snapshotBom.data ?? [], primaryBom.data ?? [], true)
        : compareBomItems(
            primaryBom.data ?? [],
            secondaryBom.data ?? [],
            false
          );

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
  }, [
    displayMode,
    compareSource,
    primaryBom.data,
    secondaryBom.data,
    snapshotBom.data
  ]);

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
          <BomTable items={comparedItems} currentSide={currentSide} />
        ) : compareSource == 'snapshot' ? (
          <Alert color='yellow'>{t`Select a BOM snapshot to view Bill of Materials comparison`}</Alert>
        ) : (
          <Alert color='yellow'>{t`Select an assembly to view Bill of Materials comparison`}</Alert>
        )}
      </Stack>
    </Drawer>
  );
}
