export function getTemplateEditor({ featureContext, pluginContext }) {
  const { ref } = featureContext;
  console.log("Template editor feature was called with", featureContext, pluginContext);
  const t = document.createElement("textarea");
  t.id = 'sample-template-editor-textarea';
  t.rows = 25;
  t.cols = 60;

  featureContext.registerHandlers({
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
