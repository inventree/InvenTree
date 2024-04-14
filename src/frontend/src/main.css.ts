import { rem } from '@mantine/core';
import { style } from '@vanilla-extract/css';

import { vars } from './theme';

export const layoutHeader = style({
  paddingTop: vars.spacing.sm,
  backgroundColor: vars.colors.gray[0],
  //theme.colorScheme === 'dark' ? vars.colors.dark[6] : vars.colors.gray[0],
  borderBottom: `1px solid ${
    //theme.colorScheme === 'dark' ? 'transparent' : vars.colors.gray[2]
    vars.colors.gray[2]
  }`,
  marginBottom: 10
});

export const layoutFooter = style({
  marginTop: 10,
  borderTop: `1px solid ${
    //theme.colorScheme === 'dark' ? vars.colors.dark[5] : vars.colors.gray[2]
    vars.colors.gray[2]
  }`
});

export const layoutHeaderSection = style({
  paddingBottom: vars.spacing.sm
});

export const layoutHeaderUser = style({
  color:
    //theme.colorScheme === 'dark' ? vars.colors.dark[0] : vars.black,
    vars.colors.black,
  padding: `${vars.spacing.xs}px ${vars.spacing.sm}px`,
  borderRadius: vars.defaultRadius,
  transition: 'background-color 100ms ease',

  [vars.smallerThan('xs')]: {
    display: 'none'
  }
});

export const headerDropdownFooter = style({
  backgroundColor:
    //theme.colorScheme === 'dark' ? vars.colors.dark[7] : vars.colors.gray[0],
    vars.colors.gray[0],
  margin: `calc(${vars.spacing.md} * -1)`,
  marginTop: vars.spacing.sm,
  padding: `${vars.spacing.md} calc(${vars.spacing.md} * 2)`,
  paddingBottom: vars.spacing.xl,
  borderTop: `${rem(1)} solid ${
    //theme.colorScheme === 'dark' ? vars.colors.dark[5] : vars.colors.gray[1]
    vars.colors.gray[1]
  }`
});

export const link = style({
  display: 'flex',
  alignItems: 'center',
  height: '100%',
  paddingLeft: vars.spacing.md,
  paddingRight: vars.spacing.md,
  textDecoration: 'none',
  color:
    //theme.colorScheme === 'dark' ? vars.white: vars.black,
    vars.colors.black,
  fontWeight: 500,
  fontSize: vars.fontSizes.sm,

  [vars.smallerThan('sm')]: {
    height: rem(42),
    display: 'flex',
    alignItems: 'center',
    width: '100%'
  }

  // ...theme.fn.hover({
  //   backgroundColor:
  //     theme.colorScheme === 'dark'
  //       ? vars.colors.dark[6]
  //       : vars.colors.gray[0]
  // })
});

export const subLink = style({
  width: '100%',
  padding: `${vars.spacing.xs} ${vars.spacing.md}`,
  borderRadius: vars.defaultRadius,

  // ...theme.fn.hover({
  //   backgroundColor:
  //     theme.colorScheme === 'dark'
  //       ? vars.colors.dark[7]
  //       : vars.colors.gray[0]
  // })

  '&:active': vars.activeStyles
});

export const docHover = style({
  border: `1px dashed `
});

export const layoutContent = style({
  flex: 1,
  width: '100%'
});

export const layoutFooterLinks = style({
  [vars.smallerThan('xs')]: {
    marginTop: vars.spacing.md
  }
});

export const layoutFooterInner = style({
  display: 'flex',
  justifyContent: 'space-between',
  alignItems: 'center',
  paddingTop: vars.spacing.xl,
  paddingBottom: vars.spacing.xl,

  [vars.smallerThan('xs')]: {
    flexDirection: 'column'
  }
});

export const tabs = style({
  [vars.smallerThan('sm')]: {
    display: 'none'
  }
});

export const tabsList = style({
  borderBottom: '0 !important',
  '& > button:first-of-type': {
    paddingLeft: '0 !important'
  },

  '& > button:last-of-type': {
    paddingRight: '0 !important'
  }
});

export const tab = style({
  fontWeight: 500,
  height: 38,
  backgroundColor: 'transparent',

  '&:hover': {
    backgroundColor:
      //theme.colorScheme === 'dark' ? vars.colors.dark[5] : vars.colors.gray[1]
      vars.colors.gray[1]
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
  backgroundColor:
    //theme.colorScheme === 'dark' ? vars.colors.dark[7] : vars.white
    vars.colors.white
});

export const itemTopBorder = style({
  borderTop: `1px solid ${
    //theme.colorScheme === 'dark' ? vars.colors.dark[4] : vars.colors.gray[2]
    vars.colors.gray[2]
  }`
});

export const navigationDrawer = style({
  padding: 0
});
