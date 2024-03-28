import {
  Badge,
  Button,
  Card,
  CloseButton,
  Divider,
  Group,
  NumberInput,
  Paper,
  ScrollArea,
  Space,
  Stack,
  Text,
  Title
} from '@mantine/core';
import { IconCheckbox, IconShoppingCart } from '@tabler/icons-react';
import React from 'react';
import { useState } from 'react';

import { Thumbnail } from '../../components/images/Thumbnail';
import { RenderInstance } from '../../components/render/Instance';
import { ModelType } from '../../enums/ModelType';

// Scan Item
interface ScanItem {
  id: string;
  ref: string;
  data: any;
  instance?: any;
  timestamp: Date;
  source: string;
  link?: string;
  model?: ModelType;
  pk?: string;
}

interface inputProps {
  items: ScanItem[];
}

export default function ScanCart({ items }: inputProps) {
  const [value, setValue] = useState<string>('');

  const renderItemList = items.map((item) => {
    console.log(item);
    return (
      <Card key={item.id}>
        <Group position="apart">
          <Group>
            {/* Image */}
            <Thumbnail size={128} src={item.instance?.part_detail?.image} />

            {/* Details */}
            <Stack>
              <Group>
                <Title order={4}>
                  {item.instance?.part_detail?.full_name ||
                    `Invalid Stock Item`}
                </Title>
                <Badge color={item.model === 'stockitem' ? 'teal' : 'red'}>
                  {item.model}
                </Badge>
              </Group>

              <RenderInstance model={item.model} instance={item.instance} />
              <Group position="apart">
                <Group>
                  <div>{item.instance?.part_detail?.name || 'ERROR'}</div>
                  <div>{item.instance?.part_detail?.IPN || 'UNDEFINED'}</div>
                  <div>{item.model}</div>
                  {/* <div>{JSON.stringify(item.data)}</div> */}
                  <div>Source: {item.source}</div>
                  <div>{item.timestamp?.toString()}</div>
                </Group>
              </Group>
            </Stack>
          </Group>

          {/* User Actions */}
          <Group spacing={24}>
            <Text size="md" fw={500}>
              Quantity
            </Text>
            <NumberInput
              step={1}
              precision={1}
              defaultValue={1}
              value={1}
              disabled={item.model !== 'stockitem'}
            />
            <CloseButton size={24} />
          </Group>
        </Group>
      </Card>
    );
  });

  return (
    <>
      <Paper>
        {/* Component Title */}
        <Title order={2}>
          <IconShoppingCart /> Your Cart
        </Title>

        <Space h={'md'} />

        {/* Component Data */}
        <Stack>
          {/* Scroll Area for Cart Items */}
          <ScrollArea>
            {/* Sub component goes here... */}
            <Stack>{renderItemList}</Stack>
          </ScrollArea>

          {/* Cart Action Buttons */}
          <Group position="right">
            <Button leftIcon={<IconCheckbox />} color="green">
              Checkout
            </Button>
          </Group>

          <Divider />
        </Stack>

        <Space h={'md'} />
      </Paper>
    </>
  );
}
