/*
 * Enumeration of available API endpoints.
 *
 * In the cases where endpoints can be accessed with a primary key,
 * the primary key should be appended to the endpoint.
 * The exception to this is when the endpoint provides an :id parameter.
 */

export enum ApiEndpoints {
  api_server_info = '',

  // User API endpoints
  user_list = 'user/',
  user_me = 'user/me/',
  user_roles = 'user/roles/',
  user_token = 'user/token/',
  user_simple_login = 'email/generate/',
  user_reset = 'auth/password/reset/',
  user_reset_set = 'auth/password/reset/confirm/',
  user_sso = 'auth/social/',
  user_sso_remove = 'auth/social/:id/disconnect/',
  user_emails = 'auth/emails/',
  user_email_remove = 'auth/emails/:id/remove/',
  user_email_verify = 'auth/emails/:id/verify/',
  user_email_primary = 'auth/emails/:id/primary/',
  user_login = 'auth/login/',
  user_logout = 'auth/logout/',
  user_register = 'auth/registration/',

  // Generic API endpoints
  currency_list = 'currency/exchange/',
  currency_refresh = 'currency/refresh/',
  task_overview = 'background-task/',
  task_pending_list = 'background-task/pending/',
  task_scheduled_list = 'background-task/scheduled/',
  task_failed_list = 'background-task/failed/',
  api_search = 'search/',
  settings_global_list = 'settings/global/',
  settings_user_list = 'settings/user/',
  barcode = 'barcode/',
  news = 'news/',
  global_status = 'generic/status/',
  version = 'version/',
  license = 'license/',
  sso_providers = 'auth/providers/',
  group_list = 'user/group/',
  owner_list = 'user/owner/',

  // Notification endpoints
  notifications_list = 'notifications/',
  notifications_readall = 'notifications/readall/',

  // Build API endpoints
  build_order_list = 'build/',
  build_order_cancel = 'build/:id/cancel/',
  build_output_create = 'build/:id/create-output/',
  build_output_complete = 'build/:id/complete/',
  build_output_scrap = 'build/:id/scrap-outputs/',
  build_output_delete = 'build/:id/delete-outputs/',
  build_line_list = 'build/line/',

  bom_list = 'bom/',
  bom_item_validate = 'bom/:id/validate/',

  // Part API endpoints
  part_list = 'part/',
  part_parameter_list = 'part/parameter/',
  part_parameter_template_list = 'part/parameter/template/',
  part_thumbs_list = 'part/thumbs/',
  part_pricing_get = 'part/:id/pricing/',
  part_serial_numbers = 'part/:id/serial-numbers/',
  part_pricing_internal = 'part/internal-price/',
  part_pricing_sale = 'part/sale-price/',
  part_stocktake_list = 'part/stocktake/',
  category_list = 'part/category/',
  category_tree = 'part/category/tree/',
  category_parameter_list = 'part/category/parameters/',
  related_part_list = 'part/related/',
  part_test_template_list = 'part/test-template/',

  // Company API endpoints
  company_list = 'company/',
  contact_list = 'company/contact/',
  address_list = 'company/address/',
  supplier_part_list = 'company/part/',
  supplier_part_pricing_list = 'company/price-break/',
  manufacturer_part_list = 'company/part/manufacturer/',
  manufacturer_part_parameter_list = 'company/part/manufacturer/parameter/',

  // Stock API endpoints
  stock_item_list = 'stock/',
  stock_tracking_list = 'stock/track/',
  stock_location_list = 'stock/location/',
  stock_location_type_list = 'stock/location-type/',
  stock_location_tree = 'stock/location/tree/',
  stock_test_result_list = 'stock/test/',
  stock_transfer = 'stock/transfer/',
  stock_remove = 'stock/remove/',
  stock_add = 'stock/add/',
  stock_count = 'stock/count/',
  stock_change_status = 'stock/change_status/',
  stock_merge = 'stock/merge/',
  stock_assign = 'stock/assign/',
  stock_status = 'stock/status/',
  stock_install = 'stock/:id/install',

  // Generator API endpoints
  generate_batch_code = 'generate/batch-code/',
  generate_serial_number = 'generate/serial-number/',

  // Order API endpoints
  purchase_order_list = 'order/po/',
  purchase_order_line_list = 'order/po-line/',
  purchase_order_receive = 'order/po/:id/receive/',

  sales_order_list = 'order/so/',
  sales_order_line_list = 'order/so-line/',
  sales_order_shipment_list = 'order/so/shipment/',

  return_order_list = 'order/ro/',

  // Template API endpoints
  label_list = 'label/template/',
  label_print = 'label/print/',
  label_output = 'label/output/',
  report_list = 'report/template/',
  report_print = 'report/print/',
  report_output = 'report/output/',
  report_snippet = 'report/snippet/',
  report_asset = 'report/asset/',

  // Plugin API endpoints
  plugin_list = 'plugins/',
  plugin_setting_list = 'plugins/:plugin/settings/',
  plugin_registry_status = 'plugins/status/',
  plugin_install = 'plugins/install/',
  plugin_reload = 'plugins/reload/',
  plugin_activate = 'plugins/:key/activate/',
  plugin_uninstall = 'plugins/:key/uninstall/',

  // Machine API endpoints
  machine_types_list = 'machine/types/',
  machine_driver_list = 'machine/drivers/',
  machine_registry_status = 'machine/status/',
  machine_list = 'machine/',
  machine_restart = 'machine/:machine/restart/',
  machine_setting_list = 'machine/:machine/settings/',
  machine_setting_detail = 'machine/:machine/settings/:config_type/',

  // Miscellaneous API endpoints
  attachment_list = 'attachment/',
  error_report_list = 'error-report/',
  project_code_list = 'project-code/',
  custom_unit_list = 'units/',
  ui_preference = 'web/ui_preference/',
  notes_image_upload = 'notes-image-upload/'
}
