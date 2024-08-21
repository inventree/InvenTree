import { Trans, t } from '@lingui/macro';
import {
  Button,
  ColorPicker,
  Container,
  DEFAULT_THEME,
  Group,
  Loader,
  Select,
  Table,
  Title,
  useMantineTheme
} from '@mantine/core';

import { ColorToggle } from '../../../../components/items/ColorToggle';
import { LanguageSelect } from '../../../../components/items/LanguageSelect';
import { IS_DEV } from '../../../../main';
import { useLocalState } from '../../../../states/LocalState';

function getLkp(color: string) {
  return { [DEFAULT_THEME.colors[color][6]]: color };
}
const LOOKUP = Object.assign(
  {},
  ...Object.keys(DEFAULT_THEME.colors).map((clr) => getLkp(clr))
);

export function UserTheme({ height }: { height: number }) {
  const [themeLoader, setThemeLoader] = useLocalState((state) => [
    state.loader,
    state.setLoader
  ]);

  const theme = useMantineTheme();

  // Set theme primary color
  function changePrimary(color: string) {
    useLocalState.setState({ primaryColor: LOOKUP[color] });
  }

  function enablePseudoLang(): void {
    useLocalState.setState({ language: 'pseudo-LOCALE' });
  }

  // Custom loading indicator
  const loaderDate = [
    { value: 'bars', label: t`Bars` },
    { value: 'oval', label: t`Oval` },
    { value: 'dots', label: t`Dots` }
  ];

  function changeLoader(value: string | null) {
    if (value === null) return;
    setThemeLoader(value);
  }

  return (
    <Container w="100%" mih={height} p={0}>
      <Title order={3}>
        <Trans>Display Settings</Trans>
      </Title>
      <Table>
        <Table.Tbody>
          <Table.Tr>
            <Table.Td>
              <Trans>Language</Trans>
            </Table.Td>
            <Table.Td>
              <LanguageSelect width={200} />
            </Table.Td>
            <Table.Td>
              {IS_DEV && (
                <Button onClick={enablePseudoLang} variant="light">
                  <Trans>Use pseudo language</Trans>
                </Button>
              )}
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Color Mode</Trans>
            </Table.Td>
            <Table.Td>
              <Group justify="left">
                <ColorToggle />
              </Group>
            </Table.Td>
            <Table.Td></Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Loader</Trans>
            </Table.Td>
            <Table.Td>
              <Group justify="left">
                <Select
                  data={loaderDate}
                  value={themeLoader}
                  onChange={changeLoader}
                />
              </Group>
            </Table.Td>
            <Table.Td>
              <Group justify="left">
                <Loader type={themeLoader} mah={18} />
              </Group>
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Highlight color</Trans>
            </Table.Td>
            <Table.Td>
              <ColorPicker
                format="hex"
                onChange={changePrimary}
                withPicker={false}
                swatches={Object.keys(LOOKUP)}
              />
            </Table.Td>
            <Table.Td>
              <Button color={theme.primaryColor} variant="light">
                <Trans>Example</Trans>
              </Button>
            </Table.Td>
          </Table.Tr>
        </Table.Tbody>
      </Table>
    </Container>
  );
}
