import type { APIResponse } from '@playwright/test';

import { createApi } from '../api.js';
import { expect, generateUUID, test } from '../baseFixtures.js';
import { clearTableFilters, loadTab, navigate } from '../helpers.js';
import { doCachedLogin } from '../login.js';

for (const savedFilter of [false, true]) {
  test(`Stock - Consuming builds${savedFilter ? ' with saved filter' : ''}`, async ({
    browser
  }) => {
    const api = await createApi({});
    const stockIds: number[] = [];
    const buildIds: number[] = [];
    let locationId: number | undefined;
    let partId: number | undefined;

    const create = async (url: string, data: object) => {
      const response = await api.post(url, { data });
      expect(response.status(), await response.text()).toBe(201);
      const body = await response.json();
      return Array.isArray(body) ? body[0] : body;
    };

    try {
      const part = await create('part/', {
        name: `Consumed reference ${generateUUID().slice(0, 8)}`,
        assembly: true,
        component: true
      });
      partId = part.pk;
      const parent = await create('stock/', { part: partId, quantity: 10 });
      stockIds.push(parent.pk);

      const builds = [];
      for (let index = 0; index < 2; index++) {
        const build = await create('build/', {
          part: partId,
          quantity: 1,
          title: `Reference test ${index}`
        });
        builds.push(build);
        buildIds.push(build.pk);
      }

      const location = await create('stock/location/', {
        name: `Reference location ${generateUUID().slice(0, 8)}`
      });
      locationId = location.pk;

      // Partial transfers create children; the parent field is read-only.
      const children = [];
      for (const build of [...builds, null]) {
        const response = await api.post('stock/transfer/', {
          data: {
            location: locationId,
            items: [{ pk: parent.pk, quantity: 1 }]
          }
        });
        expect(response.ok(), await response.text()).toBeTruthy();
        const records = await (
          await api.get('stock/', { params: { parent: parent.pk } })
        ).json();
        const child = records.find(
          (record: { pk: number }) => !stockIds.includes(record.pk)
        );
        expect(child).toBeTruthy();
        stockIds.push(child.pk);
        const patch = await api.patch(`stock/${child.pk}/`, {
          data: {
            batch: `Reference-${generateUUID().slice(0, 8)}`,
            consumed_by: build?.pk ?? null
          }
        });
        expect(patch.ok(), await patch.text()).toBeTruthy();
        children.push(await patch.json());
      }

      const unconsumedChild = children[builds.length];
      const page = await doCachedLogin(browser);
      const childRequests: URL[] = [];
      page.on('request', (request) => {
        const url = new URL(request.url());
        if (
          request.method() === 'GET' &&
          url.pathname === '/api/stock/' &&
          url.searchParams.get('parent') === String(parent.pk)
        ) {
          childRequests.push(url);
        }
      });

      // Cover fresh table preferences and a previously saved in-stock filter.
      await page.evaluate((saved) => {
        localStorage.removeItem('inventree-filterset-table-child-stock');
        if (saved)
          localStorage.setItem(
            'inventree-filterset-table-child-stock',
            JSON.stringify([{ name: 'in_stock', value: 'true' }])
          );
      }, savedFilter);
      await navigate(page, `stock/item/${parent.pk}/child-items`);
      await loadTab(page, 'Child Items');
      const header = page.getByRole('columnheader', {
        name: 'Consumed By',
        exact: true
      });
      await expect(header).toBeVisible();

      if (savedFilter) {
        await expect(
          page.getByRole('cell', { name: unconsumedChild.batch, exact: true })
        ).toBeVisible();
        await expect(
          page.getByRole('link', { name: builds[0].reference, exact: true })
        ).toHaveCount(0);
        await page.reload();
        await expect(
          page.getByRole('cell', { name: unconsumedChild.batch, exact: true })
        ).toBeVisible();
        await expect(
          page.getByRole('link', { name: builds[0].reference, exact: true })
        ).toHaveCount(0);
        await clearTableFilters(page);
      }

      for (const [index, build] of builds.entries()) {
        const row = page.getByRole('row').filter({
          has: page.getByRole('cell', {
            name: children[index].batch,
            exact: true
          })
        });
        await expect(row).toBeVisible();
        await expect(
          row.getByRole('link', { name: build.reference, exact: true })
        ).toHaveAttribute(
          'href',
          `/web/manufacturing/build-order/${build.pk}/`
        );
      }

      expect(childRequests.length).toBeGreaterThan(0);
      expect(
        childRequests.every(
          (url) => url.searchParams.get('consumed_by_detail') === 'true'
        )
      ).toBeTruthy();

      const unconsumed = page.getByRole('row').filter({
        has: page.getByRole('cell', {
          name: unconsumedChild.batch,
          exact: true
        })
      });
      await expect(unconsumed).toBeVisible();
      const columnIndex = await header.evaluate((element) =>
        Array.from(element.parentElement!.children).indexOf(element)
      );
      await expect(unconsumed.getByRole('cell').nth(columnIndex)).toBeEmpty();

      if (!savedFilter) {
        await page.getByLabel('table-select-columns').click();
        await page
          .getByRole('checkbox', { name: 'Consumed By', exact: true })
          .uncheck();
        await page.keyboard.press('Escape');
        await page.reload();
        await expect(header).toHaveCount(0);
        await page.getByLabel('table-select-columns').click();
        await page
          .getByRole('checkbox', { name: 'Consumed By', exact: true })
          .check();
        await page.keyboard.press('Escape');
        await page
          .getByRole('link', { name: builds[0].reference, exact: true })
          .click();
        await expect(page).toHaveURL(
          new RegExp(`/manufacturing/build-order/${builds[0].pk}`)
        );
        await navigate(page, `part/${partId}/stock`);
        await expect(header).toHaveCount(0);
        await page.getByLabel('table-select-columns').click();
        await expect(
          page.getByRole('checkbox', { name: 'Consumed By', exact: true })
        ).toHaveCount(0);
      }
    } finally {
      try {
        const cleanupFailures: string[] = [];
        const cleanup = async (response: APIResponse) => {
          if (!response.ok()) cleanupFailures.push(await response.text());
        };

        for (const pk of stockIds.reverse())
          await cleanup(await api.delete(`stock/${pk}/`));
        for (const pk of buildIds) {
          await cleanup(
            await api.post(`build/${pk}/cancel/`, {
              data: {
                remove_allocated_stock: false,
                remove_incomplete_outputs: true
              }
            })
          );
          // Cancellation runs in the worker; wait for its committed state.
          await expect
            .poll(
              async () => (await (await api.get(`build/${pk}/`)).json()).status,
              { timeout: 15000 }
            )
            .toBe(30);
          await cleanup(await api.delete(`build/${pk}/`));
        }

        if (partId) {
          await cleanup(
            await api.patch(`part/${partId}/`, { data: { active: false } })
          );
          await cleanup(await api.delete(`part/${partId}/`));
        }

        if (locationId)
          await cleanup(
            await api.delete(`stock/location/${locationId}/`, {
              data: { delete_stock_items: false, delete_sub_locations: false }
            })
          );

        expect(cleanupFailures).toEqual([]);
      } finally {
        await api.dispose();
      }
    }
  });
}
