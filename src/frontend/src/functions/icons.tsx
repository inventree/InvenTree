import {
  IconBinaryTree2,
  IconFlagFilled,
  IconInfoCircleFilled,
  IconMapPinFilled,
  IconPackages,
  IconQuestionMark,
  IconTool,
  IconTruck
} from '@tabler/icons-react';
import React from 'react';

type description = 'description';
type variant = 'variant' | 'variant_of';

/**
 * Returns a Tabler Icon for the model field name supplied
 * @param field string defining field name
 */
export function GetIcon(field: string) {
  const icons: any = {
    description: <IconInfoCircleFilled />,
    variant: <IconBinaryTree2 />,
    unallocated_stock: <IconPackages />,
    total_in_stock: <IconMapPinFilled />,
    minimum_stock: <IconFlagFilled />,
    allocated_to_build_orders: <IconTool />,
    allocated_to_sales_orders: <IconTruck />,
    can_build: <IconTool />
  };

  return icons[field] ?? <IconQuestionMark />;
}
