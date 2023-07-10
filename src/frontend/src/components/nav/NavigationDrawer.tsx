import { t } from '@lingui/macro';
import { Drawer, Space, Title } from '@mantine/core';

import { menuItems } from '../../defaults/menuItems';
import { DocumentationLinks } from '../items/DocumentationLinks';
import { MenuLinks } from '../items/MenuLinks';

export function NavigationDrawer({
  opened,
  close
}: {
  opened: boolean;
  close: () => void;
}) {
  return (
    <Drawer
      opened={opened}
      onClose={close}
      overlayProps={{ opacity: 0.5, blur: 4 }}
      withCloseButton={false}
    >
      <Title order={3}>{t`Navigation`}</Title>
      <Title order={5}>{t`Pages`}</Title>
      <MenuLinks links={menuItems} />
      <Space h="md" />
      <Title order={5}>{t`Plugins`}</Title>
      <MenuLinks links={[]} />
      <Space h="md" />
      <Title order={5}>{t`Documentation`}</Title>
      <DocumentationLinks
        links={[
          {
            title: t`Getting Started`,
            description: t`Getting started with InvenTree`,
            link: '/docs/getting-started'
          },
          {
            title: t`API`,
            description: t`InvenTree API documentation`,
            link: '/api'
          },
          {
            title: t`User Manual`,
            description: t`InvenTree user manual`,
            link: '/docs/user'
          },
          {
            title: t`Developer Manual`,
            description: t`InvenTree developer manual`,
            link: '/docs/developer'
          },
          {
            title: t`FAQ`,
            description: t`Frequently asked questions`,
            link: '/docs/faq'
          }
        ]}
      />
      <Space h="md" />
      <Title order={5}>{t`About`}</Title>
      <DocumentationLinks
        links={[
          {
            title: t`Instance`,
            description: t`About this Inventree instance`,
            link: '/instance'
          },
          {
            title: t`InvenTree`,
            description: t`About the InvenTree org`,
            link: '/about'
          },
          {
            title: t`Licenses`,
            description: t`Licenses for packages used by InvenTree`,
            link: '/licenses'
          }
        ]}
      />
    </Drawer>
  );
}
