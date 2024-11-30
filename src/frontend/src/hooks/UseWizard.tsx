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
  steps?: string[];
  renderStep: (step: number) => ReactNode;
}

export interface WizardState {
  opened: boolean;
  currentStep: number;
  openWizard: () => void;
  closeWizard: () => void;
  nextStep: () => void;
  previousStep: () => void;
  setCurrentStep: (step: number) => void;
  wizard: ReactNode;
}

export default function useWizard(props: WizardProps): WizardState {
  const [currentStep, setCurrentStep] = useState(0);
  const [opened, setOpened] = useState(false);

  // Reset the wizard to the first step
  useEffect(() => {
    if (opened) {
      setCurrentStep(0);
    }
  }, [opened]);

  const openWizard = useCallback(() => {
    setOpened(true);
  }, []);

  const closeWizard = useCallback(() => {
    setOpened(false);
  }, []);

  const nextStep = useCallback(() => {
    setCurrentStep((prev) => prev + 1);
  }, []);

  const previousStep = useCallback(() => {
    setCurrentStep((prev) => prev - 1);
  }, []);

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
    setCurrentStep,
    wizard: (
      <WizardDrawer
        title={props.title}
        currentStep={currentStep}
        steps={props.steps}
        opened={opened}
        onClose={closeWizard}
      >
        {contents}
      </WizardDrawer>
    )
  };
}
