import { t } from '@lingui/macro';
import {
  Button,
  Indicator,
  IndicatorProps,
  Menu,
  Tooltip
} from '@mantine/core';
import { modals } from '@mantine/modals';
import {
  IconChevronDown,
  IconCopy,
  IconDotsVertical,
  IconEdit,
  IconLink,
  IconQrcode,
  IconTrash,
  IconUnlink
} from '@tabler/icons-react';
import { ReactNode, useMemo } from 'react';

import { ModelType } from '../../enums/ModelType';
import { identifierString } from '../../functions/conversion';
import { InvenTreeIcon } from '../../functions/icons';
import { InvenTreeQRCode, QRCodeLink, QRCodeUnlink } from './QRCode';

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
  actions,
  disabled = false,
  hidden = false,
  noindicator = false
}: {
  icon: ReactNode;
  tooltip: string;
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
    <Menu position="bottom-end" key={menuName}>
      <Indicator disabled={!indicatorProps} {...indicatorProps?.indicator}>
        <Menu.Target>
          <Tooltip label={tooltip} hidden={!tooltip} position="bottom">
            <Button
              radius="sm"
              variant={noindicator ? 'transparent' : 'light'}
              disabled={disabled}
              aria-label={menuName}
              p="0"
              size="sm"
              rightSection={
                noindicator || disabled ? null : (
                  <IconChevronDown stroke={1.5} />
                )
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
                position="left"
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
}: {
  actions: ActionDropdownItem[];
  tooltip?: string;
  hidden?: boolean;
}) {
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

// Dropdown menu for barcode actions
export function BarcodeActionDropdown({
  model,
  pk,
  hash = null,
  actions = [],
  perm: permission = true
}: Readonly<{
  model: ModelType;
  pk: number;
  hash?: boolean | null;
  actions?: ActionDropdownItem[];
  perm?: boolean;
}>) {
  const hidden = hash === null;
  const prop = { model, pk, hash };
  return (
    <ActionDropdown
      tooltip={t`Barcode Actions`}
      icon={<IconQrcode />}
      actions={[
        GeneralBarcodeAction({
          mdl_prop: prop,
          title: t`View`,
          icon: <IconQrcode />,
          tooltip: t`View barcode`,
          ChildItem: InvenTreeQRCode
        }),
        GeneralBarcodeAction({
          hidden: hidden || hash || !permission,
          mdl_prop: prop,
          title: t`Link Barcode`,
          icon: <IconLink />,
          tooltip: t`Link a custom barcode to this item`,
          ChildItem: QRCodeLink
        }),
        GeneralBarcodeAction({
          hidden: hidden || !hash || !permission,
          mdl_prop: prop,
          title: t`Unlink Barcode`,
          icon: <IconUnlink />,
          tooltip: t`Unlink custom barcode`,
          ChildItem: QRCodeUnlink
        }),
        ...actions
      ]}
    />
  );
}

export type QrCodeType = {
  model: ModelType;
  pk: number;
  hash?: boolean | null;
};

function GeneralBarcodeAction({
  hidden = false,
  mdl_prop,
  title,
  icon,
  tooltip,
  ChildItem
}: {
  hidden?: boolean;
  mdl_prop: QrCodeType;
  title: string;
  icon: ReactNode;
  tooltip: string;
  ChildItem: any;
}): ActionDropdownItem {
  const onClick = () => {
    modals.open({
      title: title,
      children: <ChildItem mdl_prop={mdl_prop} />
    });
  };

  return {
    icon: icon,
    name: title,
    tooltip: tooltip,
    onClick: onClick,
    hidden: hidden
  };
}

// Common action button for editing an item
export function EditItemAction(props: ActionDropdownItem): ActionDropdownItem {
  return {
    ...props,
    icon: <IconEdit color="blue" />,
    name: t`Edit`,
    tooltip: props.tooltip ?? t`Edit item`
  };
}

// Common action button for deleting an item
export function DeleteItemAction(
  props: ActionDropdownItem
): ActionDropdownItem {
  return {
    ...props,
    icon: <IconTrash color="red" />,
    name: t`Delete`,
    tooltip: props.tooltip ?? t`Delete item`
  };
}

export function HoldItemAction(props: ActionDropdownItem): ActionDropdownItem {
  return {
    ...props,
    icon: <InvenTreeIcon icon="hold" iconProps={{ color: 'orange' }} />,
    name: t`Hold`,
    tooltip: props.tooltip ?? t`Hold`
  };
}

export function CancelItemAction(
  props: ActionDropdownItem
): ActionDropdownItem {
  return {
    ...props,
    icon: <InvenTreeIcon icon="cancel" iconProps={{ color: 'red' }} />,
    name: t`Cancel`,
    tooltip: props.tooltip ?? t`Cancel`
  };
}

// Common action button for duplicating an item
export function DuplicateItemAction(
  props: ActionDropdownItem
): ActionDropdownItem {
  return {
    ...props,
    icon: <IconCopy color="green" />,
    name: t`Duplicate`,
    tooltip: props.tooltip ?? t`Duplicate item`
  };
}
