import {
  ActionIcon,
  Button,
  Group,
  Menu,
  Text,
  Tooltip,
  createStyles,
  useMantineTheme
} from '@mantine/core';
import { IconChevronDown, TablerIconsProps } from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';

interface SplitButtonOption {
  key: string;
  name: string;
  onClick: () => void;
  icon: (props: TablerIconsProps) => JSX.Element;
  disabled?: boolean;
  tooltip?: string;
}

interface SplitButtonProps {
  options: SplitButtonOption[];
  defaultSelected: string;
  selected?: string;
  setSelected?: (value: string) => void;
  loading?: boolean;
}

const useStyles = createStyles((theme) => ({
  button: {
    borderTopRightRadius: 0,
    borderBottomRightRadius: 0,
    '&::before': {
      borderRadius: '0 !important'
    }
  },
  icon: {
    borderTopLeftRadius: 0,
    borderBottomLeftRadius: 0,
    border: 0,
    borderLeft: `1px solid ${theme.primaryShade}`
  }
}));

export function SplitButton({
  options,
  defaultSelected,
  selected,
  setSelected,
  loading
}: SplitButtonProps) {
  const [current, setCurrent] = useState<string>(defaultSelected);
  const { classes } = useStyles();

  useEffect(() => {
    setSelected?.(current);
  }, [current]);

  useEffect(() => {
    if (!selected) return;
    setCurrent(selected);
  }, [selected]);

  const currentOption = useMemo(() => {
    return options.find((option) => option.key === current);
  }, [current, options]);

  const theme = useMantineTheme();

  return (
    <Group noWrap style={{ gap: 0 }}>
      <Button
        onClick={currentOption?.onClick}
        disabled={loading ? false : currentOption?.disabled}
        className={classes.button}
        loading={loading}
      >
        {currentOption?.name}
      </Button>
      <Menu
        transitionProps={{ transition: 'pop' }}
        position="bottom-end"
        withinPortal
      >
        <Menu.Target>
          <ActionIcon
            variant="filled"
            color={theme.primaryColor}
            size={36}
            className={classes.icon}
          >
            <IconChevronDown size={16} />
          </ActionIcon>
        </Menu.Target>

        <Menu.Dropdown>
          {options.map((option) => (
            <Menu.Item
              key={option.key}
              onClick={() => {
                setCurrent(option.key);
                option.onClick();
              }}
              disabled={option.disabled}
              icon={<option.icon />}
            >
              <Tooltip label={option.tooltip} position="right">
                <Text>{option.name}</Text>
              </Tooltip>
            </Menu.Item>
          ))}
        </Menu.Dropdown>
      </Menu>
    </Group>
  );
}
