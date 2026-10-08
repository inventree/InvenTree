import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  ActionIcon,
  Box,
  Collapse,
  Divider,
  Group,
  Menu,
  ScrollArea,
  Stack,
  Switch,
  Text,
  Tooltip,
  UnstyledButton,
  useMantineColorScheme
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import {
  IconBox,
  IconBuildingBank,
  IconBuildingFactory2,
  IconBuildingStore,
  IconCategory,
  IconChevronDown,
  IconChevronLeft,
  IconChevronRight,
  IconClipboardList,
  IconCreditCard,
  IconCube,
  IconFileAnalytics,
  IconHelpCircle,
  IconLayoutDashboard,
  IconMoonStars,
  IconPackages,
  IconSettings,
  IconShoppingCart,
  IconSun,
  IconTag,
  IconTruckDelivery,
  IconTruckReturn,
  IconUserBolt,
  IconUserCog,
  IconUsers
} from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useLocation, useMatch, useNavigate } from 'react-router-dom';

import { UserRoles } from '@lib/enums/Roles';
import { navigateToLink } from '@lib/functions/Navigation';
import { aboutInvenTree } from '../../defaults/links';
import { useGlobalSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';

const SIDEBAR_WIDTH = 240;
const COLLAPSED_WIDTH = Math.round(SIDEBAR_WIDTH * 0.2); // 48px (20% of whole width)

// ─── Sidebar colors matching the InvenTree login page theme ───
const SIDEBAR_BG = 'linear-gradient(180deg, #0b1120 0%, #0f172a 60%, #0c1427 100%)';
const SIDEBAR_SECTION_LABEL = '#64748b'; // Slate 500 (from login theme)
const SIDEBAR_ITEM_DEFAULT = '#94a3b8'; // Slate 400 (from login theme)
const SIDEBAR_ITEM_HOVER_BG = 'rgba(2, 132, 199, 0.12)';
const SIDEBAR_ITEM_ACTIVE_BG = 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)'; // InvenTree Azure Blue
const SIDEBAR_ITEM_ACTIVE_COLOR = '#ffffff';

interface SidebarItemProps {
  icon: React.ReactNode;
  label: string;
  link?: string;
  action?: () => void;
  active?: boolean;
  rightSection?: React.ReactNode;
  indent?: boolean;
  collapsed?: boolean;
}

function SidebarItem({
  icon,
  label,
  link,
  action,
  active,
  rightSection,
  indent = false,
  collapsed = false
}: Readonly<SidebarItemProps>) {
  const navigate = useNavigate();

  const buttonContent = (
    <UnstyledButton
      onClick={(e: any) => {
        if (action) {
          action();
        } else if (link) {
          navigateToLink(link, navigate, e);
        }
      }}
      data-active={active ? 'true' : 'false'}
      data-clickable={link || action ? 'true' : 'false'}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: collapsed ? 'center' : 'space-between',
        width: collapsed ? 36 : '100%',
        height: collapsed ? 36 : undefined,
        margin: collapsed ? '2px auto' : undefined,
        padding: collapsed ? 0 : `8px ${indent ? '24px' : '12px'}`,
        borderRadius: 10,
        background: active ? SIDEBAR_ITEM_ACTIVE_BG : 'transparent',
        boxShadow: active ? '0 4px 14px -1px rgba(2, 132, 199, 0.45)' : 'none',
        color: active ? SIDEBAR_ITEM_ACTIVE_COLOR : SIDEBAR_ITEM_DEFAULT,
        fontSize: 13,
        fontWeight: active ? 600 : 400,
        transition: 'all 0.18s ease',
        cursor: link || action ? 'pointer' : 'default'
      }}
      className='sidebar-nav-item'
    >
      {collapsed ? (
        <Box
          style={{
            opacity: active ? 1 : 0.85,
            color: active ? '#ffffff' : '#38bdf8',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {icon}
        </Box>
      ) : (
        <>
          <Group gap={10} wrap='nowrap'>
            <Box
              style={{
                opacity: active ? 1 : 0.85,
                color: active ? '#ffffff' : '#38bdf8',
                flexShrink: 0,
                display: 'flex'
              }}
            >
              {icon}
            </Box>
            <Text
              size='sm'
              fw={active ? 600 : 400}
              c={active ? '#ffffff' : SIDEBAR_ITEM_DEFAULT}
            >
              {label}
            </Text>
          </Group>
          {rightSection}
        </>
      )}
    </UnstyledButton>
  );

  if (collapsed) {
    return (
      <Tooltip label={label} position='right' offset={14} withArrow keepMounted={false}>
        {buttonContent}
      </Tooltip>
    );
  }

  return buttonContent;
}

interface SidebarGroupProps {
  label: string;
  children: React.ReactNode;
  collapsed?: boolean;
}

function SidebarGroup({ label, children, collapsed = false }: Readonly<SidebarGroupProps>) {
  if (collapsed) {
    return (
      <Stack gap={4} align='center' w='100%'>
        <Divider my={4} w={24} color='rgba(255, 255, 255, 0.08)' />
        {children}
      </Stack>
    );
  }

  return (
    <Stack gap={2}>
      <Text
        size='xs'
        fw={700}
        tt='uppercase'
        style={{
          letterSpacing: '0.8px',
          color: SIDEBAR_SECTION_LABEL,
          padding: '8px 12px 4px'
        }}
      >
        {label}
      </Text>
      {children}
    </Stack>
  );
}

function SettingsSubMenu() {
  const navigate = useNavigate();
  const userState = useUserState();
  const { user } = userState;
  const isStaff =
    userState.isStaff() ||
    user?.is_staff ||
    userState.isSuperuser() ||
    user?.is_superuser;

  const isActive = (path: string) => {
    return window.location.pathname.startsWith(path);
  };

  return (
    <Stack
      gap={2}
      mt={4}
      mb={6}
      pl={10}
      style={{
        borderLeft: '2px solid rgba(2, 132, 199, 0.35)',
        marginLeft: 18
      }}
    >
      <SidebarItem
        icon={<IconUserCog size={15} />}
        label={t`User Settings`}
        link='/settings/user'
        active={isActive('/settings/user')}
      />
      {isStaff && (
        <SidebarItem
          icon={<IconUserBolt size={15} />}
          label={t`Admin Settings`}
          link='/settings/admin'
          active={isActive('/settings/admin')}
        />
      )}
      {isStaff && (
        <SidebarItem
          icon={<IconSettings size={15} />}
          label={t`System Settings`}
          link='/settings/system'
          active={isActive('/settings/system')}
        />
      )}
    </Stack>
  );
}

function DarkModeToggleItem({
  isDark,
  onToggle
}: Readonly<{
  isDark: boolean;
  onToggle: () => void;
}>) {
  return (
    <UnstyledButton
      onClick={onToggle}
      aria-label={isDark ? t`Switch to Light Mode` : t`Switch to Dark Mode`}
      data-clickable='true'
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        width: '100%',
        padding: '8px 12px',
        borderRadius: 10,
        color: SIDEBAR_ITEM_DEFAULT,
        fontSize: 13,
        fontWeight: 400,
        transition: 'all 0.18s ease',
        cursor: 'pointer',
        userSelect: 'none'
      }}
      className='sidebar-nav-item'
    >
      <Group gap={10} wrap='nowrap'>
        <Box
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            color: isDark ? '#74c0fc' : '#94a3b8',
            transition: 'color 0.2s ease'
          }}
        >
          <IconMoonStars size={16} style={{ color: isDark ? '#74c0fc' : '#94a3b8' }} />
        </Box>
        <Text size='sm' c={SIDEBAR_ITEM_DEFAULT} style={{ whiteSpace: 'nowrap' }}>
          {t`Dark Mode`}
        </Text>
      </Group>

      {/* Smooth Pill Switch without nested event conflicts */}
      <Box
        style={{
          width: 38,
          height: 22,
          borderRadius: 22,
          background: isDark
            ? 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)'
            : 'rgba(255, 255, 255, 0.14)',
          border: isDark
            ? '1.5px solid rgba(56, 189, 248, 0.5)'
            : '1.5px solid rgba(255, 255, 255, 0.15)',
          boxShadow: isDark
            ? '0 0 10px rgba(2, 132, 199, 0.45)'
            : 'inset 0 1px 3px rgba(0, 0, 0, 0.3)',
          display: 'flex',
          alignItems: 'center',
          padding: 2,
          transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          pointerEvents: 'none',
          flexShrink: 0
        }}
      >
        <Box
          style={{
            width: 14,
            height: 14,
            borderRadius: '50%',
            background: '#ffffff',
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
            transform: isDark ? 'translateX(16px)' : 'translateX(0px)',
            transition: 'transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1)'
          }}
        />
      </Box>
    </UnstyledButton>
  );
}

export function AppSidebar() {
  const match = useMatch(':tabName/*');
  const tabValue = match?.params.tabName ?? '';
  const userState = useUserState();
  const { user } = userState;
  const navigate = useNavigate();
  const location = useLocation();
  const pathname = location.pathname;
  const isStaff =
    userState.isStaff() ||
    user?.is_staff ||
    userState.isSuperuser() ||
    user?.is_superuser;
  const globalSettings = useGlobalSettingsState();
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const isDark = colorScheme === 'dark';

  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    try {
      return localStorage.getItem('inventree-dock-collapsed') === 'true';
    } catch {
      return false;
    }
  });

  const toggleCollapse = useCallback(() => {
    setIsCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('inventree-dock-collapsed', String(next));
      } catch {}
      return next;
    });
  }, []);

  const [settingsOpen, { toggle: toggleSettings }] = useDisclosure(
    pathname.startsWith('/settings')
  );

  const isCategoriesActive = useMemo(() => {
    if (pathname.includes('/part/category/index/subcategories')) {
      return true;
    }
    if (pathname.startsWith('/part/category') && !pathname.includes('/parts')) {
      return true;
    }
    return false;
  }, [pathname]);

  const isProductsActive = useMemo(() => {
    if (pathname.includes('/part/category/index/parts')) {
      return true;
    }
    if (pathname.startsWith('/part/') && !pathname.startsWith('/part/category')) {
      return true;
    }
    if (pathname.startsWith('/part/category') && pathname.includes('/parts')) {
      return true;
    }
    if (pathname === '/part' || pathname === '/part/') {
      return true;
    }
    return false;
  }, [pathname]);

  const isPurchasingActive = useMemo(() => {
    if (
      pathname.includes('/purchasing/index/purchaseorders') ||
      pathname.startsWith('/purchasing/purchase-order')
    ) {
      return true;
    }
    if (
      (pathname === '/purchasing' ||
        pathname === '/purchasing/' ||
        pathname === '/purchasing/index' ||
        pathname === '/purchasing/index/') &&
      !pathname.includes('supplier') &&
      !pathname.includes('manufacturer')
    ) {
      return true;
    }
    return false;
  }, [pathname]);

  const isSuppliersActive = useMemo(() => {
    if (
      pathname.includes('/purchasing/index/suppliers') ||
      pathname.includes('/purchasing/index/supplier-parts') ||
      pathname.includes('/purchasing/index/manufacturer') ||
      pathname.startsWith('/purchasing/supplier') ||
      pathname.startsWith('/purchasing/manufacturer')
    ) {
      return true;
    }
    return false;
  }, [pathname]);

  const isDashboardActive = useMemo(() => {
    return pathname === '/' || pathname === '/home' || pathname === '/home/';
  }, [pathname]);

  const isActive = (path: string) => {
    if (!path) return false;
    if (path === '/' || path === 'home') {
      return pathname === '/' || pathname === '/home' || pathname === '/home/';
    }
    return tabValue === path || pathname.startsWith(`/${path}`);
  };

  const canViewParts = userState.hasViewRole(UserRoles.part);
  const canViewCategories =
    userState.hasViewRole(UserRoles.part_category) ||
    userState.hasViewRole(UserRoles.part);
  const canViewStock = userState.hasViewRole(UserRoles.stock);
  const canViewBuild = userState.hasViewRole(UserRoles.build);
  const canViewPurchase = userState.hasViewRole(UserRoles.purchase_order);
  const canViewSales = userState.hasViewRole(UserRoles.sales_order);

  const currentWidth = isCollapsed ? COLLAPSED_WIDTH : SIDEBAR_WIDTH;

  return (
    <>
      {/* Sidebar hover & transition CSS */}
      <style>{`
        .sidebar-nav-item[data-clickable='true']:hover:not([data-active='true']) {
          background-color: ${SIDEBAR_ITEM_HOVER_BG} !important;
        }
        .sidebar-nav-item[data-clickable='true']:hover:not([data-active='true']) .mantine-Text-root {
          color: #ffffff !important;
        }
        .sidebar-edge-toggle:hover {
          background-color: #0284c7 !important;
          border-color: #38bdf8 !important;
          color: #ffffff !important;
          transform: scale(1.12);
          box-shadow: 0 0 12px rgba(56, 189, 248, 0.6) !important;
        }
      `}</style>

      <Box
        style={{
          width: currentWidth,
          minWidth: currentWidth,
          maxWidth: currentWidth,
          height: '100vh',
          background: SIDEBAR_BG,
          display: 'flex',
          flexDirection: 'column',
          position: 'sticky',
          top: 0,
          zIndex: 100,
          boxShadow: '4px 0 24px rgba(15, 23, 42, 0.35)',
          borderRight: '1px solid rgba(255, 255, 255, 0.06)',
          flexShrink: 0,
          transition:
            'width 0.28s cubic-bezier(0.4, 0, 0.2, 1), min-width 0.28s cubic-bezier(0.4, 0, 0.2, 1), max-width 0.28s cubic-bezier(0.4, 0, 0.2, 1)',
          overflow: 'visible'
        }}
      >
        {/* ─── Floating Edge Toggle Handle (Slide In/Out Option) ─── */}
        <Tooltip
          label={isCollapsed ? t`Expand dock` : t`Slide in dock (shrink to 20%)`}
          position='right'
          withArrow
          offset={8}
        >
          <Box
            onClick={toggleCollapse}
            className='sidebar-edge-toggle'
            style={{
              position: 'absolute',
              top: 18,
              right: -12,
              zIndex: 110,
              width: 24,
              height: 24,
              borderRadius: '50%',
              background: '#0b1120',
              border: '1.5px solid rgba(56, 189, 248, 0.45)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.45)',
              color: '#38bdf8',
              transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)'
            }}
          >
            {isCollapsed ? (
              <IconChevronRight size={13} stroke={2.5} />
            ) : (
              <IconChevronLeft size={13} stroke={2.5} />
            )}
          </Box>
        </Tooltip>

        {/* ─── Logo / Brand Header ─── */}
        {isCollapsed ? (
          <Box
            p='xs'
            style={{
              borderBottom: '1px solid rgba(255,255,255,0.06)',
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              height: 60
            }}
          >
            <Tooltip label={t`Expand dock (click to slide out)`} position='right' withArrow>
              <UnstyledButton
                onClick={toggleCollapse}
                style={{
                  background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
                  borderRadius: 10,
                  width: 34,
                  height: 34,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 4px 14px rgba(2, 132, 199, 0.4)',
                  cursor: 'pointer'
                }}
              >
                <IconCube size={18} color='white' />
              </UnstyledButton>
            </Tooltip>
          </Box>
        ) : (
          <Group
            align='center'
            wrap='nowrap'
            p='md'
            pb={12}
            style={{
              borderBottom: '1px solid rgba(255,255,255,0.06)',
              height: 60
            }}
          >
            <Group gap={10} wrap='nowrap'>
              <Box
                style={{
                  background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
                  borderRadius: 10,
                  width: 36,
                  height: 36,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexShrink: 0,
                  boxShadow: '0 4px 14px rgba(2, 132, 199, 0.4)'
                }}
              >
                <IconCube size={20} color='white' />
              </Box>
              <Text fw={700} size='sm' c='white' lh={1.2} style={{ whiteSpace: 'nowrap', letterSpacing: '0.2px' }}>
                TPI Inventory
              </Text>
            </Group>
          </Group>
        )}

        {/* ─── Navigation ─── */}
        <ScrollArea
          style={{ flex: 1, minHeight: 0, overflowX: 'hidden' }}
          scrollbarSize={isCollapsed ? 0 : 4}
          p={isCollapsed ? 4 : 'xs'}
        >
          <Stack gap={isCollapsed ? 'xs' : 'md'} pt='xs'>

            {/* DISCOVER */}
            <SidebarGroup label={t`Discover`} collapsed={isCollapsed}>
              <SidebarItem
                icon={<IconLayoutDashboard size={16} />}
                label={t`Dashboard`}
                link='/home'
                active={isDashboardActive}
                collapsed={isCollapsed}
              />
              <SidebarItem
                icon={<IconBuildingStore size={16} />}
                label={t`Stores`}
                link='/stock'
                active={isActive('stock')}
                collapsed={isCollapsed}
              />
              <SidebarItem
                icon={<IconBuildingBank size={16} style={{ color: '#2ca01c' }} />}
                label={t`QuickBooks`}
                link='/quickbooks'
                active={isActive('quickbooks')}
                collapsed={isCollapsed}
              />
            </SidebarGroup>

            {/* INVENTORY */}
            <SidebarGroup label={t`Inventory`} collapsed={isCollapsed}>
              {canViewParts && (
                <SidebarItem
                  icon={<IconBox size={16} />}
                  label={t`Products`}
                  link='/part/category/index/parts'
                  active={isProductsActive}
                  collapsed={isCollapsed}
                />
              )}
              {canViewCategories && (
                <SidebarItem
                  icon={<IconCategory size={16} />}
                  label={t`Categories`}
                  link='/part/category/index/subcategories'
                  active={isCategoriesActive}
                  collapsed={isCollapsed}
                />
              )}
              {canViewPurchase && (
                <SidebarItem
                  icon={<IconUsers size={16} />}
                  label={t`Suppliers`}
                  link='/purchasing/index/suppliers'
                  active={isSuppliersActive}
                  collapsed={isCollapsed}
                />
              )}
              {canViewBuild && (
                <SidebarItem
                  icon={<IconBuildingFactory2 size={16} />}
                  label={t`Manufacturing`}
                  link='/manufacturing'
                  active={isActive('manufacturing')}
                  collapsed={isCollapsed}
                />
              )}
              {canViewPurchase && (
                <SidebarItem
                  icon={<IconShoppingCart size={16} />}
                  label={t`Purchasing`}
                  link='/purchasing/index/purchaseorders'
                  active={isPurchasingActive}
                  collapsed={isCollapsed}
                />
              )}
              {canViewSales && (
                <SidebarItem
                  icon={<IconTruckDelivery size={16} />}
                  label={t`Sales`}
                  link='/sales'
                  active={isActive('sales')}
                  collapsed={isCollapsed}
                />
              )}
              <SidebarItem
                icon={<IconCreditCard size={16} />}
                label={t`Billing`}
                collapsed={isCollapsed}
              />
              <SidebarItem
                icon={<IconClipboardList size={16} />}
                label={t`Orders`}
                collapsed={isCollapsed}
              />
              <SidebarItem
                icon={<IconPackages size={16} />}
                label={t`Delivery`}
                collapsed={isCollapsed}
              />
              <SidebarItem
                icon={<IconFileAnalytics size={16} />}
                label={t`Reports`}
                collapsed={isCollapsed}
              />
            </SidebarGroup>

          </Stack>
        </ScrollArea>

        {/* ─── Settings (bottom pinned) ─── */}
        {isCollapsed ? (
          <Box
            p={4}
            py='xs'
            style={{
              borderTop: '1px solid rgba(255,255,255,0.06)',
              flexShrink: 0,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: 4
            }}
          >
            {/* Settings Menu Popup in collapsed mode */}
            <Menu position='right-end' withArrow offset={10} shadow='md' withinPortal>
              <Menu.Target>
                <Tooltip label={t`Settings`} position='right' offset={14} withArrow>
                  <UnstyledButton
                    style={{
                      width: 36,
                      height: 36,
                      borderRadius: 10,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      color: SIDEBAR_ITEM_DEFAULT,
                      cursor: 'pointer',
                      transition: 'all 0.18s ease'
                    }}
                    className='sidebar-nav-item'
                  >
                    <IconSettings size={18} style={{ color: '#38bdf8' }} />
                  </UnstyledButton>
                </Tooltip>
              </Menu.Target>
              <Menu.Dropdown
                style={{
                  background: '#0b1120',
                  borderColor: 'rgba(255, 255, 255, 0.12)',
                  boxShadow: '0 10px 25px rgba(0,0,0,0.5)'
                }}
              >
                <Menu.Label style={{ color: '#64748b' }}>{t`Settings`}</Menu.Label>
                <Menu.Item
                  leftSection={<IconUserCog size={15} style={{ color: '#38bdf8' }} />}
                  onClick={() => navigate('/settings/user')}
                  style={{ color: '#e2e8f0', fontSize: 13 }}
                >
                  {t`User Settings`}
                </Menu.Item>
                {isStaff && (
                  <Menu.Item
                    leftSection={<IconUserBolt size={15} style={{ color: '#38bdf8' }} />}
                    onClick={() => navigate('/settings/admin')}
                    style={{ color: '#e2e8f0', fontSize: 13 }}
                  >
                    {t`Admin Settings`}
                  </Menu.Item>
                )}
                {isStaff && (
                  <Menu.Item
                    leftSection={<IconSettings size={15} style={{ color: '#38bdf8' }} />}
                    onClick={() => navigate('/settings/system')}
                    style={{ color: '#e2e8f0', fontSize: 13 }}
                  >
                    {t`System Settings`}
                  </Menu.Item>
                )}
              </Menu.Dropdown>
            </Menu>

            {/* Dark Mode Toggle in collapsed mode */}
            <Tooltip
              label={isDark ? t`Light Mode` : t`Dark Mode`}
              position='right'
              offset={14}
              withArrow
            >
              <UnstyledButton
                onClick={toggleColorScheme}
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: SIDEBAR_ITEM_DEFAULT,
                  cursor: 'pointer',
                  transition: 'all 0.18s ease'
                }}
                className='sidebar-nav-item'
              >
                {isDark ? (
                  <IconSun size={18} style={{ color: '#fcc419' }} />
                ) : (
                  <IconMoonStars size={18} style={{ color: '#74c0fc' }} />
                )}
              </UnstyledButton>
            </Tooltip>

            {/* Help Button in collapsed mode */}
            <Tooltip label={t`Help`} position='right' offset={14} withArrow>
              <UnstyledButton
                onClick={() => aboutInvenTree()}
                style={{
                  width: 36,
                  height: 36,
                  borderRadius: 10,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: SIDEBAR_ITEM_DEFAULT,
                  cursor: 'pointer',
                  transition: 'all 0.18s ease'
                }}
                className='sidebar-nav-item'
              >
                <IconHelpCircle size={18} style={{ color: '#38bdf8' }} />
              </UnstyledButton>
            </Tooltip>
          </Box>
        ) : (
          <Box
            p='xs'
            style={{
              borderTop: '1px solid rgba(255,255,255,0.06)',
              flexShrink: 0
            }}
          >
            <Text
              size='xs'
              fw={700}
              tt='uppercase'
              style={{
                letterSpacing: '0.8px',
                color: SIDEBAR_SECTION_LABEL,
                padding: '4px 12px 6px'
              }}
            >
              {t`Settings`}
            </Text>

            {/* Settings tab with downward chevron */}
            <UnstyledButton
              onClick={toggleSettings}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                width: '100%',
                padding: '8px 12px',
                borderRadius: 10,
                color: settingsOpen ? '#ffffff' : SIDEBAR_ITEM_DEFAULT,
                backgroundColor: settingsOpen
                  ? 'rgba(2, 132, 199, 0.15)'
                  : 'transparent',
                fontSize: 13,
                transition: 'all 0.18s ease',
                cursor: 'pointer'
              }}
              className='sidebar-nav-item'
            >
              <Group gap={10} wrap='nowrap'>
                <IconSettings
                  size={16}
                  style={{
                    color: settingsOpen ? '#38bdf8' : '#38bdf8',
                    opacity: 0.85,
                    flexShrink: 0
                  }}
                />
                <Text size='sm' c={settingsOpen ? 'white' : SIDEBAR_ITEM_DEFAULT}>
                  {t`Settings`}
                </Text>
              </Group>
              <IconChevronDown
                size={14}
                color={settingsOpen ? '#38bdf8' : SIDEBAR_SECTION_LABEL}
                style={{
                  transform: settingsOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                  transition: 'transform 0.2s ease',
                  flexShrink: 0
                }}
              />
            </UnstyledButton>

            <Collapse expanded={settingsOpen}>
              <SettingsSubMenu />
            </Collapse>

            {/* Dark Mode toggle item */}
            <DarkModeToggleItem isDark={isDark} onToggle={toggleColorScheme} />

            {/* Help item */}
            <SidebarItem
              icon={<IconHelpCircle size={16} />}
              label={t`Help`}
              action={() => aboutInvenTree()}
            />
          </Box>
        )}
      </Box>
    </>
  );
}
