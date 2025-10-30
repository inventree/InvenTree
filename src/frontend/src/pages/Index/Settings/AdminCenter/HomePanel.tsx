import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import {
  Accordion,
  Alert,
  Button,
  SimpleGrid,
  Stack,
  Text
} from '@mantine/core';
import { IconBrandGithub } from '@tabler/icons-react';
import { type JSX, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { useShallow } from 'zustand/react/shallow';
import { StylishText } from '../../../../components/items/StylishText';
import { ServerAlert, getAlerts } from '../../../../components/nav/Alerts';
import { QuickAction } from '../../../../components/settings/QuickAction';
import { useServerApiState } from '../../../../states/ServerApiState';
import { useGlobalSettingsState } from '../../../../states/SettingsStates';

export default function HomePanel(): JSX.Element {
  const [dismissed, setDismissed] = useState<boolean>(false);
  const [server] = useServerApiState(useShallow((state) => [state.server]));
  const globalSettings = useGlobalSettingsState();

  const accElements = useMemo(() => {
    const _alerts = getAlerts(server, globalSettings, true);
    return [
      {
        key: 'active',
        text: t`Active Alerts`,
        elements: _alerts.filter((alert) => alert.condition)
      },
      {
        key: 'inactive',
        text: t`Inactive Alerts`,
        elements: _alerts.filter((alert) => !alert.condition)
      }
    ];
  }, [server, globalSettings]);

  return (
    <Stack gap='xs'>
      {dismissed ? null : (
        <Alert
          color='blue'
          title={t`Admin Center Information`}
          withCloseButton
          onClose={() => setDismissed(true)}
        >
          <Stack gap='xs'>
            <Text>
              <Trans>
                The home panel (and the whole Admin Center) is a new feature
                starting with the new UI and was previously (before 1.0) not
                available.
              </Trans>
            </Text>
            <Text>
              <Trans>
                The admin center provides a centralized location for all
                administration functionality and is meant to replace all
                interaction with the (django) backend admin interface.
              </Trans>
            </Text>
            <Text>
              <Trans>
                Please open feature requests (after checking the tracker) for
                any existing backend admin functionality you are missing in this
                UI. The backend admin interface should be used carefully and
                seldom.
              </Trans>
            </Text>
          </Stack>
          <Button
            color='green'
            component={Link}
            size='compact-md'
            to={'https://github.com/inventree/InvenTree/issues/new'}
            target='_blank'
          >
            <IconBrandGithub /> <Trans>Open an issue</Trans>
          </Button>
        </Alert>
      )}
      <QuickAction ml='' />
      <StylishText size='lg'>
        <Trans>System Status</Trans>
      </StylishText>
      <Accordion defaultValue={'active'} variant='contained'>
        {accElements.map(
          (item) =>
            item.elements.length > 0 && (
              <Accordion.Item key={item.key} value={item.key}>
                <Accordion.Control>
                  <StylishText size='md'>{item.text}</StylishText>
                </Accordion.Control>
                <Accordion.Panel>
                  <SimpleGrid
                    cols={{
                      base: 1,
                      '600px': 2,
                      '1200px': 3
                    }}
                    type='container'
                    spacing='sm'
                  >
                    {item.elements.map((alert) => (
                      <ServerAlert alert={alert} />
                    ))}
                  </SimpleGrid>
                </Accordion.Panel>
              </Accordion.Item>
            )
        )}
      </Accordion>
    </Stack>
  );
}
