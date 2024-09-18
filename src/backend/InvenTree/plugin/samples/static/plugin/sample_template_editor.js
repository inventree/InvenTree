export function getFeature({ renderContext, pluginContext }) {
  const { ref } = renderContext;
  console.log("Template editor feature was called with", renderContext, pluginContext);
  const t = document.createElement("textarea");
  t.rows = 25;
  t.cols = 60;

  renderContext.registerHandlers({
    setCode: (code) => {
      t.value = code;
    },
    getCode: () => {
      return t.value;
    }
  });

  ref.innerHTML = "";
  ref.appendChild(t);
}
