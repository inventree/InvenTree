import { Tour } from '@mantine/core';

export interface FtuStep {
  target: string;
  title: string;
  description: string;
  action_before?: () => void;
}

export default function FirstUseTourView({
  active,
  onClose,
  steps
}: Readonly<{
  active: boolean;
  onClose: () => void;
  steps: FtuStep[];
}>) {
  return (
    <Tour active={active} onClose={onClose} zIndex={10002}>
      {steps.map((step, index) => (
        <Tour.Step
          key={index}
          target={`#${step.target}`}
          title={step.title}
          onStepOpen={step.action_before}
        >
          {step.description}
        </Tour.Step>
      ))}
    </Tour>
  );
}
