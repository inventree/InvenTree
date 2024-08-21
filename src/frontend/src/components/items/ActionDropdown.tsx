import { t } from '@lingui/macro';
import {
  ActionIcon,
  Indicator,
  IndicatorProps,
  Menu,
  Tooltip
} from '@mantine/core';
import { modals } from '@mantine/modals';
import {
  IconCopy,
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
  hidden = false
}: {
  icon: ReactNode;
  tooltip: string;
  actions: ActionDropdownItem[];
  disabled?: boolean;
  hidden?: boolean;
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
          <Tooltip label={tooltip} hidden={!tooltip}>
            <ActionIcon
              size="lg"
              radius="sm"
              variant="transparent"
              disabled={disabled}
              aria-label={menuName}
            >
              {icon}
            </ActionIcon>
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

// Dropdown menu for barcode actions
export function BarcodeActionDropdown({
  actions
}: {
  actions: ActionDropdownItem[];
}) {
  return (
    <ActionDropdown
      tooltip={t`Barcode Actions`}
      icon={<IconQrcode />}
      actions={actions}
    />
  );
}

export function BarcodeActionDropdown2({
  current_barcode = null,
  model,
  pk
}: Readonly<{
  current_barcode: boolean | null;
  model: ModelType;
  pk: number;
}>) {
  const hidden = current_barcode === null;
  const actions = [
    ViewBarcodeAction({
      model: model,
      pk: pk
    }),
    LinkBarcodeAction({
      hidden: hidden || current_barcode,
      model: model,
      pk: pk
    }),
    UnlinkBarcodeAction({
      hidden: hidden || !current_barcode,
      model: model,
      pk: pk
    })
  ];
  return <BarcodeActionDropdown actions={actions} />;
}

// Common action button for viewing a barcode
export function ViewBarcodeAction({
  hidden = false,
  model,
  pk
}: {
  hidden?: boolean;
  model: ModelType;
  pk: number;
}): ActionDropdownItem {
  const onClick = () => {
    modals.open({
      title: t`View Barcode`,
      children: <InvenTreeQRCode model={model} pk={pk} />
    });
  };

  return {
    icon: <IconQrcode />,
    name: t`View`,
    tooltip: t`View barcode`,
    onClick: onClick,
    hidden: hidden
  };
}

function GeneralBarcodeAction({
  hidden = false,
  model,
  pk,
  title,
  icon,
  tooltip,
  ChildItem
}: {
  hidden?: boolean;
  model: ModelType;
  pk: number;
  title: string;
  icon: ReactNode;
  tooltip: string;
  ChildItem: any;
}): ActionDropdownItem {
  const onClick = () => {
    modals.open({
      title: title,
      children: <ChildItem model={model} pk={pk} />
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

// Common action button for linking a custom barcode
export function LinkBarcodeAction({
  hidden = false,
  model,
  pk
}: {
  hidden?: boolean;
  model: ModelType;
  pk: number;
}): ActionDropdownItem {
  return GeneralBarcodeAction({
    hidden: hidden,
    model: model,
    pk: pk,
    title: t`Link Barcode`,
    icon: <IconLink />,
    tooltip: t`Link a custom barcode to this item`,
    ChildItem: QRCodeLink
  });
}

// Common action button for un-linking a custom barcode
export function UnlinkBarcodeAction({
  hidden = false,
  model,
  pk
}: {
  hidden?: boolean;
  model: ModelType;
  pk: number;
}): ActionDropdownItem {
  return GeneralBarcodeAction({
    hidden: hidden,
    model: model,
    pk: pk,
    title: t`Unlink Barcode`,
    icon: <IconUnlink />,
    tooltip: t`Unlink custom barcode`,
    ChildItem: QRCodeUnlink
  });
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
