export interface UseWizardProps {
  opened: boolean;
  onClose: () => void;
}

export interface DataImportWizardProps extends UseWizardProps {
  sessionId: number;
}

export interface UseWizardReturn {
  wizard: React.ReactElement;
}
