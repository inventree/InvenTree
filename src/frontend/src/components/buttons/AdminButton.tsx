import { t } from '@lingui/macro';
import { IconUserStar } from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';

import { ModelType } from '../../enums/ModelType';
import { useLocalState } from '../../states/LocalState';
import { useUserState } from '../../states/UserState';
import { ModelInformationDict } from '../render/ModelType';
import { ActionButton } from './ActionButton';

export type AdminButtonProps = {
  model: ModelType;
  pk: number | undefined;
};

/*
 * A button that is used to navigate to the admin page for the selected item.
 *
 * This button is only rendered if:
 * - The admin interface is enabled for the server
 * - The selected model has an associated admin URL
 * - The user has "superuser" role
 * - The user has at least read rights for the selected item
 */
export default function AdminButton(props: AdminButtonProps) {
  const user = useUserState();

  const enabled: boolean = useMemo(() => {
    // Only users with superuser permission will see this button
    if (!user || !user.isLoggedIn() || !user.isSuperuser()) {
      return false;
    }

    // TODO: Check if the server has the admin interface enabled

    const modelDef = ModelInformationDict[props.model];

    // No admin URL associated with the model
    if (!modelDef.admin_url) {
      return false;
    }

    // No primary key provided
    if (!props.pk) {
      return false;
    }

    return true;
  }, [user, props.model, props.pk]);

  const openAdmin = useCallback(
    (event: any) => {
      const modelDef = ModelInformationDict[props.model];
      const host = useLocalState.getState().host;

      if (!modelDef.admin_url) {
        return;
      }

      // TODO: Check the actual "admin" URL (it may be custom)
      const url = `${host}/admin${modelDef.admin_url}${props.pk}/`;

      if (event?.ctrlKey || event?.shiftKey) {
        // Open the link in a new tab
        window.open(url, '_blank');
      } else {
        window.open(url, '_self');
      }
    },
    [props.model, props.pk]
  );

  return (
    <ActionButton
      icon={<IconUserStar />}
      color="blue"
      size="lg"
      radius="sm"
      variant="filled"
      tooltip={t`Open in admin interface`}
      hidden={!enabled}
      onClick={openAdmin}
      tooltipAlignment="bottom"
    />
  );
}
