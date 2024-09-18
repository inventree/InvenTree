export function getFeature({ renderContext, pluginContext }) {
  const { ref } = renderContext;
  console.log("Template preview feature was called with", renderContext, pluginContext);

  renderContext.registerHandlers({
    updatePreview: (...args) => {
      console.log("updatePreview", args);
    }
  });

  ref.innerHTML = "<h1>Hello world</h1>";
}
