import { UnstyledButton } from '@mantine/core';

import { InvenTreeLogo } from '../items/InvenTreeLogo';

export function NavHoverMenu({
  openDrawer: openDrawer
}: Readonly<{
  openDrawer: () => void;
}>) {
  return (
    <UnstyledButton onClick={() => openDrawer()} aria-label="navigation-menu">
      <InvenTreeLogo />
    </UnstyledButton>
  );
}
