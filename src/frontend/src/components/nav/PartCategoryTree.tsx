import { t } from '@lingui/macro';
import { Drawer, Group, Stack, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../App';
import { ApiPaths, apiUrl } from '../../states/ApiState';
import { StylishText } from '../items/StylishText';

export function PartCategoryTree({
  opened,
  onClose,
  selectedCategory
}: {
  opened: boolean;
  onClose: () => void;
  selectedCategory?: number | null;
}) {
  const treeQuery = useQuery({
    enabled: opened,
    queryKey: ['part_category_tree', opened],
    queryFn: async () =>
      api
        .get(apiUrl(ApiPaths.category_tree), {})
        .then((response) => response.data)
        .catch((error) => {
          console.error('Error fetching part categpry tree:', error);
          return error;
        }),
    refetchOnMount: true
  });

  return (
    <Drawer
      opened={opened}
      size="md"
      position="left"
      onClose={onClose}
      withCloseButton={true}
      styles={{
        header: {
          width: '100%'
        },
        title: {
          width: '100%'
        }
      }}
      title={
        <Group position="apart" noWrap={true}>
          <StylishText size="lg">{t`Part Categories`}</StylishText>
        </Group>
      }
    >
      <Stack spacing="xs">
        {treeQuery.data.map((category: any) => (
          <Group key={category.pk} position="apart" noWrap={true}>
            <Text>{category.name}</Text>
          </Group>
        ))}
      </Stack>
    </Drawer>
  );
}
