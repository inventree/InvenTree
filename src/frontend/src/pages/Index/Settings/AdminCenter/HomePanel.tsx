import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Alert, Button, Stack, Title } from '@mantine/core';
import { IconBrandGithub } from '@tabler/icons-react';
import type { JSX } from 'react';
import { QuickAction } from '../../../../components/settings/QuickAction';

export default function HomePanel(): JSX.Element {
  return (
    <Stack gap='xs'>
      <Alert color='blue' title={t`This is new!`}>
        <Trans>
          This is a new feature in PUI previously not available. It provides a
          centralized location for all administration functionality and is meant
          to replace Djangos admin view.
        </Trans>
        <br />
        <Trans>Please raise issues for any missing admin functionality.</Trans>
        <br />
        <Button
          color='green'
          top={'https://github.com/inventree/InvenTree/issues/new'}
        >
          <IconBrandGithub /> <Trans>Open an issue</Trans>
        </Button>
      </Alert>
      <QuickAction ml='' />
      <Title order={5}>
        <Trans>System status</Trans>
      </Title>
      TBD
      <Title order={5}>
        <Trans>Security recommodations</Trans>
      </Title>
      TBD
    </Stack>
  );
}
