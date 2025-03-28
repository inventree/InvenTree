// These tets run before any other tests
// To ensure that we have valid auth caches for each user

import { test } from '../baseFixtures';

import { doCachedLogin } from '../login';

test('Auth - Login - Admin', async ({ browser }) => {
  // Login as admin
  const page = await doCachedLogin(browser, {
    username: 'admin',
    password: 'inventree'
  });
});

test('Auth - Login - All Access', async ({ browser }) => {
  // Login as allacecss
  const page = await doCachedLogin(browser, {
    username: 'allaccess',
    password: 'nolimits'
  });
});
