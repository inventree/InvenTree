import {
  Icon123,
  IconExternalLink,
  IconGitBranch,
  IconLink,
  IconMapPinHeart,
  IconPackage,
  IconRulerMeasure,
  IconShoppingCart,
  IconShoppingCartHeart,
  IconStack3,
  IconStatusChange,
  IconTag,
  IconTools,
  IconUserStar,
  IconWorldCode,
  IconX
} from '@tabler/icons-react';
import { IconFlag } from '@tabler/icons-react';
import { IconInfoCircle } from '@tabler/icons-react';
import { IconCalendarTime } from '@tabler/icons-react';
import {
  IconBinaryTree2,
  IconCopy,
  IconCornerUpRightDouble,
  IconCurrencyDollar,
  IconGridDots,
  IconPackages,
  IconQuestionMark,
  IconTool,
  IconTruck,
  TablerIconsProps
} from '@tabler/icons-react';
import React from 'react';

const icons: { [key: string]: (props: TablerIconsProps) => React.JSX.Element } =
  {
    description: IconInfoCircle,
    variant_of: IconStatusChange,
    unallocated_stock: IconPackage,
    total_in_stock: IconPackages,
    minimum_stock: IconFlag,
    allocated_to_build_orders: IconTool,
    allocated_to_sales_orders: IconTruck,
    can_build: IconTools,
    ordering: IconShoppingCart,
    building: IconTool,
    category: IconBinaryTree2,
    IPN: Icon123,
    revision: IconGitBranch,
    units: IconRulerMeasure,
    keywords: IconTag,

    // Part Icons
    template: IconCopy,
    assembly: IconTool,
    component: IconGridDots,
    trackable: IconCornerUpRightDouble,
    purchaseable: IconShoppingCart,
    saleable: IconCurrencyDollar,
    virtual: IconWorldCode,
    inactive: IconX,

    external: IconExternalLink,
    creation_date: IconCalendarTime,
    default_location: IconMapPinHeart,
    default_supplier: IconShoppingCartHeart,
    link: IconLink,
    responsible: IconUserStar,
    pricing: IconCurrencyDollar,
    stocktake: IconStack3
  };

/**
 * Returns a Tabler Icon for the model field name supplied
 * @param field string defining field name
 */
export function GetIcon(field: keyof typeof icons) {
  return icons[field];
}

type IconProps = {
  icon: string;
  iconProps?: TablerIconsProps;
};

export function InvenTreeIcon(props: IconProps) {
  let Icon: (props: TablerIconsProps) => React.JSX.Element;

  if (props.icon in icons) {
    Icon = GetIcon(props.icon);
  } else {
    Icon = IconQuestionMark;
  }

  return <Icon {...props.iconProps} />;
}
