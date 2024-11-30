import { t } from '@lingui/macro';
import {
  ActionIcon,
  Card,
  Divider,
  Drawer,
  Group,
  Paper,
  Space,
  Stack,
  Stepper,
  Tooltip
} from '@mantine/core';
import {
  IconArrowLeft,
  IconArrowRight,
  IconCircleCheck
} from '@tabler/icons-react';
import { type ReactNode, useCallback, useMemo } from 'react';
import { Boundary } from '../Boundary';
import { StylishText } from '../items/StylishText';

/**
 * Progress stepper displayed at the top of the wizard drawer.
 */
function WizardProgressStepper({
  currentStep,
  steps,
  onSelectStep
}: {
  currentStep: number;
  steps: string[];
  onSelectStep: (step: number) => void;
}) {
  if (!steps || steps.length == 0) {
    return null;
  }

  // Determine if the user can select a particular step
  const canSelectStep = useCallback(
    (step: number) => {
      if (!steps || steps.length <= 1) {
        return false;
      }

      // Only allow single-step progression
      return Math.abs(step - currentStep) == 1;
    },
    [currentStep, steps]
  );

  const canStepBackward = currentStep > 0;
  const canStepForward = currentStep < steps.length - 1;

  return (
    <Card p='xs' withBorder>
      <Group justify='space-between' gap='xs' wrap='nowrap'>
        <Tooltip
          label={steps[currentStep - 1]}
          position='top'
          disabled={!canStepBackward}
        >
          <ActionIcon
            variant='transparent'
            onClick={() => onSelectStep(currentStep - 1)}
            disabled={!canStepBackward}
          >
            <IconArrowLeft />
          </ActionIcon>
        </Tooltip>
        <Stepper
          active={currentStep}
          onStepClick={(stepIndex: number) => onSelectStep(stepIndex)}
          iconSize={20}
          size='xs'
        >
          {steps.map((step: string, idx: number) => (
            <Stepper.Step
              label={step}
              key={step}
              aria-label={`wizard-step-${idx}`}
              allowStepSelect={canSelectStep(idx)}
            />
          ))}
        </Stepper>
        {canStepForward ? (
          <Tooltip
            label={steps[currentStep + 1]}
            position='top'
            disabled={!canStepForward}
          >
            <ActionIcon
              variant='transparent'
              onClick={() => onSelectStep(currentStep + 1)}
              disabled={!canStepForward}
            >
              <IconArrowRight />
            </ActionIcon>
          </Tooltip>
        ) : (
          <Tooltip label={t`Complete`} position='top'>
            <ActionIcon color='green' variant='transparent'>
              <IconCircleCheck />
            </ActionIcon>
          </Tooltip>
        )}
      </Group>
    </Card>
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
  onClose,
  onNextStep,
  onPreviousStep
}: {
  title: string;
  currentStep: number;
  steps: string[];
  children: ReactNode;
  opened: boolean;
  onClose: () => void;
  onNextStep?: () => void;
  onPreviousStep?: () => void;
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
          <StylishText size='xl'>{title}</StylishText>
          <WizardProgressStepper
            currentStep={currentStep}
            steps={steps}
            onSelectStep={(step: number) => {
              if (step < currentStep) {
                onPreviousStep?.();
              } else {
                onNextStep?.();
              }
            }}
          />
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
