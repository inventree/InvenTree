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

import { aboutLinks, navDocLinks } from '../../defaults/links';
import { menuItems } from '../../defaults/menuItems';
import { InvenTreeStyle } from '../../globalStyle';
import { DocumentationLinks } from '../items/DocumentationLinks';
import { MenuLinks } from '../items/MenuLinks';

// generate 100 random plugins
const plugins = [
  ...Array(100)
    .fill(0)
    .map((_, index) => ({
      id: 'plugin' + index,
      title: `Plugin ${index}`,
      description: 'Plugin description',
      link: '/plugin'
    }))
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
        <DocumentationLinks links={navDocLinks} />
        <Space h="md" />
        <Title order={5}>{t`About`}</Title>
        <DocumentationLinks links={aboutLinks} />
      </div>
    </Flex>
  );
}
