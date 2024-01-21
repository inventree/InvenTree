import { IconTools, IconWorldCode, IconX } from '@tabler/icons-react';
import {
  IconBinaryTree2,
  IconCopy,
  IconCornerUpRightDouble,
  IconCurrencyDollar,
  IconFlagFilled,
  IconGridDots,
  IconInfoCircleFilled,
  IconMapPinFilled,
  IconPackages,
  IconQuestionMark,
  IconShoppingCartFilled,
  IconTool,
  IconTruck,
  TablerIconsProps
} from '@tabler/icons-react';
import React from 'react';

const icons: { [key: string]: (props: TablerIconsProps) => React.JSX.Element } =
  {
    description: IconInfoCircleFilled,
    variant_of: IconBinaryTree2,
    unallocated_stock: IconPackages,
    total_in_stock: IconMapPinFilled,
    minimum_stock: IconFlagFilled,
    allocated_to_build_orders: IconTool,
    allocated_to_sales_orders: IconTruck,
    can_build: IconTools,
    ordering: IconShoppingCartFilled,
    building: IconTool,

    // Part Icons
    template: IconCopy,
    assembly: IconTool,
    component: IconGridDots,
    trackable: IconCornerUpRightDouble,
    purchaseable: IconShoppingCartFilled,
    saleable: IconCurrencyDollar,
    virtual: IconWorldCode,
    inactive: IconX
  };

/**
 * Returns a Tabler Icon for the model field name supplied
 * @param field string defining field name
 */
export function GetIcon(field: keyof typeof icons) {
  return icons[field];
}

type IconProps = {
  icon: keyof typeof icons;
  iconProps?: TablerIconsProps;
};

export function InvenTreeIcon(props: IconProps) {
  console.log('Proppies', props);
  const Icon = GetIcon(props.icon);

  return <Icon {...props.iconProps} />;
}
