import { t } from '@lingui/macro';
import { Drawer, Group, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

import { api } from '../../App';
import { ApiPaths, apiUrl } from '../../states/ApiState';
import { StylishText } from '../items/StylishText';

export function StockLocationTree({
  opened,
  onClose,
  selectedLocation
}: {
  opened: boolean;
  onClose: () => void;
  selectedLocation?: number | null;
}) {
  const treeQuery = useQuery({
    enabled: opened,
    queryKey: ['stock_location_tree', opened],
    queryFn: async () =>
      api
        .get(apiUrl(ApiPaths.stock_location_tree), {})
        .then((response) => response.data)
        .catch((error) => {
          console.error('Error fetching stock location tree:', error);
          return error;
        })
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
          <StylishText size="lg">{t`Stock Locations`}</StylishText>
        </Group>
      }
    >
      {treeQuery.data.map((location: any) => (
        <Group position="apart" noWrap={true}>
          <Text>{location.name}</Text>
        </Group>
      ))}
    </Drawer>
  );
}
