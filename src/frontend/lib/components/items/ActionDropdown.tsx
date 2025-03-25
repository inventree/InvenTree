import { t } from '@lingui/core/macro';
import {
  Button,
  type FloatingPosition,
  Indicator,
  type IndicatorProps,
  Menu,
  Tooltip
} from '@mantine/core';
import { IconChevronDown, IconDotsVertical } from '@tabler/icons-react';
import { type ReactNode, useMemo } from 'react';
import { identifierString } from '../../functions/conversion';

export type ActionDropdownItem = {
  icon?: ReactNode;
  name?: string;
  tooltip?: string;
  disabled?: boolean;
  hidden?: boolean;
  onClick: (event?: any) => void;
  indicator?: Omit<IndicatorProps, 'children'>;
};

/**
 * A simple Menu component which renders a set of actions.
 *
 * If no "active" actions are provided, the menu will not be rendered
 */
export function ActionDropdown({
  icon,
  tooltip,
  tooltipPosition,
  actions,
  disabled = false,
  hidden = false,
  noindicator = false
}: {
  icon: ReactNode;
  tooltip: string;
  tooltipPosition?: FloatingPosition;
  actions: ActionDropdownItem[];
  disabled?: boolean;
  hidden?: boolean;
  noindicator?: boolean;
}) {
  const hasActions = useMemo(() => {
    return actions.some((action) => !action.hidden);
  }, [actions]);

  const indicatorProps = useMemo(() => {
    return actions.find((action) => action.indicator);
  }, [actions]);

  const menuName: string = useMemo(() => {
    return identifierString(`action-menu-${tooltip}`);
  }, [tooltip]);

  return !hidden && hasActions ? (
    <Menu position='bottom-end' key={menuName}>
      <Indicator disabled={!indicatorProps} {...indicatorProps?.indicator}>
        <Menu.Target>
          <Tooltip
            label={tooltip}
            hidden={!tooltip}
            position={tooltipPosition ?? 'bottom'}
          >
            <Button
              variant={noindicator ? 'transparent' : 'light'}
              disabled={disabled}
              aria-label={menuName}
              p='0'
              size='sm'
              rightSection={
                noindicator ? null : <IconChevronDown stroke={1.5} />
              }
              styles={{
                section: { margin: 0 }
              }}
            >
              {icon}
            </Button>
          </Tooltip>
        </Menu.Target>
      </Indicator>
      <Menu.Dropdown>
        {actions.map((action) => {
          const id: string = identifierString(`${menuName}-${action.name}`);
          return action.hidden ? null : (
            <Indicator
              disabled={!action.indicator}
              {...action.indicator}
              key={action.name}
            >
              <Tooltip
                label={action.tooltip}
                hidden={!action.tooltip}
                position='left'
              >
                <Menu.Item
                  aria-label={id}
                  leftSection={action.icon}
                  onClick={action.onClick}
                  disabled={action.disabled}
                >
                  {action.name}
                </Menu.Item>
              </Tooltip>
            </Indicator>
          );
        })}
      </Menu.Dropdown>
    </Menu>
  ) : null;
}

export function OptionsActionDropdown({
  actions = [],
  tooltip = t`Options`,
  hidden = false
}: Readonly<{
  actions: ActionDropdownItem[];
  tooltip?: string;
  hidden?: boolean;
}>) {
  return (
    <ActionDropdown
      icon={<IconDotsVertical />}
      tooltip={tooltip}
      actions={actions}
      hidden={hidden}
      noindicator
    />
  );
}
