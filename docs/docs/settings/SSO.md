---
title: InvenTree Single Sign On
---

## Single Sign On

InvenTree provides the possibility to use 3rd party services to authenticate users. This functionality makes use of [django-allauth](https://django-allauth.readthedocs.io/en/latest/) and supports a wide array of OpenID and OAuth [providers](https://django-allauth.readthedocs.io/en/latest/socialaccount/providers/index.html).

!!! tip "Provider Documentation"
    There are a lot of technical considerations when configuring a particular SSO provider. A good starting point is the [django-allauth documentation](https://django-allauth.readthedocs.io/en/latest/socialaccount/providers/index.html)

## SSO Configuration

The basic requirements for configuring SSO are outlined below:

1. Enable the required providers in the [config file](../start/config.md#single-sign-on).
1. Create an external *app* with your provider of choice
1. Add the required client configurations in the `SocialApp` app in the [admin interface](../settings/admin.md).
1. Configure the *callback* URL for the external app.
1. Enable SSO for the users in the [global settings](../settings/global.md).
1. Configure [e-mail](../settings/email.md).

### Configuration File

The first step is to ensure that the required provider modules are installed, via your installation [configuration file](../start/config.md#single-sign-on).

There are two variables in the configuration file which define the operation of SSO:

| Key | Description | More Info |
| --- | --- | --- |
| `social_backends` | A *list* of provider backends enabled for the InvenTree instance | [django-allauth docs](https://django-allauth.readthedocs.io/en/latest/installation/quickstart.html) |
| `social_providers` | A *dict* of settings specific to the installed providers | [provider documentation](https://django-allauth.readthedocs.io/en/latest/socialaccount/providers/index.html) |

In the example below, SSO provider modules are activated for *google*, *github* and *microsoft*. Specific configuration options are specified for the *microsoft* provider module:

{% with id="SSO", url="settings/sso_config.png", description="SSO Config" %}
{% include 'img.html' %}
{% endwith %}

!!! info "Provider Module Format"
    Note that the provider modules specified in `social_backends` must be prefixed with `allauth.socialaccounts.providers`

!!! tip "Restart Server"
    As the [configuration file](../start/config.md) is only read when the server is launched, ensure you restart the server after editing the file.

### Create Provider App

The next step is to create an external authentication app with your provider of choice. This step is wholly separate to your InvenTree installation, and must be performed before continuing further.

!!! info "Read the Documentation"
    The [django-allauth documentation](https://django-allauth.readthedocs.io/en/latest/socialaccount/providers/index.html) is a good starting point here. There are also a number of good tutorials online (at least for the major supported SSO providers).

In general, the external app will generate a *key* and *secret* pair - although different terminology may be used, depending on the provider.

### Add Client Configurations

Once your external SSO app has been created, you need to create a new *SocialAccount* client configuration (via the InvenTree admin interface).

#### Create Social Application

In the admin interface, select *Add Social Application*

{% with id="social-add", url="settings/social_account_add.png", description="Add Social Application" %}
{% include 'img.html' %}
{% endwith %}

#### Configure Social Application

Configure the social application entry with the app details:

{% with id="social-configure", url="settings/social_application_configure.png", description="Configure Social Application" %}
{% include 'img.html' %}
{% endwith %}

- Select the *provider* type as required
- Provide a *name* for the application (note that this should match the *name* used for any custom settings provided in the configuration file)
- Add client and secret data for your external SSO app
- Add the *site* which you want to provide access for this SSO app
- Save the new application entry when configuration is finished

!!! warning "Site Selection"
    You *must* assign the new application to at least one available site domain

!!! tip "Fix Your Mistakes"
    You can always return to edit or adjust the social application details later

!!! success "Multiple Applications"
    To provide support for multiple SSO applications, simply repeat this process and create another social application entry

### Configure Callback URL

The external SSO application must be provided with a *callback* URL - a URL by which it can communicate with the InvenTree server. The specific *name* that the external SSO application uses for this callback URL may vary, with some authentication applications referring to it with other names such as *reply* or *redirect*.

In any case, the URL is is specific to your installation and the SSO provider. The general pattern for this URL is: `{% raw %}<hostname>/accounts/<provider>/login/callback/{% endraw %}`.

!!! success "Works for Local Installs"
    Your server does not need to be "public facing" for this to work. For example the URL `http://localhost:1234/accounts/github/login/callback/` would be perfectly valid!

!!! warning "Proxy Support"
    If your InvenTree server is running behind a proxy, you will need to ensure that the "public facing" host address matches the internal host address of the server, and that this host address also matches the configured callback URL

### Enable SSO Settings

Now that the social application is created, you need to enable SSO authentication for the InvenTree server.

In the [settings screen](./global.md), navigate to the *Login Settings* panel. Here you will see the required configuration options to enable SSO:

{% with id="sso-settings", url="settings/sso_settings.png", description="SSO Settings" %}
{% include 'img.html' %}
{% endwith %}

| Setting | Description |
| --- | --- |
| Enable SSO | Enable this option to allow single sign on for user login |
| Enable SSO registration | Allow users to self-register with SSO |
| Auto-fill SSO users | Automatically fill out user account data with information provided by external SSO app |
| Allowed domains | Optionally restrict signup to certain domains |

### Configure Email

Note that [email settings](./email.md) must be correctly configured before SSO will be activated. Ensure that your email setup is correctly configured and operational.

## Security Considerations

You should use SSL for your website if you want to use this feature. Also set your callback-endpoints to `https://` addresses to reduce the risk of leaking user's tokens.

Tokens for authenticating the users to the providers they registered with are saved in the database.
So ensure your database is protected and not open to the internet.

Make sure all users with admin privileges have sufficient passwords - they can read out your client configurations with providers and all auth-tokens from users.

!!! warning "It's a secret!"
    Never share the secret key associated with your InvenTree install!
