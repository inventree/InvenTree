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
    setOpened(false);
  }, []);

  // Progress the wizard to the next step
  const nextStep = useCallback(() => {
    if (props.canStepForward && !props.canStepForward(currentStep)) {
      return;
    }

    if (props.steps && currentStep < props.steps.length - 1) {
      setCurrentStep(currentStep + 1);
      clearError();
    }
  }, [currentStep, props.canStepForward]);

  // Go back to the previous step
  const previousStep = useCallback(() => {
    if (props.canStepBackward && !props.canStepBackward(currentStep)) {
      return;
    }

    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
      clearError();
    }
  }, [currentStep, props.canStepBackward]);

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
    wizard: (
      <WizardDrawer
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
