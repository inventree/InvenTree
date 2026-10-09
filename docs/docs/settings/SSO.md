---
title: InvenTree Single Sign On
---

## Single Sign On

InvenTree provides the possibility to use 3rd party services to authenticate users. This functionality makes use of [django-allauth](https://docs.allauth.org/en/latest/) and supports a wide array of OpenID and OAuth [providers](https://docs.allauth.org/en/latest/socialaccount/providers/index.html).

!!! tip "Provider Documentation"
    There are a lot of technical considerations when configuring a particular SSO provider. A good starting point is the [django-allauth documentation](https://docs.allauth.org/en/latest/socialaccount/providers/index.html)

!!! warning "Advanced Users"
    The SSO functionality provided by django-allauth is powerful, but can prove challenging to configure. Please ensure that you understand the implications of enabling SSO for your InvenTree instance. Specific technical details of each available SSO provider are beyond the scope of this documentation - please refer to the [django-allauth documentation](https://docs.allauth.org/en/latest/socialaccount/providers/index.html) for more information.

## SSO Configuration

The basic steps for configuring SSO are:

1. Add the backend for the intended SSO provider(s) in the [config file](../start/config.md#configuration-file) or environment variables.
2. Create an external *app* with the provider of choice
3. Add the required client configurations as a *Social application* in the [Database Admin interface](./db_admin.md).
4. Configure the *callback* URL for the external app.
5. Enable SSO for the users in the [global settings](../settings/global.md).
6. Configure [e-mail](../settings/email.md).

!!! info "Two-step setup"
    Provider modules are enabled in `config.yaml` (or environment variables). Client IDs, secrets, and site assignments are configured there or in the database via the Admin Center or the [Database Admin interface](./db_admin.md).

### Add Provider Backends

The first step is to ensure that the required provider modules are installed, via the installations [configuration file](../start/config.md#single-sign-on).

There are two variables in the configuration file which define the operation of SSO:

{{ configtable() }}
{{ configsetting("INVENTREE_SOCIAL_BACKENDS") }} A *list* of [social provider backends](https://docs.allauth.org/en/latest/installation/quickstart.html) enabled for the InvenTree instance |
{{ configsetting("INVENTREE_SOCIAL_PROVIDERS") }} A *dict* of settings specific to the [installed providers](https://docs.allauth.org/en/latest/socialaccount/providers/index.html) |


In the example below, SSO provider modules are activated for *google*, *github* and *microsoft*. Specific configuration options are specified for the *microsoft* provider module:

{{ image("settings/sso_config.png", "SSO Config") }}

!!! warning "Provider Documentation"
    We do not provide any specific documentation for each provider module. Please refer to the [django-allauth documentation](https://docs.allauth.org/en/latest/socialaccount/providers/index.html) for more information.

As the [configuration file](../start/config.md) is only read when the server is launched, ensure you restart the server after editing the file.

### Create Provider App

The next step is to create an external authentication app with your provider of choice. The documentation for correctly creating and configuring the provider app is not covered here.

!!! warning "External Application"
    The provider application will be created as part of your SSO provider setup. This is *not* the same as the *SocialApp* entry in the InvenTree admin interface.

!!! info "Read the Documentation"
    The [django-allauth documentation](https://docs.allauth.org/en/latest/socialaccount/providers/index.html) is a good starting point here. There are also a number of good tutorials online (at least for the major supported SSO providers).

In general, the external app will generate a *key* and *secret* pair - although different terminology may be used, depending on the provider.

### Add Client Configurations

Once you have added the provider, you need to create a new *Social application* entry in the Admin Center (under Identity Federation / SSO ) or in the [Database Admin interface](./db_admin.md) (under **Social accounts** → **Social applications**).

#### Admin Database Interface

1. Select **Add social application** (top right of the social applications list). Social applications are listed under the **Social accounts** section.

2. Configure the social application entry with the specifics provider details:

{{ image("settings/social_application_configure.png", "Sample Social Application Configuration") }}

- Select the *provider* type as required
- Provide a *name* for the social application (note that this must match the *name* used for any custom settings provided in the configuration file)
- Add client and secret data from your external SSO provider / application
- Add the *site* which you want to provide access for this SSO app
- Save the new entry

!!! warning "Site Selection"
    You *must* assign the new application to at least one available site domain

Multiple SSO applications can be configured by repeating this process and creating multiple entries.

### Configure Callback URL

Most external SSO providers must be provided with a *callback* URL - a URL by which it can communicate with the InvenTree server. The specific *name* that the external SSO application uses for this callback URL may vary, with some authentication applications referring to it with other names such as *reply* or *redirect*.

In any case, the URL is is specific to your installation and the SSO provider. The general pattern for this URL is: `{% raw %}<hostname>/accounts/<provider>/login/callback/{% endraw %}` but can vary. Read the specific provider documentation by django-allauth for exact information.

!!! success "Works for Local Installs"
    Your server does not need to be "public facing" for this to work. For example the URL `http://localhost:1234/accounts/github/login/callback/` would be perfectly valid!

!!! warning "Proxy Support"
    If your InvenTree server is running behind a proxy, you will need to ensure that the "public facing" host address matches the internal host address of the server, and that this host address also matches the configured callback URL

!!! warning "HTTP vs HTTPS"
    If your InvenTree server is running with HTTPS, the callback URL must also be HTTPS. Ensure that you have correctly configured [`LOGIN_DEFAULT_HTTP_PROTOCOL`](../start/config.md#login-options) to match your server configuration..

### Enable SSO Settings

Now that the social application is created, you need to enable SSO authentication for the InvenTree server.

In the [settings screen](./global.md), navigate to the *Login Settings* panel. Here you will see the required configuration options to enable SSO:

{{ image("settings/social_account_add.png", "Database Admin — Social applications section") }}

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("LOGIN_ENABLE_SSO") }}
{{ globalsetting("LOGIN_SIGNUP_SSO_AUTO") }}

### Configure Email

Note that [email settings](./email.md) must be correctly configured before SSO will be activated. Ensure that your email setup is correctly configured and operational.

## SSO Group Sync Configuration

InvenTree has the ability to synchronize groups assigned to each user directly from the IdP. To enable this feature, navigate to the *Login Settings* panel in the [settings screen](./global.md) first. Here, the following options are available:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("LOGIN_ENABLE_SSO_GROUP_SYNC") }}
{{ globalsetting("SSO_GROUP_KEY") }}
{{ globalsetting("SSO_GROUP_MAP") }}
{{ globalsetting("SSO_REMOVE_GROUPS") }}

!!! warning "Remove groups outside of SSO"
    Disabling this feature might cause security issues as groups that are removed in the IdP will stay assigned in InvenTree

### Keycloak OIDC example configuration

!!! tip "Configuration for different IdPs"
    The main challenge in enabling the SSO group sync feature is for the SSO admin to configure the IdP such that the groups are correctly represented in in the Django allauth `extra_data` attribute. The SSO group sync feature has been developed and tested using integrated Keycloak users/groups and OIDC. If you are utilizing this feature using another IdP, kindly consider documenting your configuration steps as well.

Keycloak groups are not sent to the OIDC client by default. To enable such functionality, create a new client scope named `groups` in the Keycloak admin console. For this scope, add a new mapper ('By Configuration') and select 'Group Membership'. Give it a descriptive name and set the token claim name to `groups`.

For each OIDC client that relies on those group, explicitly add the `groups` scope to client scopes. The groups will now be sent to client upon request.

**Note:** A group named `foo` will be displayed as `/foo`. For this reason, the example above recommends using group names like `appname/rolename` which will be sent to the client as `/appname/rolename`.

## Security Considerations

You should use SSL for your website if you want to use this feature. Also set your callback-endpoints to `https://` addresses to reduce the risk of leaking user's tokens.

Tokens for authenticating the users to the providers they registered with are saved in the database.
So ensure your database is protected and not open to the internet.

Make sure all users with admin privileges have sufficient passwords - they can read out your client configurations with providers and all auth-tokens from users.

!!! warning "It's a secret!"
    Never share the secret key associated with your InvenTree install!

## Error Handling

If you encounter an error during the SSO process, the error should be logged in the InvenTree database. You can view the [error log](./logs.md) in the [Admin Center](./admin.md#admin-center) to see the details of the error.
