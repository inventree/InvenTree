import { Tipp } from '@lib/components/Tipp';
import type { TippData } from '@lib/types/Core';
import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
import { Accordion, SimpleGrid, Stack } from '@mantine/core';
import { type JSX, useMemo } from 'react';
import { useShallow } from 'zustand/react/shallow';
import { StylishText } from '../../../../components/items/StylishText';
import { ServerAlert, getAlerts } from '../../../../components/nav/Alerts';
import { QuickAction } from '../../../../components/settings/QuickAction';
import { useServerApiState } from '../../../../states/ServerApiState';
import { useGlobalSettingsState } from '../../../../states/SettingsStates';

export default function HomePanel(): JSX.Element {
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
      <Tipp id='admin_home_1' />
      <Accordion
        multiple
        defaultValue={['quick-actions', 'active']}
        variant='contained'
      >
        <Accordion.Item value='quick-actions'>
          <Accordion.Control>
            <StylishText size='md'>
              <Trans>Quick Actions</Trans>
            </StylishText>
          </Accordion.Control>
          <Accordion.Panel>
            <QuickAction />
          </Accordion.Panel>
        </Accordion.Item>
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

export const globalTipps: Record<string, TippData> = {
  admin_home_1: {
    title: t`Admin Center Information`,
    color: 'blue',
    text: t`The home panel (and the whole Admin Center) is a new feature
    starting with the new UI and was previously (before 1.0) not
    available.

    The admin center provides a centralized location for all
    administration functionality and is meant to replace all
    interaction with the (django) backend admin interface.

    Please open feature requests (after checking the tracker) for
    any existing backend admin functionality you are missing in this
    UI. The backend admin interface should be used carefully and
    seldom.`
  }
}; // TODO: read from state / local storage
