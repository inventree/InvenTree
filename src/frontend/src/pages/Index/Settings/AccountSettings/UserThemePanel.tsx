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
import { LoaderType } from '@mantine/styles/lib/theme/types/MantineTheme';
import { useState } from 'react';

import { SizeMarks } from '../../../../defaults/defaults';
import { InvenTreeStyle } from '../../../../globalStyle';
import { useLocalState } from '../../../../states/LocalState';

function getLkp(color: string) {
  return { [DEFAULT_THEME.colors[color][6]]: color };
}
const LOOKUP = Object.assign(
  {},
  ...Object.keys(DEFAULT_THEME.colors).map((clr) => getLkp(clr))
);

export function UserTheme({ height }: { height: number }) {
  const { theme } = InvenTreeStyle();

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
  const [loader, setLoader] = useState<LoaderType>(theme.loader);
  function changeLoader(value: LoaderType) {
    setLoader(value);
    useLocalState.setState({ loader: value });
  }

  return (
    <Container w="100%" mih={height} p={0}>
      <Title order={3}>
        <Trans>Theme</Trans>
      </Title>
      <Table>
        <tbody>
          <tr>
            <td>
              <Trans>Primary color</Trans>
            </td>
            <td>
              <ColorPicker
                format="hex"
                onChange={changePrimary}
                withPicker={false}
                swatches={Object.keys(LOOKUP)}
              />
            </td>
          </tr>
          <tr>
            <td>
              <Trans>White color</Trans>
            </td>
            <td>
              <ColorInput value={whiteColor} onChange={changeWhite} />
            </td>
          </tr>
          <tr>
            <td>
              <Trans>Black color</Trans>
            </td>
            <td>
              <ColorInput value={blackColor} onChange={changeBlack} />
            </td>
          </tr>
          <tr>
            <td>
              <Trans>Border Radius</Trans>
            </td>
            <td>
              <Slider
                label={(val) => getMark(val).label}
                defaultValue={50}
                step={25}
                marks={SizeMarks}
                value={radius}
                onChange={changeRadius}
                mb={18}
              />
            </td>
          </tr>
          <tr>
            <td>
              <Trans>Loader</Trans>
            </td>
            <td>
              <Group align="center">
                <Select
                  data={loaderDate}
                  value={loader}
                  onChange={changeLoader}
                />
                <Loader type={loader} mah={18} />
              </Group>
            </td>
          </tr>
        </tbody>
      </Table>
    </Container>
  );
}
