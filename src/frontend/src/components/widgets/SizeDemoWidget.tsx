import { Trans } from '@lingui/macro';
import { Title } from '@mantine/core';
import { useElementSize } from '@mantine/hooks';

export default function SizeDemoWidget() {
  const { ref, width, height } = useElementSize();

  return (
    <>
      <Title order={5}>
        <Trans>Size Demo Widget</Trans>
      </Title>
      <textarea ref={ref} />
      <div>
        <Trans>
          Width: {width}, height: {height}
        </Trans>
      </div>
    </>
  );
}
