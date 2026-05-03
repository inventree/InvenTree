import { Switch } from '@mantine/core';
import { useEffect, useState } from 'react';

export function KeepFormOpenSwitch({
  onChange
}: { onChange?: (v: boolean) => void }) {
  const [keepOpen, setKeepOpen] = useState(false);

  useEffect(() => {
    onChange?.(keepOpen);
  }, [keepOpen]);

  return (
    <Switch
      checked={keepOpen}
      radius='lg'
      size='sm'
      label='Keep form open'
      description='Keep form open after submitting'
      onChange={(e) => setKeepOpen(e.currentTarget.checked)}
    />
  );
}
