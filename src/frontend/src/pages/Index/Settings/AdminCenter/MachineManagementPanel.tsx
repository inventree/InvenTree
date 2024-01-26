import { Stack } from '@mantine/core';

import { MachineListTable } from "../../../../components/tables/machine/MachineListTable";

export default function MachineManagementPanel() {
  return (
    <Stack spacing="xs">
      <MachineListTable props={{}} />
    </Stack>
  );
}
