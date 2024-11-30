import {
  Divider,
  Drawer,
  Group,
  Paper,
  Space,
  Stack,
  Stepper
} from '@mantine/core';
import { type ReactNode, useMemo } from 'react';
import { Boundary } from '../Boundary';
import { StylishText } from '../items/StylishText';

/**
 * Progress stepper displayed at the top of the wizard drawer.
 */
function WizardProgressStepper({
  currentStep,
  steps
}: {
  currentStep: number;
  steps?: string[];
}) {
  if (!steps || steps.length == 0) {
    return null;
  }

  return (
    <Stepper
      active={currentStep}
      onStepClick={undefined}
      allowNextStepsSelect={false}
      iconSize={20}
      size='xs'
    >
      {steps.map((step: string) => (
        <Stepper.Step label={step} key={step} />
      ))}
    </Stepper>
  );
}

/**
 * A generic "wizard" drawer, for handling multi-step processes.
 */
export default function WizardDrawer({
  title,
  currentStep,
  steps,
  children,
  opened,
  onClose
}: {
  title: string;
  currentStep: number;
  steps?: string[];
  children: ReactNode;
  opened: boolean;
  onClose: () => void;
}) {
  const titleBlock: ReactNode = useMemo(() => {
    return (
      <Stack gap='xs' style={{ width: '100%' }}>
        <Group
          gap='xs'
          wrap='nowrap'
          justify='space-between'
          grow
          preventGrowOverflow={false}
        >
          <StylishText size='lg'>{title}</StylishText>
          <WizardProgressStepper currentStep={currentStep} steps={steps} />
          <Space />
        </Group>
        <Divider />
      </Stack>
    );
  }, [title, currentStep, steps]);

  return (
    <Drawer
      position='bottom'
      size={'75%'}
      title={titleBlock}
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
      opened={opened}
      onClose={onClose}
    >
      <Boundary label='wizard-drawer'>
        <Paper p='md'>{}</Paper>
        {children}
      </Boundary>
    </Drawer>
  );
}
