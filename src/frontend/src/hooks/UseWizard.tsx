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

  // Reset the wizard to the first step
  useEffect(() => {
    if (opened) {
      setCurrentStep(0);
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
    }
  }, [currentStep, props.canStepForward]);

  // Go back to the previous step
  const previousStep = useCallback(() => {
    if (props.canStepBackward && !props.canStepBackward(currentStep)) {
      return;
    }

    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  }, [currentStep, props.canStepBackward]);

  // Render the wizard contents for the current step
  const contents = useMemo(() => {
    return props.renderStep(currentStep);
  }, [opened, currentStep, props.renderStep]);

  return {
    currentStep,
    opened,
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
        {contents}
      </WizardDrawer>
    )
  };
}
