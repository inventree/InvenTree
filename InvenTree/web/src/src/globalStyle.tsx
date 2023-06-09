import { createStyles } from '@mantine/core';

export const InvenTreeStyle = createStyles((theme) => ({
  layoutHeader: {
    paddingTop: theme.spacing.sm,
    backgroundColor:
      theme.colorScheme === 'dark'
        ? theme.colors.dark[6]
        : theme.colors.gray[0],
    borderBottom: `1px solid ${theme.colorScheme === 'dark' ? 'transparent' : theme.colors.gray[2]
      }`,
    marginBottom: 10
  },

  layoutFooter: {
    marginTop: 10,
    borderTop: `1px solid ${theme.colorScheme === 'dark' ? theme.colors.dark[5] : theme.colors.gray[2]
      }`
  },

  layoutHeaderSection: {
    paddingBottom: theme.spacing.sm
  },

  layoutHeaderUser: {
    color: theme.colorScheme === 'dark' ? theme.colors.dark[0] : theme.black,
    padding: `${theme.spacing.xs}px ${theme.spacing.sm}px`,
    borderRadius: theme.defaultRadius,
    transition: 'background-color 100ms ease',

    '&:hover': {
      backgroundColor:
        theme.colorScheme === 'dark' ? theme.colors.dark[8] : theme.white
    },

    [theme.fn.smallerThan('xs')]: {
      display: 'none'
    }
  },

  layoutHeaderUserActive: {
    backgroundColor:
      theme.colorScheme === 'dark' ? theme.colors.dark[8] : theme.white
  },

  layoutContent: {
    flex: 1,
    width: '100%'
  },

  layoutFooterLinks: {
    [theme.fn.smallerThan('xs')]: {
      marginTop: theme.spacing.md
    }
  },

  layoutFooterInner: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: theme.spacing.xl,
    paddingBottom: theme.spacing.xl,

    [theme.fn.smallerThan('xs')]: {
      flexDirection: 'column'
    }
  },

  tabs: {
    [theme.fn.smallerThan('sm')]: {
      display: 'none'
    }
  },

  tabsList: {
    borderBottom: '0 !important'
  },

  tab: {
    fontWeight: 500,
    height: 38,
    backgroundColor: 'transparent',

    '&:hover': {
      backgroundColor:
        theme.colorScheme === 'dark'
          ? theme.colors.dark[5]
          : theme.colors.gray[1]
    },

    '&[data-active]': {
      backgroundColor:
        theme.colorScheme === 'dark' ? theme.colors.dark[7] : theme.white,
      borderColor:
        theme.colorScheme === 'dark'
          ? theme.colors.dark[7]
          : theme.colors.gray[2]
    }
  },

  signText: {
    fontSize: 'xl',
    fontWeight: 700
  },

  error: {
    backgroundColor: theme.colors.gray[0],
    color: theme.colors.red[6]
  },

  dashboardItemValue: {
    fontSize: 24,
    fontWeight: 700,
    lineHeight: 1
  },

  dashboardItemTitle: {
    fontWeight: 700
  },

  card: {
    backgroundColor: theme.colorScheme === 'dark' ? theme.colors.dark[7] : theme.white,
  },

  itemTopBorder: {
    borderTop: `1px solid ${theme.colorScheme === 'dark' ? theme.colors.dark[4] : theme.colors.gray[2]}`
  },
}));
