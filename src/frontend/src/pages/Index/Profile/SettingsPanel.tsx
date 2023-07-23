import { Trans, t } from '@lingui/macro';
import {
  Accordion,
  Badge,
  Card,
  Chip,
  Container,
  Group,
  NumberInput,
  Select,
  Skeleton,
  Space,
  Switch,
  Text,
  TextInput,
  Title
} from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { showNotification } from '@mantine/notifications';
import { IconCheck, IconX } from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';

import { api } from '../../../App';
import { InvenTreeStyle } from '../../../globalStyle';
import { Setting, SettingTyp, SettingType } from '../../../states/states';

interface SectionKeys {
  key: string;
  icon?: string;
}
interface Section {
  key: string;
  name: string;
  description?: string;
  keys: SectionKeys[];
}

export function SettingsPanel({
  reference,
  title,
  description,
  url,
  sections
}: {
  reference: string;
  title: string;
  description: string;
  url?: string;
  sections?: Section[];
}) {
  const panel_url = url ? url : `settings/${reference}/`;
  function fetchData() {
    return api.get(panel_url).then((res) => res.data);
  }
  const { isLoading, data, isError } = useQuery({
    queryKey: [`settings-${reference}`],
    queryFn: fetchData,
    refetchOnWindowFocus: false
  });
  const [showNames, setShowNames] = useState<boolean>(false);
  const { classes } = InvenTreeStyle();

  function LoadingBlock({ children }: { children: JSX.Element }) {
    if (isLoading) return <Skeleton />;
    else if (isError)
      return (
        <Text>
          <Trans>Failed to load</Trans>
        </Text>
      );
    else if (data) return children;
    else
      return (
        <Text>
          <Trans>Failed to load</Trans>
        </Text>
      );
  }

  function Settings({ data }: { data: Setting[] }) {
    return <>{data.map((item) => SettingsBlock(item, panel_url, showNames))}</>;
  }

  function filter_data(data: Setting[], section: Section) {
    if (data) {
      return section.keys.map((key) => {
        return data.filter((item: Setting) => item.key === key.key)[0];
      });
    }
    return data;
  }

  return (
    <Container>
      <Title order={3}>
        <Trans>Settings</Trans>
      </Title>
      <Chip checked={showNames} onChange={(value) => setShowNames(value)}>
        <Trans>Show internal names</Trans>
      </Chip>
      <Space h="md" />

      {sections != undefined ? (
        <Accordion variant="separated">
          {sections.map((section) => (
            <Accordion.Item key={section.key} value={section.key}>
              <Accordion.Control>
                {section.name}
                <Text size={'xs'}>{section.description}</Text>
              </Accordion.Control>
              <Accordion.Panel>
                <LoadingBlock>
                  <Settings data={filter_data(data, section)} />
                </LoadingBlock>
              </Accordion.Panel>
            </Accordion.Item>
          ))}
        </Accordion>
      ) : (
        <LoadingBlock>
          <Card withBorder className={classes.card}>
            <Text size="lg" weight={500}>
              {title}
            </Text>
            <Text size="xs" color="dimmed" mb="md">
              {description}
            </Text>
            <Settings data={data} />
          </Card>
        </LoadingBlock>
      )}
    </Container>
  );
}

function SettingsBlock(
  item: Setting,
  url: string,
  showNames = false
): JSX.Element {
  const { classes } = InvenTreeStyle();

  if (item === undefined) return <></>;

  let control = (
    <Text>
      <Trans>Input {item.type} is not known</Trans>
    </Text>
  );
  let setfnc = (value: React.SetStateAction<any>) => {
    console.log(value);
  };

  function onChange(value: string | number | boolean | null | undefined) {
    const val = value?.toString();
    api
      .put(`${url}${item.key}/`, { value: val })
      .then((res) => {
        showNotification({
          title: t`Saved changes ${item.key}`,
          message: t`Changed to ${res.data.value}`,
          color: 'teal',
          icon: <IconCheck />
        });
        if (item.type == SettingType.Boolean) {
          setfnc(res.data.value === 'False' ? false : true);
        } else {
          setfnc(res.data.value);
        }
      })
      .catch((err) => {
        const err_msg = err?.response.data.non_field_errors;
        console.log(err_msg);
        showNotification({
          title: t`Error while saving ${item.key}`,
          message: err_msg ? err_msg : t`Error was ${err}`,
          color: 'red',
          icon: <IconX />
        });
      });
  }

  // Select control
  switch (item.type) {
    case SettingType.Boolean: {
      const [value, setValue] = useState<boolean>(
        item.value === 'False' ? false : true
      );
      setfnc = setValue;
      control = (
        <Switch
          checked={value}
          onChange={(event) => onChange(event.currentTarget.checked)}
        />
      );
      break;
    }
    case SettingType.Integer: {
      const [value, setValue] = useState<number>(parseInt(item.value));
      setfnc = setValue;
      control = (
        <NumberInput value={value} onChange={(value) => onChange(value)} />
      );
      break;
    }
    case SettingType.String: {
      const [value, setValue] = useState<string>(item.value);
      setfnc = setValue;

      if (item.choices.length > 0) {
        const choices = item.choices.map((choice: any) => ({
          label: choice.display_name,
          value: choice.value
        }));
        control = (
          <Select
            searchable
            data={choices}
            value={value}
            onChange={(value) => onChange(value)}
          />
        );
      } else {
        const [debouncedValue] = useDebouncedValue(value, 500);
        useEffect(() => {
          if (item.value !== debouncedValue) {
            onChange(debouncedValue);
          }
        }, [debouncedValue]);

        control = (
          <TextInput
            value={value}
            onChange={(event) => setValue(event.currentTarget.value)}
          />
        );
      }
      break;
    }
    default:
      console.log('Error: Unknown type');
  }

  return (
    <Group
      position="apart"
      className={classes.itemTopBorder}
      noWrap
      my="0"
      py="0"
      key={item.pk}
    >
      <div>
        {item.typ == SettingTyp.Plugin ? (
          <Badge color={'green'} variant="outline">
            <Trans>Plugin: {item.plugin}</Trans>
          </Badge>
        ) : null}
        {item.typ == SettingTyp.Notification ? (
          <Badge color={'green'} variant="outline">
            <Trans>Method: {item.method}</Trans>
          </Badge>
        ) : null}
        <Group>
          <Text>{item.name}</Text>
          {showNames ? (
            <Badge variant="outline">
              {item.pk}|{item.key}
            </Badge>
          ) : null}
        </Group>
        <Text size="xs" color="dimmed">
          {item.description}
        </Text>
      </div>
      {control}
    </Group>
  );
}
