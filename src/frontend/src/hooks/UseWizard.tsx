import { Alert, Stack } from '@mantine/core';
import { IconExclamationCircle } from '@tabler/icons-react';
import {
  type ReactNode,
  useCallback,
  useEffect,
  useMemo,
  useState
} from 'react';
import WizardDrawer from '../components/wizards/WizardDrawer';

export interface WizardProps {
  title: string;
  steps: string[];
  disableManualStepChange?: boolean;
  onClose?: () => void;
  renderStep: (step: number) => ReactNode;
  canStepForward?: (step: number) => boolean;
  canStepBackward?: (step: number) => boolean;
}

export interface WizardState {
  opened: boolean;
  currentStep: number;
  clearError: () => void;
  error: string | null;
  setError: (error: string | null) => void;
  errorDetail: string | null;
  setErrorDetail: (errorDetail: string | null) => void;
  openWizard: () => void;
  closeWizard: () => void;
  nextStep: () => void;
  previousStep: () => void;
  wizard: ReactNode;
  setStep: (step: number) => void;
}

/**
 * Hook for managing a wizard-style multi-step process.
 * - Manage the current step of the wizard
 * - Allows opening and closing the wizard
 * - Handles progression between steps with optional validation
 */
export default function useWizard(props: WizardProps): WizardState {
  const [currentStep, setCurrentStep] = useState(0);
  const [opened, setOpened] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [errorDetail, setErrorDetail] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
    setErrorDetail(null);
  }, []);

  // Reset the wizard to an initial state when opened
  useEffect(() => {
    if (opened) {
      setCurrentStep(0);
      clearError();
    }
  }, [opened]);

  // Open the wizard
  const openWizard = useCallback(() => {
    setOpened(true);
  }, []);

  // Close the wizard
  const closeWizard = useCallback(() => {
    props.onClose?.();
    setOpened(false);
  }, []);

  // Progress the wizard to the next step
  const nextStep = useCallback(() => {
    setCurrentStep((c) => {
      if (props.canStepForward && !props.canStepForward(c)) {
        return c;
      }
      const newStep = Math.min(c + 1, props.steps.length - 1);
      if (newStep !== c) clearError();
      return newStep;
    });
  }, [props.canStepForward]);

  // Go back to the previous step
  const previousStep = useCallback(() => {
    setCurrentStep((c) => {
      if (props.canStepBackward && !props.canStepBackward(c)) {
        return c;
      }
      const newStep = Math.max(c - 1, 0);
      if (newStep !== c) clearError();
      return newStep;
    });
  }, [props.canStepBackward]);

  const setStep = useCallback(
    (step: number) => {
      if (step < 0 || step >= props.steps.length) {
        return;
      }
      setCurrentStep(step);
      clearError();
    },
    [props.steps.length]
  );

  // Render the wizard contents for the current step
  const contents = useMemo(() => {
    return props.renderStep(currentStep);
  }, [opened, currentStep, props.renderStep]);

  return {
    currentStep,
    opened,
    clearError,
    error,
    setError,
    errorDetail,
    setErrorDetail,
    openWizard,
    closeWizard,
    nextStep,
    previousStep,
    setStep,
    wizard: (
      <WizardDrawer
        disableManualStepChange={props.disableManualStepChange}
        title={props.title}
        currentStep={currentStep}
        steps={props.steps}
        opened={opened}
        onClose={closeWizard}
        onNextStep={nextStep}
        onPreviousStep={previousStep}
      >
        <Stack gap='xs'>
          {error && (
            <Alert color='red' title={error} icon={<IconExclamationCircle />}>
              {errorDetail}
            </Alert>
          )}
          {contents}
        </Stack>
      </WizardDrawer>
    )
  };
}
