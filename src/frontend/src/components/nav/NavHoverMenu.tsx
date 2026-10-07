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
      id='tipp-ftu-nav2'
    >
      <InvenTreeLogo />
    </UnstyledButton>
  );
}
