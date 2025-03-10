import { t } from '@lingui/macro';
import { showNotification } from '@mantine/notifications';
import { IconBell } from '@tabler/icons-react';
import { useApi } from '../../contexts/ApiContext';
import { ApiEndpoints } from '../../enums/ApiEndpoints';
import { apiUrl } from '../../states/ApiState';
import { ActionButton } from './ActionButton';

export default function StarredToggleButton({
  part,
  successFunction
}: Readonly<{ part: any; successFunction: () => void }>): JSX.Element {
  const api = useApi();

  function change(starred: boolean, partPk: number) {
    api
      .patch(apiUrl(ApiEndpoints.part_list, partPk), { starred: !starred })
      .then(() => {
        showNotification({
          title: 'Part Subscription',
          message: `Part subscription ${starred ? 'removed' : 'added'}`,
          autoClose: 5000,
          color: 'blue'
        });
        successFunction();
      });
  }

  return (
    <ActionButton
      icon={<IconBell />}
      color={part.starred ? 'green' : 'blue'}
      size='lg'
      variant={part.starred ? 'filled' : 'outline'}
      tooltip={t`Unsubscribe from part`}
      onClick={() => change(part.starred, part.pk)}
      tooltipAlignment='bottom'
    />
  );
}
