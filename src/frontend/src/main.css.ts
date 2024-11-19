import { rem } from '@mantine/core';
import { style } from '@vanilla-extract/css';

import { vars } from './theme';

export const layoutHeader = style({
  paddingTop: vars.spacing.sm,
  marginBottom: 10,

  [vars.lightSelector]: {
    backgroundColor: vars.colors.gray[0],
    borderBottom: `${rem(1)} solid ${vars.colors.gray[2]}`
  },
  [vars.darkSelector]: {
    backgroundColor: vars.colors.dark[6],
    borderBottom: `${rem(1)} solid transparent`
  }
});

export const layoutFooter = style({
  marginTop: 10,
  [vars.lightSelector]: { borderTop: `1px solid ${vars.colors.gray[2]}` },
  [vars.darkSelector]: { borderTop: `1px solid ${vars.colors.dark[5]}` }
});

export const layoutHeaderSection = style({
  paddingBottom: vars.spacing.sm
});

export const layoutHeaderUser = style({
  padding: `${vars.spacing.xs}px ${vars.spacing.sm}px`,
  borderRadius: vars.radiusDefault,
  transition: 'background-color 100ms ease',

  [vars.lightSelector]: { color: vars.colors.black },
  [vars.darkSelector]: { color: vars.colors.dark[0] },

  [vars.smallerThan('xs')]: {
    display: 'none'
  }
});

export const headerDropdownFooter = style({
  margin: `calc(${vars.spacing.md} * -1)`,
  marginTop: vars.spacing.sm,
  padding: `${vars.spacing.md} calc(${vars.spacing.md} * 2)`,
  paddingBottom: vars.spacing.xl,

  [vars.lightSelector]: {
    backgroundColor: vars.colors.gray[0],
    borderTop: `${rem(1)} solid ${vars.colors.gray[1]}`
  },
  [vars.darkSelector]: {
    backgroundColor: vars.colors.dark[7],
    borderTop: `${rem(1)} solid ${vars.colors.dark[5]}`
  }
});

export const link = style({
  display: 'flex',
  alignItems: 'center',
  height: '100%',
  paddingLeft: vars.spacing.md,
  paddingRight: vars.spacing.md,
  textDecoration: 'none',
  fontWeight: 500,
  fontSize: vars.fontSizes.sm,

  [vars.lightSelector]: { color: vars.colors.black },
  [vars.darkSelector]: { color: vars.colors.white },

  [vars.smallerThan('sm')]: {
    height: rem(42),
    display: 'flex',
    alignItems: 'center',
    width: '100%'
  },

  ':hover': {
    [vars.lightSelector]: { backgroundColor: vars.colors.gray[0] },
    [vars.darkSelector]: { backgroundColor: vars.colors.dark[6] }
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
  [vars.smallerThan('sm')]: {
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
    [vars.lightSelector]: { backgroundColor: vars.colors.gray[1] },
    [vars.darkSelector]: { backgroundColor: vars.colors.dark[5] }
  }
});

export const signText = style({
  fontSize: 'xl',
  fontWeight: 700
});

export const error = style({
  backgroundColor: vars.colors.gray[0],
  color: vars.colors.red[6]
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
  [vars.lightSelector]: { backgroundColor: vars.colors.white },
  [vars.darkSelector]: { backgroundColor: vars.colors.dark[7] }
});

export const itemTopBorder = style({
  [vars.lightSelector]: { borderTop: `1px solid ${vars.colors.gray[2]}` },
  [vars.darkSelector]: { borderTop: `1px solid ${vars.colors.dark[4]}` }
});

export const navigationDrawer = style({
  padding: 0
});
