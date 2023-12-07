/*
 * Enumeration of available user role groups
 */
export enum UserRoles {
  admin = 'admin',
  build = 'build',
  part = 'part',
  part_category = 'part_category',
  purchase_order = 'purchase_order',
  return_order = 'return_order',
  sales_order = 'sales_order',
  stock = 'stock',
  stock_location = 'stocklocation',
  stocktake = 'stocktake'
}

/*
 * Enumeration of available user permissions within each role group
 */
export enum UserPermissions {
  view = 'view',
  add = 'add',
  change = 'change',
  delete = 'delete'
}
