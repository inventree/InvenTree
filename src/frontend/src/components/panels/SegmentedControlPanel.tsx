import SegmentedIconControl from '../buttons/SegmentedIconControl';
import type { PanelType } from './Panel';

export type SegmentedControlPanelSelection = {
  value: string;
  label: string;
  icon: React.ReactNode;
  content: React.ReactNode;
};

interface SegmentedPanelType extends PanelType {
  options: SegmentedControlPanelSelection[];
  selection: string;
  onChange: (value: string) => void;
}

/**
 * Display a panel which can be used to display multiple options,
 * based on a built-in segmented control.
 */
export default function SegmentedControlPanel(
  props: SegmentedPanelType
): PanelType {
  // Extract the content based on the selection
  let content = null;

  for (const option of props.options) {
    if (option.value === props.selection) {
      content = option.content;
      break;
    }
  }

  if (content === null && props.options.length > 0) {
    content = props.options[0].content;
  }

  return {
    ...props,
    content: content,
    controls: (
      <SegmentedIconControl
        value={props.selection}
        onChange={props.onChange}
        data={props.options.map((option: any) => ({
          value: option.value,
          label: option.label,
          icon: option.icon
        }))}
      />
    )
  };
}
