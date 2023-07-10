import { t } from '@lingui/macro';
import {
  Container,
  Drawer,
  Flex,
  ScrollArea,
  Space,
  Title
} from '@mantine/core';
import { useViewportSize } from '@mantine/hooks';
import { useEffect, useRef, useState } from 'react';

import { menuItems } from '../../defaults/menuItems';
import { InvenTreeStyle } from '../../globalStyle';
import { DocumentationLinks } from '../items/DocumentationLinks';
import { MenuLinks } from '../items/MenuLinks';

// generate 100 random plugins
const plugins = [
  ...Array(100)
    .fill(0)
    .map((_, index) => ({
      title: `Plugin ${index}`,
      description: 'Plugin description',
      link: '/plugin'
    }))
];

const docLinks = [
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
];

const aboutLinks = [
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
];

export function NavigationDrawer({
  opened,
  close
}: {
  opened: boolean;
  close: () => void;
}) {
  const { classes } = InvenTreeStyle();

  return (
    <Drawer
      opened={opened}
      onClose={close}
      overlayProps={{ opacity: 0.5, blur: 4 }}
      withCloseButton={false}
      classNames={{
        body: classes.navigationDrawer
      }}
    >
      <DrawerContent />
    </Drawer>
  );
}
function DrawerContent() {
  const { classes } = InvenTreeStyle();
  const [scrollHeight, setScrollHeight] = useState(0);
  const ref = useRef(null);
  const { height } = useViewportSize();

  // update scroll height when viewport size changes
  useEffect(() => {
    if (ref.current == null) return;
    setScrollHeight(height - ref.current['clientHeight'] - 62);
  });

  return (
    <Flex direction="column" mih="100vh" p={16}>
      <Title order={3}>{t`Navigation`}</Title>
      <Container className={classes.layoutContent} p={0}>
        <ScrollArea h={scrollHeight} type="always" offsetScrollbars>
          <Title order={5}>{t`Pages`}</Title>
          <MenuLinks links={menuItems} />
          <Space h="md" />
          <Title order={5}>{t`Plugins`}</Title>
          <MenuLinks links={plugins} />
        </ScrollArea>
      </Container>
      <div ref={ref}>
        <Space h="md" />
        <Title order={5}>{t`Documentation`}</Title>
        <DocumentationLinks links={docLinks} />
        <Space h="md" />
        <Title order={5}>{t`About`}</Title>
        <DocumentationLinks links={aboutLinks} />
      </div>
    </Flex>
  );
}
