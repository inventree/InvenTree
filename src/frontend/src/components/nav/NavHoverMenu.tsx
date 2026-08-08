import { UnstyledButton } from '@mantine/core';

import { InvenTreeLogo } from '../items/InvenTreeLogo';

export function NavHoverMenu({
  openDrawer
}: Readonly<{
  openDrawer: () => void;
}>) {
  return (
    <UnstyledButton
      onClick={() => openDrawer()}
      aria-label='navigation-menu'
      style={{ display: 'flex', alignItems: 'center', height: 38 }}
    >
      <InvenTreeLogo />
    </UnstyledButton>
  );
}
