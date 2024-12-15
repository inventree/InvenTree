import { t } from '@lingui/macro';
import { IconUserStar } from '@tabler/icons-react';
import { useCallback, useMemo } from 'react';

import type { ModelType } from '../../enums/ModelType';
import { generateUrl } from '../../functions/urls';
import { useServerApiState } from '../../states/ApiState';
import { useUserState } from '../../states/UserState';
import { ModelInformationDict } from '../render/ModelType';
import { ActionButton } from './ActionButton';

export type AdminButtonProps = {
  model: ModelType;
  id: number | undefined;
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
export default function AdminButton(props: Readonly<AdminButtonProps>) {
  const user = useUserState();
  const server = useServerApiState();

  const enabled: boolean = useMemo(() => {
    // Only users with superuser permission will see this button
    if (!user || !user.isLoggedIn() || !user.isSuperuser()) {
      return false;
    }

    const modelDef = ModelInformationDict[props.model];

    // Check if the server has the admin interface enabled
    if (!server.server.django_admin) {
      return false;
    }

    // No admin URL associated with the model
    if (!modelDef.admin_url) {
      return false;
    }

    // No primary key provided
    if (!props.id) {
      return false;
    }

    return true;
  }, [user, props.model, props.id]);

  const openAdmin = useCallback(
    (event: any) => {
      const modelDef = ModelInformationDict[props.model];

      if (!modelDef.admin_url) {
        return;
      }

      // Generate the URL for the admin interface
      const url = generateUrl(
        `${server.server.django_admin}${modelDef.admin_url}${props.id}/`
      );

      if (event?.ctrlKey || event?.shiftKey) {
        // Open the link in a new tab
        window.open(url, '_blank');
      } else {
        window.open(url, '_self');
      }
    },
    [props.model, props.id]
  );

  return (
    <ActionButton
      icon={<IconUserStar />}
      color='blue'
      size='lg'
      variant='filled'
      tooltip={t`Open in admin interface`}
      hidden={!enabled}
      onClick={openAdmin}
      tooltipAlignment='bottom'
    />
  );
}
