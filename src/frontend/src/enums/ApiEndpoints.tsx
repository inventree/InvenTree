/*
 * Enumeration of available API endpoints.
 *
 * In the cases where endpoints can be accessed with a primary key,
 * the primary key should be appended to the endpoint.
 * The exception to this is when the endpoint provides an :id parameter.
 */

export enum ApiEndpoints {
  api_server_info = '',
  user_list = 'user/',
  user_me = 'user/me/',
  user_roles = 'user/roles/',
  user_token = 'user/token/',
  user_simple_login = 'email/generate/',
  user_reset = 'auth/password/reset/', // Note leading prefix here
  user_reset_set = 'auth/password/reset/confirm/', // Note leading prefix here
  user_sso = 'auth/social/',
  user_sso_remove = 'auth/social/:id/disconnect/',
  user_emails = 'auth/emails/',
  user_email_remove = 'auth/emails/:id/remove/',
  user_email_verify = 'auth/emails/:id/verify/',
  user_email_primary = 'auth/emails/:id/primary/',
  user_logout = 'auth/logout/',
  user_register = 'auth/registration/',
  currency_list = 'currency/exchange/',
  currency_refresh = 'currency/refresh/',
  task_overview = 'background-task/',
  task_pending_list = 'background-task/pending/',
  task_scheduled_list = 'background-task/scheduled/',
  task_failed_list = 'background-task/failed/',
  api_search = 'search/',
  settings_global_list = 'settings/global/',
  settings_user_list = 'settings/user/',
  notifications_list = 'notifications/',
  barcode = 'barcode/',
  news = 'news/',
  global_status = 'generic/status/',
  version = 'version/',
  sso_providers = 'auth/providers/',
  group_list = 'user/group/',
  owner_list = 'user/owner/',
  build_order_list = 'build/',
  build_order_attachment_list = 'build/attachment/',
  build_line_list = 'build/line/',
  bom_list = 'bom/',
  part_list = 'part/',
  part_parameter_list = 'part/parameter/',
  part_parameter_template_list = 'part/parameter/template/',
  category_list = 'part/category/',
  category_tree = 'part/category/tree/',
  related_part_list = 'part/related/',
  part_attachment_list = 'part/attachment/',
  part_test_template_list = 'part/test-template/',
  company_list = 'company/',
  contact_list = 'company/contact/',
  address_list = 'company/address/',
  company_attachment_list = 'company/attachment/',
  supplier_part_list = 'company/part/',
  manufacturer_part_list = 'company/part/manufacturer/',
  manufacturer_part_attachment_list = 'company/part/manufacturer/attachment/',
  manufacturer_part_parameter_list = 'company/part/manufacturer/parameter/',
  stock_item_list = 'stock/',
  stock_tracking_list = 'stock/track/',
  stock_location_list = 'stock/location/',
  stock_location_tree = 'stock/location/tree/',
  stock_attachment_list = 'stock/attachment/',
  purchase_order_list = 'order/po/',
  purchase_order_line_list = 'order/po-line/',
  purchase_order_attachment_list = 'order/po/attachment/',
  sales_order_list = 'order/so/',
  sales_order_attachment_list = 'order/so/attachment/',
  sales_order_shipment_list = 'order/so/shipment/',
  return_order_list = 'order/ro/',
  return_order_attachment_list = 'order/ro/attachment/',
  plugin_list = 'plugins/',
  plugin_setting_list = 'plugins/:plugin/settings/',
  plugin_registry_status = 'plugins/status/',
  plugin_install = 'plugins/install/',
  plugin_reload = 'plugins/reload/',
  error_report_list = 'error-report/',
  project_code_list = 'project-code/',
  custom_unit_list = 'units/'
}

export enum ApiPaths {
  api_server_info = 'api-server-info',

  api_search = 'api-search',

  // User information
  user_me = 'api-user-me',
  user_roles = 'api-user-roles',
  user_token = 'api-user-token',
  user_simple_login = 'api-user-simple-login',
  user_reset = 'api-user-reset',
  user_reset_set = 'api-user-reset-set',
  user_sso = 'api-user-sso',
  user_sso_remove = 'api-user-sso-remove',
  user_emails = 'api-user-emails',
  user_email_verify = 'api-user-email-verify',
  user_email_primary = 'api-user-email-primary',
  user_email_remove = 'api-user-email-remove',
  user_logout = 'api-user-logout',
  user_register = 'api-user-register',

  user_list = 'api-user-list',
  group_list = 'api-group-list',
  owner_list = 'api-owner-list',

  task_overview = 'api-task-overview',
  task_pending_list = 'api-task-pending-list',
  task_scheduled_list = 'api-task-scheduled-list',
  task_failed_list = 'api-task-failed-list',

  settings_global_list = 'api-settings-global-list',
  settings_user_list = 'api-settings-user-list',
  notifications_list = 'api-notifications-list',

  currency_list = 'api-currency-list',
  currency_refresh = 'api-currency-refresh',

  barcode = 'api-barcode',
  news = 'news',
  global_status = 'api-global-status',
  version = 'api-version',
  sso_providers = 'api-sso-providers',

  // Build order URLs
  build_order_list = 'api-build-list',
  build_order_attachment_list = 'api-build-attachment-list',
  build_line_list = 'api-build-line-list',

  // BOM URLs
  bom_list = 'api-bom-list',

  // Part URLs
  part_list = 'api-part-list',
  category_list = 'api-category-list',
  category_tree = 'api-category-tree',
  related_part_list = 'api-related-part-list',
  part_attachment_list = 'api-part-attachment-list',
  part_parameter_list = 'api-part-parameter-list',
  part_parameter_template_list = 'api-part-parameter-template-list',
  part_test_template_list = 'api-part-test-template-list',

  // Company URLs
  company_list = 'api-company-list',
  company_attachment_list = 'api-company-attachment-list',
  supplier_part_list = 'api-supplier-part-list',
  manufacturer_part_list = 'api-manufacturer-part-list',
  manufacturer_part_attachment_list = 'api-manufacturer-part-attachment-list',
  manufacturer_part_parameter_list = 'api-manufacturer-part-parameter-list',
  address_list = 'api-address-list',
  contact_list = 'api-contact-list',

  // Stock Item URLs
  stock_item_list = 'api-stock-item-list',
  stock_tracking_list = 'api-stock-tracking-list',
  stock_location_list = 'api-stock-location-list',
  stock_location_tree = 'api-stock-location-tree',
  stock_attachment_list = 'api-stock-attachment-list',

  // Purchase Order URLs
  purchase_order_list = 'api-purchase-order-list',
  purchase_order_line_list = 'api-purchase-order-line-list',
  purchase_order_attachment_list = 'api-purchase-order-attachment-list',

  // Sales Order URLs
  sales_order_list = 'api-sales-order-list',
  sales_order_attachment_list = 'api-sales-order-attachment-list',
  sales_order_shipment_list = 'api_sales_order_shipment_list',

  // Return Order URLs
  return_order_list = 'api-return-order-list',
  return_order_attachment_list = 'api-return-order-attachment-list',

  // Plugin URLs
  plugin_list = 'api-plugin-list',
  plugin_setting_list = 'api-plugin-settings',
  plugin_install = 'api-plugin-install',
  plugin_reload = 'api-plugin-reload',
  plugin_registry_status = 'api-plugin-registry-status',

  error_report_list = 'api-error-report-list',
  project_code_list = 'api-project-code-list',
  custom_unit_list = 'api-custom-unit-list'
}
