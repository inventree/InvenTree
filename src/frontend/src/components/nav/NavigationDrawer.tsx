import { t } from '@lingui/macro';
import {
  Container,
  Drawer,
  Flex,
  Group,
  ScrollArea,
  Space
} from '@mantine/core';
import { useViewportSize } from '@mantine/hooks';
import { useEffect, useMemo, useRef, useState } from 'react';

import { AboutLinks, DocumentationLinks } from '../../defaults/links';
import { ModelType } from '../../enums/ModelType';
import { UserRoles } from '../../enums/Roles';
import useInstanceName from '../../hooks/UseInstanceName';
import * as classes from '../../main.css';
import { useGlobalSettingsState } from '../../states/SettingsState';
import { useUserState } from '../../states/UserState';
import { InvenTreeLogo } from '../items/InvenTreeLogo';
import { type MenuLinkItem, MenuLinks } from '../items/MenuLinks';
import { StylishText } from '../items/StylishText';

// TODO @matmair #1: implement plugin loading and menu item generation see #5269
const plugins: MenuLinkItem[] = [];

export function NavigationDrawer({
  opened,
  close
}: Readonly<{
  opened: boolean;
  close: () => void;
}>) {
  return (
    <Drawer
      opened={opened}
      onClose={close}
      size='lg'
      withCloseButton={false}
      classNames={{
        body: classes.navigationDrawer
      }}
    >
      <DrawerContent closeFunc={close} />
    </Drawer>
  );
}

function DrawerContent({ closeFunc }: Readonly<{ closeFunc?: () => void }>) {
  const user = useUserState();

  const globalSettings = useGlobalSettingsState();

  const [scrollHeight, setScrollHeight] = useState(0);
  const ref = useRef(null);
  const { height } = useViewportSize();

  const title = useInstanceName();

  // update scroll height when viewport size changes
  useEffect(() => {
    if (ref.current == null) return;
    setScrollHeight(height - ref.current['clientHeight'] - 65);
  });

  // Construct menu items
  const menuItemsNavigate: MenuLinkItem[] = useMemo(() => {
    return [
      {
        id: 'home',
        title: t`Dashboard`,
        link: '/',
        icon: 'dashboard'
      },
      {
        id: 'parts',
        title: t`Parts`,
        hidden: !user.hasViewPermission(ModelType.part),
        link: '/part',
        icon: 'part'
      },
      {
        id: 'stock',
        title: t`Stock`,
        link: '/stock',
        hidden: !user.hasViewPermission(ModelType.stockitem),
        icon: 'stock'
      },
      {
        id: 'build',
        title: t`Manufacturing`,
        link: '/manufacturing/',
        hidden: !user.hasViewRole(UserRoles.build),
        icon: 'build'
      },
      {
        id: 'purchasing',
        title: t`Purchasing`,
        link: '/purchasing/',
        hidden: !user.hasViewRole(UserRoles.purchase_order),
        icon: 'purchase_orders'
      },
      {
        id: 'sales',
        title: t`Sales`,
        link: '/sales/',
        hidden: !user.hasViewRole(UserRoles.sales_order),
        icon: 'sales_orders'
      }
    ];
  }, [user]);

  const menuItemsAction: MenuLinkItem[] = useMemo(() => {
    return [
      {
        id: 'barcode',
        title: t`Scan Barcode`,
        link: '/scan',
        icon: 'barcode',
        hidden: !globalSettings.isSet('BARCODE_ENABLE')
      }
    ];
  }, [user, globalSettings]);

  const menuItemsSettings: MenuLinkItem[] = useMemo(() => {
    return [
      {
        id: 'notifications',
        title: t`Notifications`,
        link: '/notifications',
        icon: 'notification'
      },
      {
        id: 'user-settings',
        title: t`User Settings`,
        link: '/settings/user',
        icon: 'user'
      },
      {
        id: 'system-settings',
        title: t`System Settings`,
        link: '/settings/system',
        icon: 'system',
        hidden: !user.isStaff()
      },
      {
        id: 'admin-center',
        title: t`Admin Center`,
        link: '/settings/admin',
        icon: 'admin',
        hidden: !user.isStaff()
      }
    ];
  }, [user]);

  const menuItemsDocumentation: MenuLinkItem[] = useMemo(
    () => DocumentationLinks(),
    []
  );

  const menuItemsAbout: MenuLinkItem[] = useMemo(
    () => AboutLinks(globalSettings, user),
    []
  );

  return (
    <Flex direction='column' mih='100vh' p={16}>
      <Group wrap='nowrap'>
        <InvenTreeLogo />
        <StylishText size='xl'>{title}</StylishText>
      </Group>
      <Space h='xs' />
      <Container className={classes.layoutContent} p={0}>
        <ScrollArea h={scrollHeight} type='always' offsetScrollbars>
          <MenuLinks
            title={t`Navigation`}
            links={menuItemsNavigate}
            beforeClick={closeFunc}
          />
          <MenuLinks
            title={t`Settings`}
            links={menuItemsSettings}
            beforeClick={closeFunc}
          />
          <MenuLinks
            title={t`Actions`}
            links={menuItemsAction}
            beforeClick={closeFunc}
          />
          <Space h='md' />
          {plugins.length > 0 ? (
            <MenuLinks
              title={t`Plugins`}
              links={plugins}
              beforeClick={closeFunc}
            />
          ) : (
            <></>
          )}
        </ScrollArea>
      </Container>
      <div ref={ref}>
        <Space h='md' />
        <MenuLinks
          title={t`Documentation`}
          links={menuItemsDocumentation}
          beforeClick={closeFunc}
        />
        <Space h='md' />
        <MenuLinks
          title={t`About`}
          links={menuItemsAbout}
          beforeClick={closeFunc}
        />
      </div>
    </Flex>
  );
}
