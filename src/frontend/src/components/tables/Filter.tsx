/**
 * Interface for the table filter choice
 */
export type TableFilterChoice = {
  value: string;
  label: string;
};

/**
 * Interface for the table filter,
 */
export type TableFilter = {
  name: string;
  label: string;
  description?: string;
  type?: string;
  choices?: TableFilterChoice[];
  choiceFunction?: () => TableFilterChoice[];
  defaultValue?: any;
  value?: any;
};
