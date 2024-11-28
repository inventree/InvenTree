import { Trans, t } from '@lingui/macro';
import {
  ActionIcon,
  Button,
  ColorInput,
  ColorPicker,
  Container,
  DEFAULT_THEME,
  Group,
  Loader,
  Select,
  Slider,
  Table,
  Title,
  useMantineTheme
} from '@mantine/core';
import { IconRestore } from '@tabler/icons-react';
import { useState } from 'react';

import { ColorToggle } from '../../../../components/items/ColorToggle';
import { LanguageSelect } from '../../../../components/items/LanguageSelect';
import { SizeMarks } from '../../../../defaults/defaults';
import { IS_DEV } from '../../../../main';
import { useLocalState } from '../../../../states/LocalState';

function getLkp(color: string) {
  return { [DEFAULT_THEME.colors[color][6]]: color };
}
const LOOKUP = Object.assign(
  {},
  ...Object.keys(DEFAULT_THEME.colors).map((clr) => getLkp(clr))
);

export function UserTheme({ height }: Readonly<{ height: number }>) {
  const theme = useMantineTheme();

  const [themeLoader, setThemeLoader] = useLocalState((state) => [
    state.loader,
    state.setLoader
  ]);

  // white color
  const [whiteColor, setWhiteColor] = useState(theme.white);

  function changeWhite(color: string) {
    useLocalState.setState({ whiteColor: color });
    setWhiteColor(color);
  }

  // black color
  const [blackColor, setBlackColor] = useState(theme.black);

  function changeBlack(color: string) {
    useLocalState.setState({ blackColor: color });
    setBlackColor(color);
  }
  // radius
  function getMark(value: number) {
    const obj = SizeMarks.find((mark) => mark.value === value);
    if (obj) return obj;
    return SizeMarks[0];
  }

  function getDefaultRadius() {
    const obj = SizeMarks.find(
      (mark) => mark.label === useLocalState.getState().radius
    );
    if (obj) return obj.value;
    return 50;
  }
  const [radius, setRadius] = useState(getDefaultRadius());
  function changeRadius(value: number) {
    setRadius(value);
    useLocalState.setState({ radius: getMark(value).label });
  }

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
    <Container w='100%' mih={height} p={0}>
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
                <Button onClick={enablePseudoLang} variant='light'>
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
              <Group justify='left'>
                <ColorToggle />
              </Group>
            </Table.Td>
            <Table.Td />
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Highlight color</Trans>
            </Table.Td>
            <Table.Td>
              <ColorPicker
                format='hex'
                onChange={changePrimary}
                withPicker={false}
                swatches={Object.keys(LOOKUP)}
              />
            </Table.Td>
            <Table.Td>
              <Button color={theme.primaryColor} variant='light'>
                <Trans>Example</Trans>
              </Button>
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>White color</Trans>
            </Table.Td>
            <Table.Td>
              <ColorInput value={whiteColor} onChange={changeWhite} />
            </Table.Td>
            <Table.Td>
              <ActionIcon
                variant='default'
                onClick={() => changeWhite('#FFFFFF')}
              >
                <IconRestore />
              </ActionIcon>
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Black color</Trans>
            </Table.Td>
            <Table.Td>
              <ColorInput value={blackColor} onChange={changeBlack} />
            </Table.Td>
            <Table.Td>
              <ActionIcon
                variant='default'
                onClick={() => changeBlack('#000000')}
              >
                <IconRestore />
              </ActionIcon>
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Border Radius</Trans>
            </Table.Td>
            <Table.Td>
              <Slider
                label={(val) => getMark(val).label}
                defaultValue={50}
                step={25}
                marks={SizeMarks}
                value={radius}
                onChange={changeRadius}
                mb={18}
              />
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Loader</Trans>
            </Table.Td>
            <Table.Td>
              <Group justify='left'>
                <Select
                  data={loaderDate}
                  value={themeLoader}
                  onChange={changeLoader}
                />
              </Group>
            </Table.Td>
            <Table.Td>
              <Group justify='left'>
                <Loader type={themeLoader} mah={16} size='sm' />
              </Group>
            </Table.Td>
          </Table.Tr>
        </Table.Tbody>
      </Table>
    </Container>
  );
}
