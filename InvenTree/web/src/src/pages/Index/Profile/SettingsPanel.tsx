import { Trans, t } from '@lingui/macro';
import { Container, Skeleton, Title, Badge, NumberInput, TextInput, Chip, Space } from '@mantine/core';
import { Card, Group, Switch, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '../../../App';
import { GlobalSetting, Type } from '../../../contex/states';
import { InvenTreeStyle } from '../../../globalStyle';

export function SettingsPanel() {
    function fetchData() {
        return api.get('settings/global/').then((res) => res.data);
    }
    const { isLoading, data } = useQuery({ queryKey: ['settings-global'], queryFn: fetchData });
    const [showNames, setShowNames] = useState<boolean>(false);

    return (
        <Container>
            <Title order={3}><Trans>Settings</Trans></Title>
            <Chip checked={showNames} onChange={(val) => setShowNames(val)}><Trans>Show internal names</Trans></Chip>
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

    return (
        <Card withBorder className={classes.card}>
            <Text size="lg" weight={500}>{title}</Text><Text size="xs" color="dimmed" mb="md">{description}</Text>{data.map((item) => (SettingsBlock(item, showNames)))}
        </Card>
    );
}


function SettingsBlock(item: GlobalSetting, showNames = false): JSX.Element {
    const { classes } = InvenTreeStyle();

    function getControl(item: GlobalSetting) {
        if (item.type == Type.Boolean)
            return <Switch checked={item.value === 'True'} />
        if (item.type == Type.Integer)
            return <NumberInput value={parseInt(item.value)} />
        if (item.type == Type.String)
            return <TextInput value={item.value} />
        return <Text><Trans>Input {item.type} is not known</Trans></Text>
    }

    return <Group position="apart" className={classes.itemTopBorder} noWrap my='0' py='0' key={item.pk}>
        <div>
            <Group>
                <Text>{item.name}</Text>
                {showNames ? <Badge variant='outline' >{item.pk}|{item.key}</Badge> : null}
            </Group>
            <Text size="xs" color="dimmed">{item.description}</Text>
        </div>
        {getControl(item)}
    </Group>;
}
