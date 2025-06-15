---
title: Basic Plugin Walkthrough
---

## Attachment Carousel

### Overview
A walkthrough showing how to build a part panel plugin.

By the end of the walkthrough, you will have created a plugin that adds a new part panel to display an image carousel from the images attached to the current part.

![Attachment Carousel in Inventree panel screenshot](../assets/images/plugin/plugin_attachment_carousel.png "Attachment Carousel in Inventree panel screenshot")

#### Prerequisites
This is a basic walkthrough and not a guide on how to code in Python or React. It is presumed you have the following,

* A running Inventree instance
* The [Inventree Plugin Creator](https://github.com/inventree/plugin-creator) installed
* [Visual Studio Code (VS Code)](https://code.visualstudio.com/) (or an IDE of your choosing)
* Basic Python knowledge
* Basic React knowledge
* Optional:
    * Vite knowledge
    * [Mantine UI](https://mantine.dev/) knowledge ([Inventree and Mantine UI](./mixins/ui.md#mantine))


### Creating the Plugin Environment
Create a new empty folder called `Inventree` and open it in `VS Code`. In VS Code launch a new terminal window and run the following command,

``` bash
create-inventree-plugin
```

After the plugin wizard has launched, enter the name as `Attachment Carousel` and fill out the other questions until you reach the plugin structure information questions.

![Plugin Wizard Screenshot](../assets/images/plugin/plugin_wizard.png "Plugin Wizard Screenshot")

At the plugin structure information questions,

* Select `UserInterfaceMixin`
* `Add User Interface Support`
* Select `Custom panel items`
* Select `None` for the `DevOps support`

![Plugin Wizard Screenshot showing mixins](../assets/images/plugin/plugin_wizard_mixins.png "Plugin Wizard Screenshot showing mixins")
![Plugin Wizard Screenshot showing items](../assets/images/plugin/plugin_wizard_items.png "Plugin Wizard Screenshot showing items")

After the Plugin Creator has finished you should have a new project that looks like this,

![VS Code screenshot](../assets/images/plugin/plugin_vscode_layout.png "VS Code screenshot")

#### A Brief Overview of the Environment

`attachment_carousel` contains several files, but the main file is `core.py` which is the Python entry point for the plugin. Once created, this folder will also contain the bundled frontend code and any [static file assets](./index.md#static-files).

`frontend/src` contains the frontend React TypeScript code,
* `App.tsx` - The application component
* `main.tsx` - The standalone development entry point (this is only required for testing)
* `Panel.tsx` - The Inventree panel entry point

### Testing the Plugin Environment

To ensure the environment is working as expected, from the terminal run the development Vite server,

``` Bash
npm run dev
```
This should launch the local development server,

![Vite screenshot](../assets/images/plugin/plugin_vite_running.png "Vite screenshot")

If you browse to the address provided you should see the default plugin website,

![Vite website screenshot](../assets/images/plugin/plugin_vite_dev_site.png "Vite website screenshot")


### Creating the Carousel

Mantine UI provides an easy-to-use [Carousel](https://mantine.dev/x/carousel/) component that will be used in this walkthrough.

As the Mantine UI carousel is not added to the plugin project by default, add it via the terminal,

``` Bash
npm install @mantine/carousel
```

Edit `main.tsx` to add the carousel CSS,

``` TypeScript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import { MantineProvider } from '@mantine/core'
import "@mantine/core/styles.css";
import '@mantine/carousel/styles.css';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <MantineProvider>
      <App />
    </MantineProvider>
  </StrictMode>,
)
```

Edit `App.tsx` to add the relevant carousel code,

``` TypeScript
import { Carousel } from '@mantine/carousel';
import { Image, AspectRatio } from '@mantine/core';

export default function App() {

  const indicators = true
  const loop = true
  const imageUrls = [
    'https://picsum.photos/1920/1080?random=1',
    'https://picsum.photos/1920/1080?random=2',
    'https://picsum.photos/1920/1080?random=3',
    // Add more image URLs here. See https://picsum.photos/ for more information
  ];

  const slides = imageUrls.map((url) => (
    <Carousel.Slide key={url}>
      <Image src={url} />
    </Carousel.Slide>
  ));

  return (
    <AspectRatio ratio={1920 / 1080} >
      <Carousel withIndicators={indicators} loop={loop}>{slides}</Carousel>
    </AspectRatio>
  );
}
```

Run the Vite development environment again and browse to the website. You should now see the Mantine UI carousel.

![Mantine UI carousel screenshot](../assets/images/plugin/plugin_vite_mantine_carousel.png "Mantine UI carousel screenshot")

### Adding The Carousel to an Inventree Panel

As previously mentioned, `Panel.tsx` is the default entry point from the Inventree Python backend. Therefore, change `Panel.tsx` to render our carousel component rather than the example code,

``` TypeScript
import { MantineProvider } from '@mantine/core';
import { createRoot } from 'react-dom/client';
import App from './App';
import '@mantine/carousel/styles.css';

/**
 * Render the AttachmentCarouselPanel component.
 *
 * @param target - The target HTML element to render the panel into
 * @param context - The context object to pass to the panel
 */
export function renderAttachmentCarouselPanel(target: HTMLElement, context: any) {
    createRoot(target).render(
        <MantineProvider theme={context.theme} defaultColorScheme={context.colorScheme}>
            <App />
        </MantineProvider>
    );
}
```

Generate the Vite bundle via terminal,

``` Bash
vite run build --emptyOutDir
```

Depending on how you are running Inventree, [install the plugin](./install.md), enable it, and view the resulting panel,

![Attachment Carousel Screenshot](../assets/images/plugin/plugin_attachment_carousel_icon_wrong.png "Attachment Carousel Screenshot")

!!! info "Tip"
    If you do not see the `Attachment Carousel` panel listed, make sure you have `Enable interface integration` turned on (it is disabled by default)

![Attachment Carousel in Inventree panel screenshot](../assets/images/plugin/plugin_interface_integration.png "Attachment Carousel in Inventree panel screenshot")

### Connecting the Carousel to Inventree Part Attachments via the Frontend

Currently, the panel displays randomly generated images from https://picsum.photos. To make it more useful, we can get the images from files that are attached to the part via a frontend API query.

Install TanStack Query in our project via the terminal

``` Bash
npm install @tanstack/react-query
```

Update `App.tsx` to use TanStack Query and query for all part attachments,

!!! info "More Info"
    By using the `context` api query we do not need to pass an API key or have the user login to perform the API call, it just happens automatically.

``` TypeScript
import { Carousel } from '@mantine/carousel';
import { Image, AspectRatio } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';

export default function Test({ context }: { context: any }) {

  const indicators = true
  const loop = true
  const vaildAttachmentTypes: string[] = ["jpg", "jpeg"] // Add more items to the array if you want to support more file types.
  let imageUrls: string[] = new Array();

  const { data: attachments } = useQuery({
    queryKey: ["attachment"],
    queryFn: async () => {
      const response = await context.api?.get('api/attachment/', {
        params: {
                model_type: context.model,
                model_id: context.id,
                is_file: true,
                limit: 100
              }
      })
      return await response.data.results
    }
  })

  if (attachments) {
    attachments.forEach((element: { attachment: string; filename: string; }) => {
      if (vaildAttachmentTypes.includes(element.filename.split('.').pop() || "")) {
        imageUrls.push(context.globalSettings.getSetting("INVENTREE_BASE_URL") + element.attachment);
      }
    });
  }
  else {
    imageUrls = [""];
  }

  const slides = imageUrls.map((url) => (
    <Carousel.Slide key={url}>
      <Image src={url} />
    </Carousel.Slide>
  ));

  return (
    <AspectRatio ratio={1920 / 1080} >
      <Carousel withIndicators={indicators} loop={loop}>{slides}</Carousel>
    </AspectRatio>
  );
}
```

Upload some appropriately sized images in the specified file type (see code), re-bundle the plugin, and update it in Inventree.

You should now see the carousel displaying images from the attachments on the part. Upload images to different parts and see how the carousel changes based on the part you are viewing.

### Connecting the Carousel to Inventree Part Attachments via the Backend

An alternative to doing the API query on the frontend is to do it via the backend and supply the image URLs via additional context data. The advantage of doing the query this way is the panel can now be shown or hidden based on if any images are found on the part, and the images could also be checked to ensure they are images and not corrupted etc. The downside is there is more backend processing, and the context variable could become quite large when passed to the frontend. Of course, queries could be done on the backend and frontend and not pass the data via the context. It is for the developer of the plugin to decide which approach is best...

Back to the walkthrough, open `core.py` in the `attachment_carousel` folder and make the following changes,

``` Diff
  from plugin import InvenTreePlugin
+ from part.models import Part
+ from common.models import InvenTreeSetting
+ from django.db.models import Q
  from plugin.mixins import SettingsMixin, UserInterfaceMixin

  from . import PLUGIN_VERSION
  ...
  ...
    def get_ui_panels(self, request, context: dict, **kwargs):
        """Return a list of custom panels to be rendered in the InvenTree user interface."""

        panels = []
+       base_url = InvenTreeSetting.get_setting('INVENTREE_BASE_URL')

        # Only display this panel for the 'part' target
        if context.get('target_model') == 'part':

+           part = Part.objects.get(pk=context.get('target_id'))
+           part_attachments = part.attachments
+           attachments = part_attachments.filter(Q(attachment__endswith='.jpg') | Q(attachment__endswith='.jpeg'))

+           attachment_urls = []

+           if attachments.count() > 0:
+               for attachment in attachments:
+                   attachments_urls.append(base_url + '/media/' + attachment.attachment.name)

+           if len(attachment_urls) > 0:
                panels.append({
                    'key': 'attachment-carousel-panel',
                    'title': 'Attachment Carousel',
                    'description': 'Custom panel description',
                    'icon': 'ti:carousel-horizontal:outline',
                    'source': self.plugin_static_file('Panel.js:renderAttachmentCarouselPanel'),
                    'context': {
                        # Provide additional context data to the panel
                        'settings': self.get_settings_dict(),
+                       'attachments': attachment_urls,
                    }
                })

        return panels
```

Now the backend collects the attachment details and passes them to the frontend, whilst also only displaying the panel if attachments are found.

Next, modify `App.tsx` to use this new information,

``` Diff
  import { Carousel } from '@mantine/carousel';
  import { Image, AspectRatio } from '@mantine/core';
- import { useQuery } from '@tanstack/react-query';

  export default function Test({ context }: { context: any }) {

    const indicators = true
    const loop = true
+   const imageUrls: string[] = context.context.attachments;
-   const vaildAttachmentTypes: string[] = ["jpg", "jpeg"] // Add more items to the array if you want to support more file types.
-   let imageUrls: string[] = new Array();
-   const { data: attachments } = useQuery({
-     queryKey: ["attachment"],
-     queryFn: async () => {
-       const response = await context.api?.get('api/attachment/', {
-         params: {
-                 model_type: context.model,
-                 model_id: context.id,
-                 is_file: true,
-                 limit: 100
-               }
-       })
-       return await response.data.results
-     }
-   })

-   if (attachments) {
-     attachments.forEach((element: { attachment: string; filename: string; }) => {
-       if (vaildAttachmentTypes.includes(element.filename.split('.').pop() || "")) {
-         imageUrls.push(context.globalSettings.getSetting("INVENTREE_BASE_URL") + element.attachment);
-       }
-     });
-   }
-   else {
-     imageUrls = [""];
-   }

    const slides = imageUrls.map((url) => (
      <Carousel.Slide key={url}>
        <Image src={url} />
      </Carousel.Slide>
    ));

    return (
      <AspectRatio ratio={1920 / 1080} >
        <Carousel withIndicators={indicators} loop={loop}>{slides}</Carousel>
      </AspectRatio>
    );
  }

```

### Changing the Panel Icon

Inventree uses [Tabler icons](https://tabler.io/icons) and it is easy to change the panel's icon to something more suitable. Simply find the [Tabler icon](https://tabler.io/icons) you would like and update the icon reference in `core.py`,

``` Diff
panels.append({
    'key': 'attachment-carousel-panel',
    'title': 'Attachment Carousel',
    'description': 'Custom panel description',
-   'icon': 'ti:mood-smile:outline',
+   'icon': 'ti:carousel-horizontal:outline',
    'source': self.plugin_static_file('Panel.js:renderAttachmentCarouselPanel'),
    'context': {
        # Provide additional context data to the panel
        'settings': self.get_settings_dict(),
        'attachments': attachment_urls,
    }
})
```

![Attachment Carousel in Inventree panel with updated icon screenshot](../assets/images/plugin/plugin_attachment_carousel_icon.png "Attachment Carousel in Inventree panel screenshot updated icon screenshot")

### Adding Plugin Admin Options

Plugin settings can be added to allow the end user to change certain settings from the admin panel.

In this walkthrough add settings to allow the user to show/hide the `indicators` (the pill buttons at the bottom of the panel) and enable/disable `loop` functionality (the ability to loop through all the images).

Make the following changes to `core.py`,

``` Diff
...
  SETTINGS = {
      # Define your plugin settings here...
-     'CUSTOM_VALUE': {
-         'name': 'Custom Value',
-         'description': 'A custom value',
-         'validator': int,
-         'default': 42,
-     }
+     'ENABLE_INDICATORS': {
+         'name': 'Indicators',
+         'description': 'Show navigation indicators',
+         'validator': bool,
+         'default': True,
+     },
+     'ENABLE_LOOP': {
+         'name': 'Loop',
+         'description': 'Loop through images',
+         'validator': bool,
+         'default': True,
+     }
}
...
```

Edit `App.tsx` to use the new options,

``` Diff
export default function App({ context }: { context: any }) {

- const indicators = true
- const loop = false
+ const indicators = context.context.settings.ENABLE_INDICATORS
+ const loop = context.context.settings.ENABLE_LOOP
  const imageUrls: string[] = context.context.attachments;
```

Now you have two options that change the behaviour of the plugin.

![Attachment Carousel Inventree Admin interface screenshot](../assets/images/plugin/plugin_admin_interface.png "Attachment Carousel Inventree Admin interface screenshot")

### Using CSS to Enhance the User Experience

When `loop` is set to `disabled` the carousel still displays the previous and next buttons for the first and last images. This behaviour can be changed with some CSS.

Create a new file called `App.css` and add the following,

``` CSS
.control {
  &[data-inactive] {
    opacity: 0;
    cursor: default;
  }
}

.control:hover {
  &[data-inactive] {
    opacity: 0;
    cursor: default;
  }
}
```

Vite will automatically bundle all the CSS files in the project to `static/assets/style.css`, but it will not automatically add a reference to the stylesheet. Add the reference manually to `Panel.tsx`,

``` TypeScript
...
export function renderAttachmentCarouselPanel(target: HTMLElement, context: any) {

    createRoot(target).render(
        <>
            <link rel="stylesheet" href={`${context.host}static/plugins/${context.context.slug}/assets/style.css`} />
            <QueryClientProvider client={queryClient}>
                <MantineProvider theme={context.theme} defaultColorScheme={context.colorScheme}>
                    <App context={context} />
                </MantineProvider>
            </QueryClientProvider>
        </>
    );
}
```

The reference requires the host and the [plugin-name](./index.md##static-files). Rather than statically coding these references, the host reference may be retrieved via the context and the plugin-name may be passed via additional context data. In this example it is passed as the `slug`, as by default the slug is the plugin name. Add this additional context data via `core.py`,

``` diff
panels.append({
    'key': 'attachment-carousel-panel',
    'title': 'Attachment Carousel',
    'description': 'Custom panel description',
    'icon': 'ti:carousel-horizontal:outline',
    'source': self.plugin_static_file('Panel.js:renderAttachmentCarouselPanel'),
    'context': {
        # Provide additional context data to the panel
        'settings': self.get_settings_dict(),
        'attachments': attachments_info,
+       'slug': self.SLUG
    }
})
```

Update the plugin in Inventree and the walkthrough is complete!

![Attachment Carousel in Inventree panel screenshot](../assets/images/plugin/plugin_attachment_carousel.png "Attachment Carousel in Inventree panel screenshot")
