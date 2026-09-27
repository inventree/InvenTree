/*
 * A minimal OIDC provider, used only by the Playwright e2e suite to exercise
 * real SSO logins without depending on an external identity provider.
 *
 * Started as a 'webServer' entry in playwright.config.ts. The identity it
 * always authenticates as is configured via env vars (set from
 * tests/defaults.ts's `mockSsoUser`, so the test spec and this process agree
 * on the same values) - see tests/pui_sso.spec.ts.
 *
 * oauth2-mock-server auto-approves every /authorize request (no login UI),
 * which is what makes this usable headlessly in CI.
 */
import { Events, OAuth2Server } from 'oauth2-mock-server';

const port = Number(process.env.MOCK_OIDC_PORT ?? 9950);
const host = process.env.MOCK_OIDC_HOST ?? 'localhost';

const claims = {
  sub: process.env.MOCK_OIDC_SUB,
  preferred_username: process.env.MOCK_OIDC_USERNAME,
  email: process.env.MOCK_OIDC_EMAIL,
  email_verified: true,
  given_name: process.env.MOCK_OIDC_FIRST_NAME,
  family_name: process.env.MOCK_OIDC_LAST_NAME
};

const server = new OAuth2Server();
await server.issuer.keys.generate('RS256');

server.service.on(Events.BeforeTokenSigning, (token) => {
  Object.assign(token.payload, claims);
});

server.service.on(Events.BeforeUserinfo, (userInfoResponse) => {
  userInfoResponse.body = { ...claims };
});

await server.start(port, host);
console.log(`Mock OIDC server listening at ${server.issuer.url}`);

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, async () => {
    await server.stop();
    process.exit(0);
  });
}
