import {
  Icon123,
  IconBinaryTree2,
  IconBookmarks,
  IconBox,
  IconBuilding,
  IconBuildingFactory2,
  IconBuildingStore,
  IconCalendar,
  IconCalendarStats,
  IconCategory,
  IconCheck,
  IconClipboardList,
  IconCopy,
  IconCornerUpRightDouble,
  IconCurrencyDollar,
  IconDotsCircleHorizontal,
  IconExternalLink,
  IconFileUpload,
  IconGitBranch,
  IconGridDots,
  IconHash,
  IconLayersLinked,
  IconLink,
  IconList,
  IconListTree,
  IconMail,
  IconMapPin,
  IconMapPinHeart,
  IconNotes,
  IconNumbers,
  IconPackage,
  IconPackageImport,
  IconPackages,
  IconPaperclip,
  IconPhone,
  IconPhoto,
  IconProgressCheck,
  IconQuestionMark,
  IconRulerMeasure,
  IconShoppingCart,
  IconShoppingCartHeart,
  IconSitemap,
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
  IconWorld,
  IconWorldCode,
  IconX
} from '@tabler/icons-react';
import { IconFlag } from '@tabler/icons-react';
import { IconTruckReturn } from '@tabler/icons-react';
import { IconInfoCircle } from '@tabler/icons-react';
import { IconCalendarTime } from '@tabler/icons-react';
import { TablerIconsProps } from '@tabler/icons-react';
import React from 'react';

const icons = {
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
  status: IconInfoCircle,
  info: IconInfoCircle,
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
  customers: IconBuildingStore,
  purchase_orders: IconShoppingCart,
  sales_orders: IconTruckDelivery,
  return_orders: IconTruckReturn,
  shipment: IconTruckDelivery,
  scheduling: IconCalendarStats,
  test_templates: IconTestPipe,
  related_parts: IconLayersLinked,
  attachments: IconPaperclip,
  notes: IconNotes,
  photo: IconPhoto,
  upload: IconFileUpload,
  reject: IconX,
  select_image: IconGridDots,
  delete: IconTrash,

  // Part Icons
  active: IconCheck,
  template: IconCopy,
  assembly: IconTool,
  component: IconGridDots,
  trackable: IconCornerUpRightDouble,
  purchaseable: IconShoppingCart,
  saleable: IconCurrencyDollar,
  virtual: IconWorldCode,
  inactive: IconX,
  part: IconBox,
  supplier_part: IconPackageImport,

  calendar: IconCalendar,
  external: IconExternalLink,
  creation_date: IconCalendarTime,
  location: IconMapPin,
  default_location: IconMapPinHeart,
  default_supplier: IconShoppingCartHeart,
  link: IconLink,
  responsible: IconUserStar,
  pricing: IconCurrencyDollar,
  currency: IconCurrencyDollar,
  stocktake: IconClipboardList,
  user: IconUser,
  group: IconUsersGroup,
  check: IconCheck,
  copy: IconCopy,
  quantity: IconNumbers,
  progress: IconProgressCheck,
  reference: IconHash,
  website: IconWorld,
  email: IconMail,
  phone: IconPhone,
  sitemap: IconSitemap
};

export type InvenTreeIconType = keyof typeof icons;

/**
 * Returns a Tabler Icon for the model field name supplied
 * @param field string defining field name
 */
export function GetIcon(field: InvenTreeIconType) {
  return icons[field];
}

type IconProps = {
  icon: InvenTreeIconType;
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
function IconShapes(props: TablerIconsProps): Element {
  throw new Error('Function not implemented.');
}
