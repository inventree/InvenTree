import { t } from '@lingui/core/macro';
import { TextInput, Tooltip } from '@mantine/core';
import { useDebouncedValue } from '@mantine/hooks';
import { IconCopyCheck, IconX } from '@tabler/icons-react';
import {
  type ReactNode,
  useCallback,
  useEffect,
  useId,
  useMemo,
  useState
} from 'react';
import type { FieldValues, UseControllerReturn } from 'react-hook-form';

/*
 * Custom implementation of the mantine <TextInput> component,
 * used for rendering text input fields in forms.
 * Uses a debounced value to prevent excessive re-renders.
 */
export default function TextField({
  controller,
  fieldName,
  definition,
  placeholderAutofill,
  onChange,
  onKeyDown
}: Readonly<{
  controller: UseControllerReturn<FieldValues, any>;
  definition: any;
  fieldName: string;
  placeholderAutofill?: boolean;
  onChange: (value: any) => void;
  onKeyDown: (value: any) => void;
}>) {
  const fieldId = useId();
  const {
    field,
    fieldState: { error }
  } = controller;

  const { value } = useMemo(() => field, [field]);

  const [rawText, setRawText] = useState<string>(value || '');

  const [debouncedText] = useDebouncedValue(rawText, 100);

  useEffect(() => {
    setRawText(value || '');
  }, [value]);

  const onTextChange = useCallback((value: any) => {
    setRawText(value);
  }, []);

  useEffect(() => {
    if (debouncedText !== value) {
      onChange(debouncedText);
    }
  }, [debouncedText]);

  // Construct a "right section" for the text field
  const textFieldRightSection: ReactNode = useMemo(() => {
    if (definition.rightSection) {
      // Use the specified override value
      return definition.rightSection;
    } else if (value) {
      if (!definition.required) {
        // Render a button to clear the text field
        return (
          <Tooltip label={t`Clear`} position='top-end'>
            <IconX size='1rem' color='red' onClick={() => onTextChange('')} />
          </Tooltip>
        );
      }
    } else if (!value && definition.placeholder && placeholderAutofill) {
      return (
        <Tooltip label={t`Accept suggested value`} position='top-end'>
          <IconCopyCheck
            size='1rem'
            color='green'
            onClick={() => onTextChange(definition.placeholder)}
          />
        </Tooltip>
      );
    }
  }, [placeholderAutofill, definition, value]);

  return (
    <TextInput
      {...definition}
      ref={field.ref}
      id={fieldId}
      aria-label={`text-field-${field.name}`}
      type={definition.field_type}
      value={rawText || ''}
      error={definition.error ?? error?.message}
      radius='sm'
      onChange={(event) => onTextChange(event.currentTarget.value)}
      onBlur={(event) => {
        if (event.currentTarget.value != value) {
          onChange(event.currentTarget.value);
        }
      }}
      onKeyDown={(event) => {
        if (event.code === 'Enter') {
          // Bypass debounce on enter key
          onChange(event.currentTarget.value);
        }
        onKeyDown(event.code);
      }}
      rightSection={textFieldRightSection}
    />
  );
}
