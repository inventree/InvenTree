import { Trans } from '@lingui/macro';
import { Button, Container, Group, Table, Title } from '@mantine/core';

import { ColorToggle } from '../../../../components/items/ColorToggle';
import { LanguageSelect } from '../../../../components/items/LanguageSelect';
import { IS_DEV } from '../../../../main';
import { useLocalState } from '../../../../states/LocalState';

export function DisplaySettingsPanel({ height }: { height: number }) {
  function enablePseudoLang(): void {
    useLocalState.setState({ language: 'pseudo-LOCALE' });
  }

  return (
    <Container w="100%" mih={height} p={0}>
      <Title order={3}>
        <Trans>Display Settings</Trans>
      </Title>
      <Table>
        <tbody>
          <tr>
            <td>
              <Trans>Color Mode</Trans>
            </td>
            <td>
              <Group>
                <ColorToggle />
              </Group>
            </td>
          </tr>
          <tr>
            <td>
              <Trans>Language</Trans>
            </td>
            <td>
              {' '}
              <Group>
                <LanguageSelect width={200} />
                {IS_DEV && (
                  <Button onClick={enablePseudoLang} variant="light">
                    <Trans>Use pseudo language</Trans>
                  </Button>
                )}
              </Group>
            </td>
          </tr>
        </tbody>
      </Table>
    </Container>
  );
}
