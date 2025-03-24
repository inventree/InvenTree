import { rem } from '@mantine/core';
import { style } from '@vanilla-extract/css';

import { themeVars } from '@lib/index';

export const layoutHeader = style({
  paddingTop: themeVars.spacing.sm,
  marginBottom: 10,

  [themeVars.lightSelector]: {
    backgroundColor: themeVars.colors.gray[0],
    borderBottom: `${rem(1)} solid ${themeVars.colors.gray[2]}`
  },
  [themeVars.darkSelector]: {
    backgroundColor: themeVars.colors.dark[6],
    borderBottom: `${rem(1)} solid transparent`
  }
});

export const layoutFooter = style({
  marginTop: 10,
  [themeVars.lightSelector]: {
    borderTop: `1px solid ${themeVars.colors.gray[2]}`
  },
  [themeVars.darkSelector]: {
    borderTop: `1px solid ${themeVars.colors.dark[5]}`
  }
});

export const layoutHeaderSection = style({
  paddingBottom: themeVars.spacing.sm
});

export const layoutHeaderUser = style({
  padding: `${themeVars.spacing.xs}px ${themeVars.spacing.sm}px`,
  borderRadius: themeVars.radiusDefault,
  transition: 'background-color 100ms ease',

  [themeVars.lightSelector]: { color: themeVars.colors.black },
  [themeVars.darkSelector]: { color: themeVars.colors.dark[0] },

  [themeVars.smallerThan('xs')]: {
    display: 'none'
  }
});

export const headerDropdownFooter = style({
  margin: `calc(${themeVars.spacing.md} * -1)`,
  marginTop: themeVars.spacing.sm,
  padding: `${themeVars.spacing.md} calc(${themeVars.spacing.md} * 2)`,
  paddingBottom: themeVars.spacing.xl,

  [themeVars.lightSelector]: {
    backgroundColor: themeVars.colors.gray[0],
    borderTop: `${rem(1)} solid ${themeVars.colors.gray[1]}`
  },
  [themeVars.darkSelector]: {
    backgroundColor: themeVars.colors.dark[7],
    borderTop: `${rem(1)} solid ${themeVars.colors.dark[5]}`
  }
});

export const link = style({
  display: 'flex',
  alignItems: 'center',
  height: '100%',
  paddingLeft: themeVars.spacing.md,
  paddingRight: themeVars.spacing.md,
  textDecoration: 'none',
  fontWeight: 500,
  fontSize: themeVars.fontSizes.sm,

  [themeVars.lightSelector]: { color: themeVars.colors.black },
  [themeVars.darkSelector]: { color: themeVars.colors.white },

  [themeVars.smallerThan('sm')]: {
    height: rem(42),
    display: 'flex',
    alignItems: 'center',
    width: '100%'
  },

  ':hover': {
    [themeVars.lightSelector]: { backgroundColor: themeVars.colors.gray[0] },
    [themeVars.darkSelector]: { backgroundColor: themeVars.colors.dark[6] }
  }
});

export const docHover = style({
  border: '1px dashed '
});

export const layoutContent = style({
  flex: 1,
  width: '100%'
});

export const tabs = style({
  [themeVars.smallerThan('sm')]: {
    display: 'none'
  }
});

export const tabsList = style({
  borderBottom: '0 !important'
});

export const tab = style({
  fontWeight: 500,
  height: 38,
  backgroundColor: 'transparent',

  ':hover': {
    [themeVars.lightSelector]: { backgroundColor: themeVars.colors.gray[1] },
    [themeVars.darkSelector]: { backgroundColor: themeVars.colors.dark[5] }
  },

  selectors: {
    '&[data-active]': {
      backgroundColor: themeVars.colors.primaryColors.light
    }
  }
});

export const error = style({
  backgroundColor: themeVars.colors.gray[0],
  color: themeVars.colors.red[6]
});

export const dashboardItemValue = style({
  fontSize: 24,
  fontWeight: 700,
  lineHeight: 1
});

export const dashboardItemTitle = style({
  fontWeight: 700
});

export const card = style({
  [themeVars.lightSelector]: { backgroundColor: themeVars.colors.white },
  [themeVars.darkSelector]: { backgroundColor: themeVars.colors.dark[7] }
});

export const itemTopBorder = style({
  [themeVars.lightSelector]: {
    borderTop: `1px solid ${themeVars.colors.gray[2]}`
  },
  [themeVars.darkSelector]: {
    borderTop: `1px solid ${themeVars.colors.dark[4]}`
  }
});

export const navigationDrawer = style({
  padding: 0
});
