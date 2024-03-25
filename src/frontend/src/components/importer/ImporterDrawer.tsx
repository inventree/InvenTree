import { Drawer } from '@mantine/core';

export default function ImporterDrawer({
  opened,
  onClose
}: {
  opened: boolean;
  onClose: () => void;
}) {
  return (
    <Drawer
      position="bottom"
      size="xl"
      opened={opened}
      onClose={onClose}
      withCloseButton={false}
    >
      <div>Hello world!</div>
    </Drawer>
  );
}
