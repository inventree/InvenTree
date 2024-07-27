import { Stack } from '@mantine/core';

import PartStocktakeTable from '../../tables/part/PartStocktakeTable';

export default function PartStocktakeDetail({ partId }: { partId: number }) {
  return (
    <>
      <Stack gap="xs">
        <PartStocktakeTable partId={partId} />
      </Stack>
    </>
  );
}
