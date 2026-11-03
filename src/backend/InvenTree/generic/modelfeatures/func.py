"""Generic model features, declared by model mixin classes."""

from typing import Optional

from django.apps import apps

import structlog

logger = structlog.get_logger('inventree')


class ModelFeatureMixin:
    """Base class for mixins which provide a generic 'feature' to a model.

    Identified with the MODEL_FEATURE attribute. Builtin start with 'org.inventree.i.modelfeatures.', do not use that space in a plugin.

    Example:
        class MyPluginMixin(ModelFeatureMixin, models.Model):
            MODEL_FEATURE = 'com.example.myplugin.my_feature'
    """

    MODEL_FEATURE: Optional[str] = None


_model_features_cache: Optional[dict[str, list[str]]] = None


def collect_model_features(model_class):
    """Collect the generic features declared in the class hierarchy of a model."""
    features = []

    for base in model_class.__mro__:
        feature = base.__dict__.get('MODEL_FEATURE')
        if feature and feature not in features:
            features.append(feature)

    return features


def build_model_features_cache():
    """Build cache of features for all registered models."""
    global _model_features_cache

    _model_features_cache = {
        model._meta.label_lower: collect_model_features(model)
        for model in apps.get_models()
        if issubclass(model, ModelFeatureMixin)
    }
    logger.debug('Built model feature cache for %s models', len(_model_features_cache))
    return _model_features_cache


def clear_model_features_cache():
    """Clear feature cache."""
    global _model_features_cache
    _model_features_cache = None


def get_model_features(model_class) -> list[str]:
    """Return the features supported by model class."""
    if model_class is None or not issubclass(model_class, ModelFeatureMixin):
        return []

    cache = _model_features_cache
    if cache is None:
        cache = build_model_features_cache()

    meta = getattr(model_class, '_meta', None)
    features = cache.get(meta.label_lower) if meta else None

    if features is None:
        # Not a registered model - e.g. an abstract class
        return collect_model_features(model_class)
    return features
