import { t } from '@lingui/core/macro';
import {
  Alert,
  Button,
  Divider,
  Drawer,
  Group,
  Paper,
  Space,
  Stack,
  Stepper
} from '@mantine/core';
import { IconCheck, IconExclamationCircle } from '@tabler/icons-react';
import { type ReactNode, useMemo } from 'react';

import { ModelType } from '@lib/enums/ModelType';
import { useImportSession } from '../../hooks/UseImportSession';
import useStatusCodes from '../../hooks/UseStatusCodes';
import { StylishText } from '../items/StylishText';
import ImporterDataSelector from './ImportDataSelector';
import ImporterColumnSelector from './ImporterColumnSelector';
import ImporterStatus from './ImporterStatus';

/*
 * Stepper component showing the current step of the data import process.
 */
function ImportDrawerStepper({
  currentStep
}: Readonly<{ currentStep: number }>) {
  /* TODO: Enhance this with:
   * - Custom icons
   * - Loading indicators for "background" states
   */

  return (
    <Stepper
      active={currentStep}
      onStepClick={undefined}
      allowNextStepsSelect={false}
      iconSize={20}
      size='xs'
    >
      <Stepper.Step label={t`Upload File`} />
      <Stepper.Step label={t`Map Columns`} />
      <Stepper.Step label={t`Import Rows`} />
      <Stepper.Step label={t`Process Data`} />
      <Stepper.Step label={t`Complete Import`} />
    </Stepper>
  );
}

export default function ImporterDrawer({
  sessionId,
  opened,
  onClose
}: Readonly<{
  sessionId: number;
  opened: boolean;
  onClose: () => void;
}>) {
  const session = useImportSession({ sessionId: sessionId });

  const importSessionStatus = useStatusCodes({
    modelType: ModelType.importsession
  });

  // Map from import steps to stepper steps
  const currentStep = useMemo(() => {
    switch (session.status) {
      case importSessionStatus.INITIAL:
        return 0;
      case importSessionStatus.MAPPING:
        return 1;
      case importSessionStatus.IMPORTING:
        return 2;
      case importSessionStatus.PROCESSING:
        return 3;
      case importSessionStatus.COMPLETE:
        return 4;
      default:
        return 0;
    }
  }, [session.status]);

  const widget = useMemo(() => {
    if (session.sessionQuery.isError) {
      return (
        <Alert color='red' title={t`Error`} icon={<IconExclamationCircle />}>
          {t`Failed to fetch import session data`}
        </Alert>
      );
    }

    switch (session.status) {
      case importSessionStatus.MAPPING:
        return <ImporterColumnSelector session={session} />;
      case importSessionStatus.PROCESSING:
        return <ImporterDataSelector session={session} />;
      case importSessionStatus.COMPLETE:
        return (
          <Stack gap='xs'>
            <Alert
              color='green'
              title={t`Import Complete`}
              icon={<IconCheck />}
            >
              {t`Data has been imported successfully`}
            </Alert>
            <Button color='blue' onClick={onClose}>{t`Close`}</Button>
          </Stack>
        );
      default:
        return <ImporterStatus session={session} />;
    }
  }, [session.status, session.sessionQuery]);

  const title: ReactNode = useMemo(() => {
    return (
      <Stack gap='xs' style={{ width: '100%' }}>
        <Group
          gap='xs'
          wrap='nowrap'
          justify='space-apart'
          grow
          preventGrowOverflow={false}
        >
          <StylishText size='lg'>
            {session.sessionData?.statusText ?? t`Importing Data`}
          </StylishText>
          <ImportDrawerStepper currentStep={currentStep} />
          <Space />
        </Group>
        <Divider />
      </Stack>
    );
  }, [currentStep, session.sessionData]);

  return (
    <Drawer
      position='bottom'
      size='80%'
      title={title}
      opened={opened}
      onClose={onClose}
      withCloseButton={true}
      closeOnEscape={false}
      closeOnClickOutside={false}
      styles={{
        header: {
          width: '100%'
        },
        title: {
          width: '100%'
        }
      }}
    >
      <Stack gap='xs'>
        <Paper p='md'>{widget}</Paper>
      </Stack>
    </Drawer>
  );
}
