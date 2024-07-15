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
 * @param page - Page object from test
 * @param {TestSetting} setting - Setting to change, including desired new state
 */
export const setGlobalSetting = async (page, setting: TestSetting) => {
  const startUrl = new URL(page.url());
  const startPath = `.${startUrl.pathname}`;

  if (`${baseUrl}/settings/system/${setting.slug}` !== startPath) {
    await page.goto(`${baseUrl}/settings/system/${setting.slug}`);
    await page.getByText('System Settings').waitFor();
  }

  if (setting.isToggle) {
    await setToggleSetting(page, setting);
  } else {
    await setTextSetting(page, setting);
  }
};

/**
 * Sets all given global settings to the values provided
 * @param page - Page object from test
 * @param {TestSetting[]} settings - Array of settings to change
 */
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

/**
 *
 * @param page - Page object from test
 * @param {TestSetting} setting - Setting to change, including desired new state
 */
const setToggleSetting = async (page, setting: TestSetting) => {
  await page
    .getByTestId(setting.key)
    .locator('input')
    .evaluate((input: any, setting: TestSetting) => {
      if (input.checked !== setting.state) {
        input.click();
      }
    }, setting);
  await page.getByText(`Setting ${setting.key} updated successfully`);
};

/**
 * Set a setting that's considered a string in the API
 * This includes choice-based settings.
 * @param page
 * @param setting
 */
const setTextSetting = async (page, setting: TestSetting) => {
  let updated = true;

  await page
    .getByTestId(setting.key)
    .locator('button')
    .evaluate((input: any) => {
      input.click();
    });

  await page.getByText('Edit Setting').waitFor();
  const text = page.locator(
    'input[type=string], input[aria-label="number-field-value"]'
  );

  if (await text.isVisible()) {
    console.log("IS TEXT'Y");
    const value = await text.evaluate((node) => node.getAttribute('value'));
    if (value != setting.state) {
      // Fill out the text field
      await text.fill(String(setting.state));
      await page.getByRole('button', { name: 'Submit' }).click();
    } else {
      // No updates made
      updated = false;
      await page.getByRole('button', { name: 'Cancel' }).click();
    }
  } else {
    // Not a text field
    const choice = await page
      .locator('input[aria-label="choice-field-value"]')
      .isVisible();

    if (choice) {
      // It is a choice field, open the dropdown
      await page.click('input[aria-label="choice-field-value"]');
      await page.locator('div[role="listbox"]').waitFor();

      if (setting.state === null || setting.state === undefined) {
        // Choice should be one without a value
        const noValue = page
          .locator(
            'div[role="listbox"] div[role="option"]:not([value]), div[role="listbox"] div[role="option"][value=""]'
          )
          .first();
        // See if the value is already selected.
        // If you re-select a value on Mantine selects, the value is de-selected
        const selected = await noValue.evaluate(
          (node) => node.getAttribute('aria-selected') === 'true'
        );
        let btnName = 'Submit';
        if (selected) {
          updated = false;
          // Just close the dropdown
          await page.click('input[aria-label="choice-field-value"]');
          btnName = 'Cancel';
        } else {
          // Select the first option
          await noValue.click();
        }
        // Wait for the dropdown to close
        await page.locator('div[role="listbox"]').waitFor({ state: 'hidden' });
        await page.getByRole('button', { name: btnName }).click();
      } else {
        // Click the drowndown matching the supplied state
        await page.click(`div[role="option"][value="${setting.state}"]`);
        await page.locator('div[role="listbox"]').waitFor({ state: 'hidden' });
        await page.getByRole('button', { name: 'Submit' }).click();
      }
    }
  }
  await page.getByText('Edit Setting').waitFor({ state: 'hidden' });

  if (updated) {
    await page
      .getByText(`Setting ${setting.key} updated successfully`)
      .waitFor();
  }
};
