---
title: Transition Mixin
---

## TransitionMixin

The `TransitionMixin` allows plugins to provide custom state transition logic for InvenTree models.

Model types which support transition between different "states" (e.g. orders), can be extended to support custom transition logic by implementing the `TransitionMixin` class.

This allows for custom functionality to be executed when a state transition occurs, such as sending notifications, updating related models, or performing other actions.

Additionally, the mixin can be used to prevent certain transitions from occurring, or to modify the transition logic based on custom conditions.

!!! info "More Info"
    For more information on this plugin mixin, refer to the InvenTree source code. [A working example is available as a starting point]({{ sourcefile("/src/backend/InvenTree/plugin/samples/integration/transition.py") }}).
