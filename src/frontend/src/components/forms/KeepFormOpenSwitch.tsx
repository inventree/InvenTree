import { Switch } from '@mantine/core';
import { useEffect, useState } from 'react';

import { t } from '@lingui/core/macro';

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
      label={t`Keep form open`}
      description={t`Keep form open after submitting`}
      onChange={(e) => setKeepOpen(e.currentTarget.checked)}
    />
  );
}
