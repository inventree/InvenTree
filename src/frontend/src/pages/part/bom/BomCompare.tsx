import { ApiEndpoints, ModelType, StylishText, apiUrl } from '@lib/index';
import { t } from '@lingui/core/macro';
import {
  Divider,
  Drawer,
  Group,
  Loader,
  SimpleGrid,
  Stack,
  Table,
  Text
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useMemo, useState } from 'react';
import { api } from '../../../App';
import { StandaloneField } from '../../../components/forms/StandaloneField';
import Expand from '../../../components/items/Expand';
import { RenderPartColumn } from '../../../tables/ColumnRenderers';

const MISMATCH_COLOR = '#ffe6e6aa';
const MATCH_COLOR = 'transparent';

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

function getBomDeltas(primary: any, secondary: any): string[] {
  const deltas: string[] = [];

  Object.entries(DELTA_FIELDS).forEach(([field, label]) => {
    if (primary?.[field] != secondary?.[field]) {
      deltas.push(label);
    }
  });

  return deltas;
}

function BomTableRow({
  item,
  primary
}: {
  item: BomCompareRow;
  primary: boolean;
}) {
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

  return (
    <Table.Tr key={item.key}>
      <Table.Td
        style={{ backgroundColor: partMatch ? MATCH_COLOR : MISMATCH_COLOR }}
      >
        {hasPart ? (
          <RenderPartColumn part={item.part_detail} />
        ) : (
          <Text size='sm'>-</Text>
        )}
      </Table.Td>
      <Table.Td
        style={{
          backgroundColor: quantityMatch ? MATCH_COLOR : MISMATCH_COLOR
        }}
      >
        <Group gap='xs' justify='space-between'>
          <Text size='sm'>{data?.quantity ?? '-'}</Text>
          {hasPart && item.part_detail?.units && (
            <Text size='xs'>[{item.part_detail.units}]</Text>
          )}
        </Group>
      </Table.Td>
    </Table.Tr>
  );
}

function BomTable({
  items,
  primary
}: {
  items: BomCompareRow[];
  primary: boolean;
}) {
  return (
    <Table>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>{t`Part`}</Table.Th>
          <Table.Th>{t`Quantity`}</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {items.map((item: any, index) => (
          <BomTableRow key={index} item={item} primary={primary} />
        ))}
      </Table.Tbody>
    </Table>
  );
}

export function BomCompareDrawer({
  opened,
  onClosed,
  partInstance
}: {
  opened: boolean;
  onClosed: () => void;
  partInstance: any;
}) {
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

  // Secondary part instance
  const [secondaryPart, setSecondaryPart] = useState<any>({});

  // Fetch BOM for the secondary part
  const secondaryBom = useQuery({
    queryKey: ['bom-compare-secondary', secondaryPart.pk, opened],
    enabled: opened && !!secondaryPart.pk,
    queryFn: async () => {
      return api
        .get(apiUrl(ApiEndpoints.bom_list), {
          params: {
            part: secondaryPart.pk,
            sub_part_detail: true
          }
        })
        .then((response) => response.data);
    }
  });

  // Perform comparison against
  const comparedItems: any[] = useMemo(() => {
    const rows: BomCompareRow[] = [];

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

    // Return rows, sorted by part name
    return rows.sort((a, b) => {
      const nameA = a.part_detail?.name ?? '';
      const nameB = b.part_detail?.name ?? '';

      return nameA.localeCompare(nameB);
    });
  }, [primaryBom.data, secondaryBom.data]);

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
        <SimpleGrid cols={2} type='container' spacing='xs' verticalSpacing='xs'>
          <RenderPartColumn part={partInstance} />
          <Expand>
            <StandaloneField
              fieldName='assembly'
              fieldDefinition={{
                description: t`Select assembly to compare`,
                label: t`Assembly`,
                field_type: 'related field',
                api_url: apiUrl(ApiEndpoints.part_list),
                model: ModelType.part,
                required: true,
                filters: {
                  assembly: true
                },
                onValueChange: (value, instance) => {
                  setSecondaryPart(instance);
                }
              }}
            />
          </Expand>
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
      </Stack>
    </Drawer>
  );
}
