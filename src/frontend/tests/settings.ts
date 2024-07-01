import { baseUrl } from './defaults';

export type TestSetting = {
  slug: string;
  key: string;
  state: any;
  isToggle?: boolean;
};

type SettingsMap = {
  [key: string]: TestSetting[];
};

/**
 * Sets any given global setting to the value provided
 */
export const setGlobalSetting = async (page, setting: TestSetting) => {
  await page.goto(`${baseUrl}/settings/system/${setting.slug}`);
  await page.getByText('System Settings').waitFor();

  if (setting.isToggle) {
    await setToggleSetting(page, setting);
  } else {
    await setTextSetting(page, setting);
  }
};

export const setGlobalSettings = async (page, settings: TestSetting[]) => {
  const sorted = settings.sort((a, b) => {
    return a.slug.localeCompare(b.slug);
  });

  const pages: SettingsMap = {};

  for (const elem of sorted) {
    if (!pages[elem.slug]) {
      pages[elem.slug] = [elem];
    } else {
      pages[elem.slug].push(elem);
    }
  }

  for (const [key, value] of Object.entries(pages)) {
    await page.goto(`${baseUrl}/settings/system/${key}`);
    await page.getByText('System Settings').waitFor();

    for (const setting of value) {
      if (setting.isToggle) {
        await setToggleSetting(page, setting);
      } else {
        await setTextSetting(page, setting);
      }
    }
  }
};

const setToggleSetting = async (page, setting: TestSetting) => {
  await page
    .getByTestId(setting.key)
    .locator('input')
    .evaluate((input: any, setting: TestSetting) => {
      if (input.checked !== setting.state) {
        input.click();
      }
    }, setting);
};

const setTextSetting = async (page, setting: TestSetting) => {
  await page
    .getByTestId(setting.key)
    .locator('button')
    .evaluate((input: any) => {
      input.click();
    });

  await page.getByText('Edit Setting').waitFor();
  await page.locator('input[type=string]').fill(setting.state);
  await page.getByRole('button', { name: 'Submit' }).click();
};
