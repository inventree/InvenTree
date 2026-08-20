import { ActionButton } from '@lib/components/ActionButton';
import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { UserRoles } from '@lib/enums/Roles';
import type { UseInstanceResult } from '@lib/types/Rendering';
import { t } from '@lingui/core/macro';
import {
  ActionIcon,
  Alert,
  Group,
  HoverCard,
  Loader,
  type MantineColor,
  Stack,
  Text
} from '@mantine/core';
import {
  IconCircleCheck,
  IconExclamationCircle,
  IconGitCompare,
  IconListCheck
} from '@tabler/icons-react';
import { type ReactNode, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { RenderUser } from '../../../components/render/User';
import useBackgroundTask from '../../../hooks/UseBackgroundTask';
import { useApiFormModal } from '../../../hooks/UseForm';
import { useUserState } from '../../../states/UserState';
import { BomCompareDrawer } from './BomCompare';

/**
 * A hover-over component which displays information about the BOM validation for a given part
 */
export function BomActions({
  bomInformation,
  partInstance
}: Readonly<{
  bomInformation: UseInstanceResult;
  partInstance: any;
}>) {
  const user = useUserState();

  const [bomCompareOpen, setBomCompareOpen] = useState<boolean>(false);

  const [bomCompareId, setBomCompareId] = useState<string>('');

  const [searchParams, setSearchParams] = useSearchParams();

  // Open the BOM compare drawer if the URL contains the relevant query parameter
  useEffect(() => {
    if (
      searchParams.has('compare') &&
      !!searchParams.get('compare') &&
      !bomCompareOpen
    ) {
      setBomCompareId(searchParams.get('compare') as string);
      setBomCompareOpen(true);
    }
  }, [searchParams]);

  const [taskId, setTaskId] = useState<string>('');

  useBackgroundTask({
    taskId: taskId,
    message: t`Validating BOM`,
    successMessage: t`BOM validated`,
    onComplete: () => {
      bomInformation.instanceQuery.refetch();
    }
  });

  const validateBom = useApiFormModal({
    url: ApiEndpoints.bom_validate,
    method: 'PUT',
    fields: {
      valid: {
        hidden: true,
        value: true
      }
    },
    title: t`Validate BOM`,
    pk: partInstance.pk,
    preFormContent: (
      <Alert color='green' icon={<IconCircleCheck />} title={t`Validate BOM`}>
        <Text>{t`Do you want to validate the bill of materials for this assembly?`}</Text>
      </Alert>
    ),
    successMessage: null,
    onFormSuccess: (response: any) => {
      // If the process has been offloaded to a background task
      if (response.task_id) {
        setTaskId(response.task_id);
      } else {
        bomInformation.instanceQuery.refetch();
      }
    }
  });

  if (bomInformation.instanceQuery.isFetching) {
    return <Loader size='sm' />;
  }

  let icon: ReactNode;
  let color: MantineColor;
  let title = '';
  let description = '';

  if (bomInformation.instance?.bom_validated) {
    color = 'green';
    icon = <IconListCheck />;
    title = t`BOM Validated`;
    description = t`The Bill of Materials for this part has been validated`;
  } else if (bomInformation.instance?.bom_checked_date) {
    color = 'yellow';
    icon = <IconExclamationCircle />;
    title = t`BOM Not Validated`;
    description = t`The Bill of Materials for this part has previously been checked, but requires revalidation`;
  } else {
    color = 'red';
    icon = <IconExclamationCircle />;
    title = t`BOM Not Validated`;
    description = t`The Bill of Materials for this part has not yet been validated`;
  }

  return (
    <>
      {validateBom.modal}
      <Group gap='xs' justify='flex-end'>
        <ActionButton
          icon={<IconGitCompare />}
          color='blue'
          tooltip={t`Compare Bill of Materials`}
          onClick={() => setBomCompareOpen(true)}
        />
        {!bomInformation.instance?.bom_validated &&
          user.hasChangeRole(UserRoles.bom) && (
            <ActionButton
              icon={<IconCircleCheck />}
              color='green'
              tooltip={t`Validate BOM`}
              onClick={validateBom.open}
            />
          )}
        <HoverCard position='bottom-end'>
          <HoverCard.Target>
            <ActionIcon
              color={color}
              variant='transparent'
              aria-label='bom-validation-info'
            >
              {icon}
            </ActionIcon>
          </HoverCard.Target>
          <HoverCard.Dropdown>
            <Alert color={color} icon={icon} title={title}>
              <Stack gap='xs'>
                <Text size='sm'>{description}</Text>
                {bomInformation.instance?.bom_checked_date && (
                  <Text size='sm'>
                    {t`Validated On`}:{' '}
                    {bomInformation.instance.bom_checked_date}
                  </Text>
                )}
                {bomInformation.instance?.bom_checked_by_detail && (
                  <Group gap='xs'>
                    <Text size='sm'>{t`Validated By`}: </Text>
                    <RenderUser
                      instance={bomInformation.instance.bom_checked_by_detail}
                    />
                  </Group>
                )}
              </Stack>
            </Alert>
          </HoverCard.Dropdown>
        </HoverCard>
      </Group>
      <BomCompareDrawer
        partInstance={partInstance}
        compareId={bomCompareId}
        opened={bomCompareOpen}
        onClosed={() => {
          setBomCompareId('');
          setBomCompareOpen(false);
          setSearchParams((params: URLSearchParams) => {
            params.delete('compare');
            return params;
          });
        }}
      />
    </>
  );
}
