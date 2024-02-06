import {
  Icon123,
  IconBinaryTree2,
  IconBookmarks,
  IconBuilding,
  IconBuildingFactory2,
  IconCalendarStats,
  IconCheck,
  IconClipboardList,
  IconCopy,
  IconCornerUpRightDouble,
  IconCurrencyDollar,
  IconExternalLink,
  IconFileDownload,
  IconFileUpload,
  IconGitBranch,
  IconGridDots,
  IconLayersLinked,
  IconLink,
  IconList,
  IconListTree,
  IconMapPinHeart,
  IconNotes,
  IconPackage,
  IconPackages,
  IconPaperclip,
  IconPhoto,
  IconQuestionMark,
  IconRulerMeasure,
  IconShoppingCart,
  IconShoppingCartHeart,
  IconStack2,
  IconStatusChange,
  IconTag,
  IconTestPipe,
  IconTool,
  IconTools,
  IconTrash,
  IconTruck,
  IconTruckDelivery,
  IconUser,
  IconUserStar,
  IconUsersGroup,
  IconVersions,
  IconWorldCode,
  IconX
} from '@tabler/icons-react';
import { IconFlag } from '@tabler/icons-react';
import { IconInfoCircle } from '@tabler/icons-react';
import { IconCalendarTime } from '@tabler/icons-react';
import { TablerIconsProps } from '@tabler/icons-react';
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
    details: IconInfoCircle,
    parameters: IconList,
    stock: IconPackages,
    variants: IconVersions,
    allocations: IconBookmarks,
    bom: IconListTree,
    builds: IconTools,
    used_in: IconStack2,
    manufacturers: IconBuildingFactory2,
    suppliers: IconBuilding,
    purchase_orders: IconShoppingCart,
    sales_orders: IconTruckDelivery,
    scheduling: IconCalendarStats,
    test_templates: IconTestPipe,
    related_parts: IconLayersLinked,
    attachments: IconPaperclip,
    notes: IconNotes,
    photo: IconPhoto,
    upload: IconFileUpload,
    download: IconFileDownload,
    reject: IconX,
    select_image: IconGridDots,
    delete: IconTrash,

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
    stocktake: IconClipboardList,
    user: IconUser,
    group: IconUsersGroup,
    check: IconCheck,
    copy: IconCopy
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
