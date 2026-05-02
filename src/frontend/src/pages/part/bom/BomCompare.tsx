import { ApiEndpoints, ModelType, StylishText, apiUrl } from '@lib/index';
import { t } from '@lingui/core/macro';
import { Divider, Drawer, Group, Stack } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '../../../App';
import { StandaloneField } from '../../../components/forms/StandaloneField';
import Expand from '../../../components/items/Expand';
import { RenderPart } from '../../../components/render/Part';

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

  return (
    <Drawer
      opened={opened}
      onClose={onClosed}
      withCloseButton
      position='bottom'
      size='80%'
      title={
        <Expand>
          <Group gap='lg' grow style={{ width: '100%' }}>
            <StylishText size='lg'>{t`Compare Bill of Materials`}</StylishText>
            <RenderPart instance={partInstance} showSecondary={false} />
          </Group>
        </Expand>
      }
    >
      <Stack gap='xs'>
        <Divider />
        <Group gap='xs'>
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
        </Group>
      </Stack>
    </Drawer>
  );
}
