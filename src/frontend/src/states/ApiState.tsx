import { create } from 'zustand';

import { api } from '../App';
import { emptyServerAPI } from '../defaults/defaults';
import { ServerAPIProps, UserProps } from './states';

interface ApiStateProps {
  user: UserProps | undefined;
  setUser: (newUser: UserProps) => void;
  fetchApiState: () => void;
}

export const useApiState = create<ApiStateProps>((set, get) => ({
  user: undefined,
  setUser: (newUser: UserProps) => set({ user: newUser }),
  fetchApiState: async () => {
    // Fetch user data
    await api.get(url(ApiPaths.user_me)).then((response) => {
      const user: UserProps = {
        name: `${response.data.first_name} ${response.data.last_name}`,
        email: response.data.email,
        username: response.data.username
      };
      set({ user: user });
    });
  }
}));

interface ServerApiStateProps {
  server: ServerAPIProps;
  setServer: (newServer: ServerAPIProps) => void;
  fetchServerApiState: () => void;
}

export const useServerApiState = create<ServerApiStateProps>((set, get) => ({
  server: emptyServerAPI,
  setServer: (newServer: ServerAPIProps) => set({ server: newServer }),
  fetchServerApiState: async () => {
    // Fetch server data
    await api.get('/').then((response) => {
      set({ server: response.data });
    });
  }
}));

export enum ApiPaths {
  user_me = 'api-user-me',
  user_token = 'api-user-token',
  user_simple_login = 'api-user-simple-login',
  user_reset = 'api-user-reset',
  user_reset_set = 'api-user-reset-set',

  barcode = 'api-barcode',
  part_detail = 'api-part-detail',
  supplier_part_detail = 'api-supplier-part-detail',
  stock_item_detail = 'api-stock-item-detail',
  stock_location_detail = 'api-stock-location-detail',
  purchase_order_detail = 'api-purchase-order-detail',
  sales_order_detail = 'api-sales-order-detail',
  build_order_detail = 'api-build-order-detail'
}

export function url(path: ApiPaths, pk?: any): string {
  switch (path) {
    case ApiPaths.user_me:
      return 'user/me/';
    case ApiPaths.user_token:
      return 'user/token/';
    case ApiPaths.user_simple_login:
      return 'email/generate/';
    case ApiPaths.user_reset:
      return '/auth/password/reset/';
    case ApiPaths.user_reset_set:
      return '/auth/password/reset/confirm/';

    case ApiPaths.barcode:
      return 'barcode/';
    case ApiPaths.part_detail:
      return `part/${pk}/`;
    case ApiPaths.supplier_part_detail:
      return `company/part/${pk}/`;
    case ApiPaths.stock_item_detail:
      return `stock/${pk}/`;
    case ApiPaths.stock_location_detail:
      return `stock/location/${pk}/`;
    case ApiPaths.purchase_order_detail:
      return `order/po/${pk}/`;
    case ApiPaths.sales_order_detail:
      return `order/so/${pk}/`;
    case ApiPaths.build_order_detail:
      return `build/${pk}/`;

    default:
      return '';
  }
}
