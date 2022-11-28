import { Trans, t } from '@lingui/macro';
import { Container, Skeleton, Title, Badge, NumberInput, TextInput, Chip, Space, Select } from '@mantine/core';
import { Card, Group, Switch, Text } from '@mantine/core';
import { showNotification } from '@mantine/notifications';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '../../../App';
import { GlobalSetting, Type } from '../../../contex/states';
import { InvenTreeStyle } from '../../../globalStyle';
import { IconCheck, IconX } from '@tabler/icons';

export function SettingsPanel() {
    function fetchData() {
        return api.get('settings/global/').then((res) => res.data);
    }
    const { isLoading, data } = useQuery({ queryKey: ['settings-global'], queryFn: fetchData, refetchOnWindowFocus: false });
    const [showNames, setShowNames] = useState<boolean>(false);


    return (
        <Container>
            <Title order={3}><Trans>Settings</Trans></Title>
            <Chip checked={showNames} onChange={(value) => setShowNames(value)}><Trans>Show internal names</Trans></Chip>
            <Space h="md" />
            {isLoading ?
                <><Text><Trans>Data is current beeing loaded</Trans></Text><Skeleton h={3} /></>
                :
                <SwitchesCard title={t`Global Server Settings`} description={t`Global Settings for this instance`} data={data} showNames={showNames} />
            }
        </Container >
    );
}


export function SwitchesCard({ title, description, data, showNames = false }: { title: string; description: string; data: GlobalSetting[]; showNames?: boolean; }) {
    const { classes } = InvenTreeStyle();
    const items = data.map((item) => (SettingsBlock(item, showNames)))

    return (
        <Card withBorder className={classes.card}>
            <Text size="lg" weight={500}>{title}</Text><Text size="xs" color="dimmed" mb="md">{description}</Text>{items}
        </Card>
    );
}


function SettingsBlock(item: GlobalSetting, showNames = false): JSX.Element {
    const { classes } = InvenTreeStyle();

    let control = <Text><Trans>Input {item.type} is not known</Trans></Text>
    let setfnc = (value: React.SetStateAction<any>) => { console.log(value) };

    function onChange(value: string | number | boolean | null | undefined) {
        const val = value?.toString;
        api.put(`settings/global/${item.key}/`, { value: val }).then((res) => {
            showNotification({ title: t`Saved changes ${item.key}`, message: t`Changed to ${res.data.value}`, color: 'teal', icon: < IconCheck size={18} />, })
            if (item.type == Type.Boolean) {
                setfnc(res.data.value === 'False' ? false : true);
            } else {
                setfnc(res.data.value);
            }
        }).catch((err) => {
            const err_msg = err?.response.data.non_field_errors
            console.log(err_msg);
            showNotification({ title: t`Error while saving ${item.key}`, message: (err_msg) ? err_msg : t`Error was ${err}`, color: 'red', icon: <IconX size={18} /> })
        });
    }

    // Select control
    switch (item.type) {
        case Type.Boolean: {
            const [value, setValue] = useState<boolean>(item.value === 'False' ? false : true);
            setfnc = setValue
            control = <Switch checked={value} onChange={(event) => onChange(event.currentTarget.checked)} />
            break;
        }
        case Type.Integer: {
            const [value, setValue] = useState<number>(parseInt(item.value));
            setfnc = setValue
            control = <NumberInput value={value} onChange={(value) => onChange(value)} />
            break;
        }
        case Type.String: {
            const [value, setValue] = useState<string>(item.value);
            setfnc = setValue

            if (item.choices.length > 0) {
                control = <Select data={item.choices} value={value} onChange={(value) => onChange(value)} />
            }
            else {
                control = <TextInput value={value} onChange={(event) => onChange(event.currentTarget.value)} />;
            }
            break;
        }
        default:
            console.log('Error: Unknown type');
    }

    return <Group position="apart" className={classes.itemTopBorder} noWrap my='0' py='0' key={item.pk}>
        <div>
            <Group>
                <Text>{item.name}</Text>
                {showNames ? <Badge variant='outline' >{item.pk}|{item.key}</Badge> : null}
            </Group>
            <Text size="xs" color="dimmed">{item.description}</Text>
        </div>
        {control}
    </Group>;
}
