import { t } from '@lingui/core/macro';
import { Trans } from '@lingui/react/macro';
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
  useMantineTheme
} from '@mantine/core';
import { IconRestore } from '@tabler/icons-react';
import { useState } from 'react';

import { StylishText } from '@lib/components/StylishText';
import { useShallow } from 'zustand/react/shallow';
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
  const [userTheme, setTheme, setLanguage] = useLocalState(
    useShallow((state) => [state.userTheme, state.setTheme, state.setLanguage])
  );

  // radius
  function getMark(value: number) {
    const obj = SizeMarks.find((mark) => mark.value === value);
    if (obj) return obj;
    return SizeMarks[0];
  }
  function getDefaultRadius() {
    const value = Number.parseInt(userTheme.radius.toString());
    return SizeMarks.some((mark) => mark.value === value) ? value : 50;
  }
  const [radius, setRadius] = useState(getDefaultRadius());
  function changeRadius(value: number) {
    setRadius(value);
    setTheme([{ key: 'radius', value: value.toString() }]);
  }

  return (
    <Container w='100%' mih={height} p={0}>
      <StylishText size='lg'>
        <Trans>Display Settings</Trans>
      </StylishText>
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
                <Button
                  onClick={() => setLanguage('pseudo-LOCALE', true)}
                  variant='light'
                >
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
                onChange={(v) =>
                  setTheme([{ key: 'primaryColor', value: LOOKUP[v] }])
                }
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
              <ColorInput
                aria-label='Color Picker White'
                value={userTheme.whiteColor}
                onChange={(v) => setTheme([{ key: 'whiteColor', value: v }])}
              />
            </Table.Td>
            <Table.Td>
              <ActionIcon
                variant='default'
                aria-label='Reset White Color'
                onClick={() =>
                  setTheme([{ key: 'whiteColor', value: '#FFFFFF' }])
                }
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
              <ColorInput
                aria-label='Color Picker Black'
                value={userTheme.blackColor}
                onChange={(v) => setTheme([{ key: 'blackColor', value: v }])}
              />
            </Table.Td>
            <Table.Td>
              <ActionIcon
                variant='default'
                aria-label='Reset Black Color'
                onClick={() =>
                  setTheme([{ key: 'blackColor', value: '#000000' }])
                }
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
                  aria-label='Loader Type Selector'
                  data={[
                    { value: 'bars', label: t`Bars` },
                    { value: 'oval', label: t`Oval` },
                    { value: 'dots', label: t`Dots` }
                  ]}
                  value={userTheme.loader}
                  onChange={(v) => {
                    if (v != null) setTheme([{ key: 'loader', value: v }]);
                  }}
                />
              </Group>
            </Table.Td>
            <Table.Td>
              <Group justify='left'>
                <Loader type={userTheme.loader} mah={16} size='sm' />
              </Group>
            </Table.Td>
          </Table.Tr>
        </Table.Tbody>
      </Table>
    </Container>
  );
}
