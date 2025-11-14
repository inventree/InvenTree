import { t } from '@lingui/core/macro';
import { TextInput, Tooltip } from '@mantine/core';
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

  const [textValue, setTextValue] = useState<string>(value || '');

  const onTextChange = useCallback(
    (value: any) => {
      setTextValue(value);
      onChange(value);
    },
    [onChange]
  );

  useEffect(() => {
    setTextValue(value || '');
  }, [value]);

  // Construct a "right section" for the text field
  const textFieldRightSection: ReactNode = useMemo(() => {
    if (definition.rightSection) {
      // Use the specified override value
      return definition.rightSection;
    } else if (textValue) {
      if (!definition.required && !definition.disabled) {
        // Render a button to clear the text field
        return (
          <Tooltip label={t`Clear`} position='top-end'>
            <IconX
              aria-label={`text-field-${fieldName}-clear`}
              size='1rem'
              color='red'
              onClick={() => onTextChange('')}
            />
          </Tooltip>
        );
      }
    } else if (
      !textValue &&
      definition.placeholder &&
      placeholderAutofill &&
      !definition.disabled
    ) {
      return (
        <Tooltip label={t`Accept suggested value`} position='top-end'>
          <IconCopyCheck
            aria-label={`text-field-${fieldName}-accept-placeholder`}
            size='1rem'
            color='green'
            onClick={() => onTextChange(definition.placeholder)}
          />
        </Tooltip>
      );
    }
  }, [placeholderAutofill, definition, textValue]);

  return (
    <TextInput
      {...definition}
      ref={field.ref}
      id={fieldId}
      aria-label={`text-field-${field.name}`}
      type={definition.field_type}
      value={textValue || ''}
      error={definition.error ?? error?.message}
      radius='sm'
      onChange={(event) => onTextChange(event.currentTarget.value)}
      onBlur={(event) => {
        if (event.currentTarget.value != textValue) {
          onTextChange(event.currentTarget.value);
        }
      }}
      onKeyDown={(event) => {
        if (event.code === 'Enter') {
          // Bypass debounce on enter key
          onTextChange(event.currentTarget.value);
        }
        onKeyDown(event.code);
      }}
      rightSection={textFieldRightSection}
    />
  );
}
