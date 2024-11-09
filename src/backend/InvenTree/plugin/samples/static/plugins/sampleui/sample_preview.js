export function getTemplatePreview({ featureContext, pluginContext }) {
    const { ref } = featureContext;
    console.log("Template preview feature was called with", featureContext, pluginContext);

    featureContext.registerHandlers({
      updatePreview: (...args) => {
        console.log("updatePreview", args);
      }
    });

    ref.innerHTML = "<h1>Hello world</h1>";
  }
