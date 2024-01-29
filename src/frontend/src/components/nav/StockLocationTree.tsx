import { t } from '@lingui/macro';
import { Drawer, Group, LoadingOverlay, Stack, Text } from '@mantine/core';
import { ReactTree } from '@naisutech/react-tree';
import { IconSitemap } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';

import { api } from '../../App';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
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
  const navigate = useNavigate();

  const treeQuery = useQuery({
    enabled: opened,
    queryKey: ['stock_location_tree', opened],
    queryFn: async () =>
      api
        .get(ApiEndpoints.stock_location_tree, {})
        .then((response) =>
          response.data.map((location: any) => {
            return {
              id: location.pk,
              label: location.name,
              parentId: location.parent
            };
          })
        )
        .catch((error) => {
          console.error('Error fetching stock location tree:', error);
          return error;
        }),
    refetchOnMount: true
  });

  function renderNode({ node }: { node: any }) {
    return (
      <Group
        position="apart"
        key={node.id}
        noWrap={true}
        onClick={() => {
          onClose();
          navigate(`/stock/location/${node.id}`);
        }}
      >
        <Text>{node.label}</Text>
      </Group>
    );
  }

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
        <Group position="left" noWrap={true} spacing="md" p="md">
          <IconSitemap />
          <StylishText size="lg">{t`Stock Locations`}</StylishText>
        </Group>
      }
    >
      <Stack spacing="xs">
        <LoadingOverlay visible={treeQuery.isFetching} />
        <ReactTree
          nodes={treeQuery.data ?? []}
          showEmptyItems={false}
          RenderNode={renderNode}
          defaultSelectedNodes={selectedLocation ? [selectedLocation] : []}
        />
      </Stack>
    </Drawer>
  );
}
