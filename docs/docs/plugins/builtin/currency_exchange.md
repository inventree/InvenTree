---
title: InvenTree Currency Exchange
---

## InvenTree Currency Exchange

The **InvenTree Currency Exchange** plugin provides a default currency exchange rate provider for InvenTree.

The plugin pulls exchange rate information from the [frankfurter API](https://www.frankfurter.app/) API.

### Activation

This plugin is a *mandatory* plugin, and is always enabled.

### Plugin Settings

This plugin has no configurable settings.

## Usage

This plugin is the default currency exchange provider for InvenTree. It is used to convert between different currencies when displaying prices in the InvenTree user interface. An altertnative currency exchange provider can be configured in the InvenTree settings, but this plugin is always available as a fallback option.

## ExchangeRate.host Plugin

The **ExchangeRate.host** plugin is a variant of the InvenTree Currency Exchange plugin, which uses the [ExchangeRate.host](https://exchangerate.host/) API to fetch exchange rates. It provides similar functionality but with a different data source.

Unlike the InvenTree Currency Exchange plugin, the ExchangeRate.host plugin is not enabled by default. It can be installed and activated as a separate plugin.

Note that this plugin requires an API key from ExchangeRate.host, which can be obtained by signing up on their website. Once you have the API key, you can configure it in the plugin settings.
