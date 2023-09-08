import { Select } from '@mantine/core';
import { useEffect, useState } from 'react';

import { Locales, languages } from '../../contexts/LanguageContext';
import { useLocalState } from '../../states/LocalState';

export function LanguageSelect() {
  const [value, setValue] = useState<string | null>(null);
  const [locale, setLanguage] = useLocalState((state) => [
    state.language,
    state.setLanguage
  ]);

  // change global language on change
  useEffect(() => {
    if (value === null) return;
    setLanguage(value as Locales);
  }, [value]);

  // set language on component load
  useEffect(() => {
    setValue(locale);
  }, [locale]);

  return <Select w={80} data={languages} value={value} onChange={setValue} />;
}
