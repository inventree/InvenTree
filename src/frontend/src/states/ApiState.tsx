import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';

import { api } from '../App';
import { StatusCodeListInterface } from '../components/render/StatusRenderer';
import { statusCodeList } from '../defaults/backendMappings';
import { emptyServerAPI } from '../defaults/defaults';
import { ApiPaths } from '../enums/ApiEndpoints';
import { ModelType } from '../enums/ModelType';
import { AuthProps, ServerAPIProps } from './states';

type StatusLookup = Record<ModelType | string, StatusCodeListInterface>;

interface ServerApiStateProps {
  server: ServerAPIProps;
  setServer: (newServer: ServerAPIProps) => void;
  fetchServerApiState: () => void;
  status?: StatusLookup;
  auth_settings?: AuthProps;
}

export const useServerApiState = create<ServerApiStateProps>()(
  persist(
    (set) => ({
      server: emptyServerAPI,
      setServer: (newServer: ServerAPIProps) => set({ server: newServer }),
      fetchServerApiState: async () => {
        // Fetch server data
        await api
          .get(apiUrl(ApiPaths.api_server_info))
          .then((response) => {
            set({ server: response.data });
          })
          .catch(() => {});
        // Fetch status data for rendering labels
        await api
          .get(apiUrl(ApiPaths.global_status))
          .then((response) => {
            const newStatusLookup: StatusLookup = {} as StatusLookup;
            for (const key in response.data) {
              newStatusLookup[statusCodeList[key] || key] =
                response.data[key].values;
            }
            set({ status: newStatusLookup });
          })
          .catch(() => {});

        // Fetch login/SSO behaviour
        await api
          .get(apiUrl(ApiPaths.sso_providers), {
            headers: { Authorization: '' }
          })
          .then((response) => {
            set({ auth_settings: response.data });
          })
          .catch(() => {});
      },
      status: undefined
    }),
    {
      name: 'server-api-state',
      storage: createJSONStorage(() => sessionStorage)
    }
  )
);

/**
 * Function to return the API prefix.
 * For now it is fixed, but may be configurable in the future.
 */
export function apiPrefix(): string {
  return '/api/';
}

/**
 * Return the endpoint associated with a given API path
 */
export function apiEndpoint(path: ApiPaths): string {
  switch (path) {
    case ApiPaths.api_server_info:
      return '';
    case ApiPaths.user_list:
      return 'user/';
    case ApiPaths.owner_list:
      return 'user/owner/';
    case ApiPaths.user_me:
      return 'user/me/';
    case ApiPaths.user_roles:
      return 'user/roles/';
    case ApiPaths.user_token:
      return 'user/token/';
    case ApiPaths.user_simple_login:
      return 'email/generate/';
    case ApiPaths.user_reset:
      // Note leading prefix here
      return 'auth/password/reset/';
    case ApiPaths.user_reset_set:
      // Note leading prefix here
      return 'auth/password/reset/confirm/';
    case ApiPaths.user_sso:
      return 'auth/social/';
    case ApiPaths.user_sso_remove:
      return 'auth/social/:id/disconnect/';
    case ApiPaths.user_emails:
      return 'auth/emails/';
    case ApiPaths.user_email_remove:
      return 'auth/emails/:id/remove/';
    case ApiPaths.user_email_verify:
      return 'auth/emails/:id/verify/';
    case ApiPaths.user_email_primary:
      return 'auth/emails/:id/primary/';
    case ApiPaths.user_logout:
      return 'auth/logout/';
    case ApiPaths.user_register:
      return 'auth/registration/';
    case ApiPaths.currency_list:
      return 'currency/exchange/';
    case ApiPaths.currency_refresh:
      return 'currency/refresh/';
    case ApiPaths.task_overview:
      return 'background-task/';
    case ApiPaths.task_pending_list:
      return 'background-task/pending/';
    case ApiPaths.task_scheduled_list:
      return 'background-task/scheduled/';
    case ApiPaths.task_failed_list:
      return 'background-task/failed/';
    case ApiPaths.api_search:
      return 'search/';
    case ApiPaths.settings_global_list:
      return 'settings/global/';
    case ApiPaths.settings_user_list:
      return 'settings/user/';
    case ApiPaths.notifications_list:
      return 'notifications/';
    case ApiPaths.barcode:
      return 'barcode/';
    case ApiPaths.news:
      return 'news/';
    case ApiPaths.global_status:
      return 'generic/status/';
    case ApiPaths.version:
      return 'version/';
    case ApiPaths.sso_providers:
      return 'auth/providers/';
    case ApiPaths.group_list:
      return 'user/group/';
    case ApiPaths.owner_list:
      return 'user/owner/';
    case ApiPaths.build_order_list:
      return 'build/';
    case ApiPaths.build_order_attachment_list:
      return 'build/attachment/';
    case ApiPaths.build_line_list:
      return 'build/line/';
    case ApiPaths.bom_list:
      return 'bom/';
    case ApiPaths.part_list:
      return 'part/';
    case ApiPaths.part_parameter_list:
      return 'part/parameter/';
    case ApiPaths.part_parameter_template_list:
      return 'part/parameter/template/';
    case ApiPaths.category_list:
      return 'part/category/';
    case ApiPaths.category_tree:
      return 'part/category/tree/';
    case ApiPaths.related_part_list:
      return 'part/related/';
    case ApiPaths.part_attachment_list:
      return 'part/attachment/';
    case ApiPaths.part_test_template_list:
      return 'part/test-template/';
    case ApiPaths.company_list:
      return 'company/';
    case ApiPaths.contact_list:
      return 'company/contact/';
    case ApiPaths.address_list:
      return 'company/address/';
    case ApiPaths.company_attachment_list:
      return 'company/attachment/';
    case ApiPaths.supplier_part_list:
      return 'company/part/';
    case ApiPaths.manufacturer_part_list:
      return 'company/part/manufacturer/';
    case ApiPaths.manufacturer_part_attachment_list:
      return 'company/part/manufacturer/attachment/';
    case ApiPaths.stock_item_list:
      return 'stock/';
    case ApiPaths.stock_tracking_list:
      return 'stock/track/';
    case ApiPaths.stock_location_list:
      return 'stock/location/';
    case ApiPaths.stock_location_tree:
      return 'stock/location/tree/';
    case ApiPaths.stock_attachment_list:
      return 'stock/attachment/';
    case ApiPaths.purchase_order_list:
      return 'order/po/';
    case ApiPaths.purchase_order_line_list:
      return 'order/po-line/';
    case ApiPaths.purchase_order_attachment_list:
      return 'order/po/attachment/';
    case ApiPaths.sales_order_list:
      return 'order/so/';
    case ApiPaths.sales_order_attachment_list:
      return 'order/so/attachment/';
    case ApiPaths.sales_order_shipment_list:
      return 'order/so/shipment/';
    case ApiPaths.return_order_list:
      return 'order/ro/';
    case ApiPaths.return_order_attachment_list:
      return 'order/ro/attachment/';
    case ApiPaths.plugin_list:
      return 'plugins/';
    case ApiPaths.plugin_setting_list:
      return 'plugins/:plugin/settings/';
    case ApiPaths.plugin_registry_status:
      return 'plugins/status/';
    case ApiPaths.plugin_install:
      return 'plugins/install/';
    case ApiPaths.plugin_reload:
      return 'plugins/reload/';
    case ApiPaths.error_report_list:
      return 'error-report/';
    case ApiPaths.project_code_list:
      return 'project-code/';
    case ApiPaths.custom_unit_list:
      return 'units/';
    default:
      return '';
  }
}

export type PathParams = Record<string, string | number>;

/**
 * Construct an API URL with an endpoint and (optional) pk value
 */
export function apiUrl(
  path: ApiPaths | string,
  pk?: any,
  pathParams?: PathParams
): string {
  let _url = path;
  if (Object.values(ApiPaths).includes(path as ApiPaths)) {
    _url = apiEndpoint(path as ApiPaths);
  }

  // If the URL does not start with a '/', add the API prefix
  if (!_url.startsWith('/')) {
    _url = apiPrefix() + _url;
  }

  if (_url && pk) {
    _url += `${pk}/`;
  }

  if (_url && pathParams) {
    for (const key in pathParams) {
      _url = _url.replace(`:${key}`, `${pathParams[key]}`);
    }
  }

  return _url;
}
