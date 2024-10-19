import {
  ActionIcon,
  Button,
  Group,
  Menu,
  Text,
  Tooltip,
  useMantineTheme
} from '@mantine/core';
import { IconChevronDown } from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';

import { identifierString } from '../../functions/conversion';
import type { TablerIconType } from '../../functions/icons';
import * as classes from './SplitButton.css';

interface SplitButtonOption {
  key: string;
  name: string;
  onClick: () => void;
  icon: TablerIconType;
  disabled?: boolean;
  tooltip?: string;
}

interface SplitButtonProps {
  options: SplitButtonOption[];
  defaultSelected: string;
  name: string;
  selected?: string;
  setSelected?: (value: string) => void;
  loading?: boolean;
}

export function SplitButton({
  options,
  defaultSelected,
  selected,
  name,
  setSelected,
  loading
}: Readonly<SplitButtonProps>) {
  const [current, setCurrent] = useState<string>(defaultSelected);

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
    <Group wrap='nowrap' style={{ gap: 0 }}>
      <Button
        onClick={currentOption?.onClick}
        disabled={loading ? false : currentOption?.disabled}
        className={classes.button}
        loading={loading}
        aria-label={`split-button-${name}`}
      >
        {currentOption?.name}
      </Button>
      <Menu
        transitionProps={{ transition: 'pop' }}
        position='bottom-end'
        withinPortal
      >
        <Menu.Target>
          <ActionIcon
            variant='filled'
            color={theme.primaryColor}
            size={36}
            className={classes.icon}
            aria-label={`split-button-${name}-action`}
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
              aria-label={`split-button-${name}-item-${identifierString(
                option.key
              )}`}
              disabled={option.disabled}
              leftSection={<option.icon />}
            >
              <Tooltip label={option.tooltip} position='right'>
                <Text>{option.name}</Text>
              </Tooltip>
            </Menu.Item>
          ))}
        </Menu.Dropdown>
      </Menu>
    </Group>
  );
}
