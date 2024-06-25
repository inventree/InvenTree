import { Trans, t } from '@lingui/macro';
import {
  ColorInput,
  ColorPicker,
  Container,
  DEFAULT_THEME,
  Group,
  Loader,
  Select,
  Slider,
  Table,
  Title
} from '@mantine/core';
import { useState } from 'react';

import { SizeMarks } from '../../../../defaults/defaults';
import { useLocalState } from '../../../../states/LocalState';
import { theme } from '../../../../theme';

function getLkp(color: string) {
  return { [DEFAULT_THEME.colors[color][6]]: color };
}
const LOOKUP = Object.assign(
  {},
  ...Object.keys(DEFAULT_THEME.colors).map((clr) => getLkp(clr))
);

export function UserTheme({ height }: { height: number }) {
  // primary color
  function changePrimary(color: string) {
    useLocalState.setState({ primaryColor: LOOKUP[color] });
  }
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
  // loader
  const loaderDate = [
    { value: 'bars', label: t`bars` },
    { value: 'oval', label: t`oval` },
    { value: 'dots', label: t`dots` }
  ];
  const [themeLoader, setThemeLoader] = useLocalState((state) => [
    state.loader,
    state.setLoader
  ]);
  function changeLoader(value: string | null) {
    if (value === null) return;
    setThemeLoader(value);
  }

  return (
    <Container w="100%" mih={height} p={0}>
      <Title order={3}>
        <Trans>Theme</Trans>
      </Title>
      <Table>
        <Table.Tbody>
          <Table.Tr>
            <Table.Td>
              <Trans>Primary color</Trans>
            </Table.Td>
            <Table.Td>
              <ColorPicker
                format="hex"
                onChange={changePrimary}
                withPicker={false}
                swatches={Object.keys(LOOKUP)}
              />
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>White color</Trans>
            </Table.Td>
            <Table.Td>
              <ColorInput value={whiteColor} onChange={changeWhite} />
            </Table.Td>
          </Table.Tr>
          <Table.Tr>
            <Table.Td>
              <Trans>Black color</Trans>
            </Table.Td>
            <Table.Td>
              <ColorInput value={blackColor} onChange={changeBlack} />
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
              <Group align="center">
                <Select
                  data={loaderDate}
                  value={themeLoader}
                  onChange={changeLoader}
                />
                <Loader type={themeLoader} mah={18} />
              </Group>
            </Table.Td>
          </Table.Tr>
        </Table.Tbody>
      </Table>
    </Container>
  );
}
