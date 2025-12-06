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
  user_set_password = 'user/:id/set-password/',
  user_me = 'user/me/',
  user_profile = 'user/profile/',
  user_roles = 'user/roles/',
  user_token = 'user/token/',
  user_tokens = 'user/tokens/',
  user_simple_login = 'email/generate/',

  // User auth endpoints
  user_reset = 'auth/v1/auth/password/request',
  user_reset_set = 'auth/v1/auth/password/reset',
  auth_pwd_change = 'auth/v1/account/password/change',
  auth_login = 'auth/v1/auth/login',
  auth_login_2fa = 'auth/v1/auth/2fa/authenticate',
  auth_session = 'auth/v1/auth/session',
  auth_signup = 'auth/v1/auth/signup',
  auth_authenticators = 'auth/v1/account/authenticators',
  auth_recovery = 'auth/v1/account/authenticators/recovery-codes',
  auth_mfa_reauthenticate = 'auth/v1/auth/2fa/reauthenticate',
  auth_totp = 'auth/v1/account/authenticators/totp',
  auth_trust = 'auth/v1/auth/2fa/trust',
  auth_webauthn = 'auth/v1/account/authenticators/webauthn',
  auth_webauthn_login = 'auth/v1/auth/webauthn/authenticate',
  auth_reauthenticate = 'auth/v1/auth/reauthenticate',
  auth_email = 'auth/v1/account/email',
  auth_email_verify = 'auth/v1/auth/email/verify',
  auth_providers = 'auth/v1/account/providers',
  auth_provider_redirect = 'auth/v1/auth/provider/redirect',
  auth_config = 'auth/v1/config',

  // Generic API endpoints
  currency_list = 'currency/exchange/',
  currency_refresh = 'currency/refresh/',
  all_units = 'units/all/',
  task_overview = 'background-task/',
  task_pending_list = 'background-task/pending/',
  task_scheduled_list = 'background-task/scheduled/',
  task_failed_list = 'background-task/failed/',
  api_search = 'search/',
  settings_global_list = 'settings/global/',
  settings_user_list = 'settings/user/',
  news = 'news/',
  global_status = 'generic/status/',
  custom_state_list = 'generic/status/custom/',
  version = 'version/',
  license = 'license/',
  group_list = 'user/group/',
  owner_list = 'user/owner/',
  ruleset_list = 'user/ruleset/',
  content_type_list = 'contenttype/',
  icons = 'icons/',
  selectionlist_list = 'selection/',
  selectionlist_detail = 'selection/:id/',

  // Barcode API endpoints
  barcode = 'barcode/',
  barcode_history = 'barcode/history/',
  barcode_link = 'barcode/link/',
  barcode_unlink = 'barcode/unlink/',
  barcode_generate = 'barcode/generate/',

  // Data output endpoints
  data_output = 'data-output/',

  // Data import endpoints
  import_session_list = 'importer/session/',
  import_session_accept_fields = 'importer/session/:id/accept_fields/',
  import_session_accept_rows = 'importer/session/:id/accept_rows/',
  import_session_column_mapping_list = 'importer/column-mapping/',
  import_session_row_list = 'importer/row/',

  // Notification endpoints
  notifications_list = 'notifications/',
  notifications_readall = 'notifications/readall/',

  // Build API endpoints
  build_order_list = 'build/',
  build_order_issue = 'build/:id/issue/',
  build_order_cancel = 'build/:id/cancel/',
  build_order_hold = 'build/:id/hold/',
  build_order_complete = 'build/:id/finish/',
  build_output_complete = 'build/:id/complete/',
  build_output_create = 'build/:id/create-output/',
  build_output_scrap = 'build/:id/scrap-outputs/',
  build_output_delete = 'build/:id/delete-outputs/',
  build_order_auto_allocate = 'build/:id/auto-allocate/',
  build_order_allocate = 'build/:id/allocate/',
  build_order_consume = 'build/:id/consume/',
  build_order_deallocate = 'build/:id/unallocate/',

  build_line_list = 'build/line/',
  build_item_list = 'build/item/',

  bom_list = 'bom/',
  bom_item_validate = 'bom/:id/validate/',
  bom_validate = 'part/:id/bom-validate/',
  bom_substitute_list = 'bom/substitute/',

  // Part API endpoints
  part_list = 'part/',
  part_thumbs_list = 'part/thumbs/',
  part_pricing = 'part/:id/pricing/',
  part_requirements = 'part/:id/requirements/',
  part_serial_numbers = 'part/:id/serial-numbers/',
  part_scheduling = 'part/:id/scheduling/',
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

  // Stock location endpoints
  stock_location_list = 'stock/location/',
  stock_location_type_list = 'stock/location-type/',
  stock_location_tree = 'stock/location/tree/',

  // Stock item API endpoints
  stock_item_list = 'stock/',
  stock_tracking_list = 'stock/track/',
  stock_test_result_list = 'stock/test/',
  stock_transfer = 'stock/transfer/',
  stock_remove = 'stock/remove/',
  stock_return = 'stock/return/',
  stock_add = 'stock/add/',
  stock_count = 'stock/count/',
  stock_change_status = 'stock/change_status/',
  stock_merge = 'stock/merge/',
  stock_assign = 'stock/assign/',
  stock_status = 'stock/status/',
  stock_install = 'stock/:id/install/',
  stock_uninstall = 'stock/:id/uninstall/',
  stock_serialize = 'stock/:id/serialize/',
  stock_serial_info = 'stock/:id/serial-numbers/',

  // Generator API endpoints
  generate_batch_code = 'generate/batch-code/',
  generate_serial_number = 'generate/serial-number/',

  // Order API endpoints
  purchase_order_list = 'order/po/',
  purchase_order_issue = 'order/po/:id/issue/',
  purchase_order_hold = 'order/po/:id/hold/',
  purchase_order_cancel = 'order/po/:id/cancel/',
  purchase_order_complete = 'order/po/:id/complete/',
  purchase_order_line_list = 'order/po-line/',
  purchase_order_extra_line_list = 'order/po-extra-line/',
  purchase_order_receive = 'order/po/:id/receive/',

  sales_order_list = 'order/so/',
  sales_order_issue = 'order/so/:id/issue/',
  sales_order_hold = 'order/so/:id/hold/',
  sales_order_cancel = 'order/so/:id/cancel/',
  sales_order_ship = 'order/so/:id/ship/',
  sales_order_complete = 'order/so/:id/complete/',
  sales_order_allocate = 'order/so/:id/allocate/',
  sales_order_allocate_serials = 'order/so/:id/allocate-serials/',

  sales_order_line_list = 'order/so-line/',
  sales_order_extra_line_list = 'order/so-extra-line/',
  sales_order_allocation_list = 'order/so-allocation/',

  sales_order_shipment_list = 'order/so/shipment/',
  sales_order_shipment_complete = 'order/so/shipment/:id/ship/',

  return_order_list = 'order/ro/',
  return_order_issue = 'order/ro/:id/issue/',
  return_order_hold = 'order/ro/:id/hold/',
  return_order_cancel = 'order/ro/:id/cancel/',
  return_order_complete = 'order/ro/:id/complete/',
  return_order_receive = 'order/ro/:id/receive/',
  return_order_line_list = 'order/ro-line/',
  return_order_extra_line_list = 'order/ro-extra-line/',

  // Template API endpoints
  label_list = 'label/template/',
  label_print = 'label/print/',
  report_list = 'report/template/',
  report_print = 'report/print/',
  report_snippet = 'report/snippet/',
  report_asset = 'report/asset/',

  // Plugin API endpoints
  plugin_list = 'plugins/',
  plugin_setting_list = 'plugins/:plugin/settings/',
  plugin_user_setting_list = 'plugins/:plugin/user-settings/',
  plugin_registry_status = 'plugins/status/',
  plugin_install = 'plugins/install/',
  plugin_reload = 'plugins/reload/',
  plugin_activate = 'plugins/:key/activate/',
  plugin_uninstall = 'plugins/:key/uninstall/',
  plugin_admin = 'plugins/:key/admin/',

  // User interface plugin endpoints
  plugin_ui_features_list = 'plugins/ui/features/:feature_type/',

  // Special plugin endpoints
  plugin_locate_item = 'locate/',
  plugin_supplier_list = 'supplier/list/',
  plugin_supplier_search = 'supplier/search/',
  plugin_supplier_import = 'supplier/import/',

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
  notes_image_upload = 'notes-image-upload/',
  email_list = 'admin/email/',
  email_test = 'admin/email/test/',
  config_list = 'admin/config/',
  parameter_list = 'parameter/',
  parameter_template_list = 'parameter/template/'
}
