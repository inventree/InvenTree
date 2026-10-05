import type { ApiFormFieldSet, ApiFormFieldType } from '@lib/types/Forms';
import { Accordion, Divider, SimpleGrid, Stack, Text } from '@mantine/core';
import { memo } from 'react';
import type { Control, FieldValues } from 'react-hook-form';
import { ApiFormField } from './ApiFormField';

function NestedObjectFieldComponent({
  control,
  fieldName,
  definition,
  url,
  setFields
}: Readonly<{
  control: Control<FieldValues, any>;
  definition: ApiFormFieldType;
  fieldName: string;
  url?: string;
  setFields?: React.Dispatch<React.SetStateAction<ApiFormFieldSet>>;
}>) {
  return (
    <Accordion defaultValue={null} variant='contained' radius='sm'>
      <Accordion.Item value={'OpenByDefault'}>
        <Accordion.Control icon={definition.icon} style={{ padding: '6px 12px' }}>
          <Text size='xs' fw={600}>{definition.label}</Text>
        </Accordion.Control>
        <Accordion.Panel style={{ padding: '8px 12px' }}>
          <Divider style={{ marginTop: '-4px', marginBottom: '8px' }} />
          <SimpleGrid cols={2} spacing='xs'>
            {Object.entries(definition.children ?? {}).map(
              ([childFieldName, field]) => (
                <ApiFormField
                  key={childFieldName}
                  fieldName={`${fieldName}.${childFieldName}`}
                  definition={field}
                  control={control}
                  url={url}
                  setFields={setFields}
                />
              )
            )}
          </SimpleGrid>
        </Accordion.Panel>
      </Accordion.Item>
    </Accordion>
  );
}

export const NestedObjectField = memo(NestedObjectFieldComponent);
