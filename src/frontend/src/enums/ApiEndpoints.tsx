/*
 * Enumeration of available API endpoints.
 */
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

  user_list = 'api-user-list',
  group_list = 'api-group-list',
  owner_list = 'api-owner-list',

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
  part_thumbs_list = 'api-part-thumbs',

  // Company URLs
  company_list = 'api-company-list',
  company_attachment_list = 'api-company-attachment-list',
  supplier_part_list = 'api-supplier-part-list',
  manufacturer_part_list = 'api-manufacturer-part-list',
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
