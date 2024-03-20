import { Select, SelectItem } from '@mantine/core';
import { useEffect, useState } from 'react';

import { getSupportedLanguages } from '../../contexts/LanguageContext';
import { useLocalState } from '../../states/LocalState';

export function LanguageSelect({ width = 80 }: { width?: number }) {
  const [value, setValue] = useState<string | null>(null);
  const [locale, setLanguage] = useLocalState((state) => [
    state.language,
    state.setLanguage
  ]);
  const [langOptions, setLangOptions] = useState<SelectItem[]>([]);

  // change global language on change
  useEffect(() => {
    if (value === null) return;
    setLanguage(value as string);
  }, [value]);

  // set language on component load
  useEffect(() => {
    const languages = getSupportedLanguages();

    const newLangOptions = Object.keys(languages).map((key) => ({
      value: key,
      label: languages[key as string]
    }));
    setLangOptions(newLangOptions);
    setValue(locale);
  }, [locale]);

  return (
    <Select
      w={width}
      data={langOptions}
      value={value}
      onChange={setValue}
      searchable
    />
  );
}
