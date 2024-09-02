import { MantineTheme } from '@mantine/core';
import { AxiosInstance } from 'axios';
import { NavigateFunction } from 'react-router-dom';

import { ModelType } from '../../enums/ModelType';
import { UserStateProps } from '../../states/UserState';

/*
 * A set of properties which are passed to a plugin,
 * for rendering an element in the user interface.
 *
 * @param model - The model type for the plugin (e.g. 'part' / 'purchaseorder')
 * @param id - The ID (primary key) of the model instance for the plugin
 * @param instance - The model instance data (if available)
 * @param api - The Axios API instance (see ../states/ApiState.tsx)
 * @param user - The current user instance (see ../states/UserState.tsx)
 * @param navigate - The navigation function (see react-router-dom)
 * @param theme - The current Mantine theme
 */
export type PluginContext = {
  model?: ModelType | string;
  id?: string | number | null;
  instance?: any;
  api: AxiosInstance;
  user: UserStateProps;
  host: string;
  navigate: NavigateFunction;
  theme: MantineTheme;
};
