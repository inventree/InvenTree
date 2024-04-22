// eslint.config.js
import js from "@eslint/js";
import globals from "globals";

export default [
  js.configs.recommended,
  {
    languageOptions: {
      ecmaVersion: 12,
      sourceType: "module",
      globals: {
        ...globals.browser,
        ...globals.es2021,
        ...globals.jquery,
      }
    },
    rules: {
      "no-var": "off",
      "guard-for-in": "off",
      "no-trailing-spaces": "off",
      "camelcase": "off",
      "padded-blocks": "off",
      "prefer-const": "off",
      "max-len": "off",
      "require-jsdoc": "off",
      "valid-jsdoc": "off",
      "no-multiple-empty-lines": "off",
      "comma-dangle": "off",
      "no-unused-vars": "off",
      "no-useless-escape": "off",
      "prefer-spread": "off",
      "indent": ["error", 4]
    },
    linterOptions: {
      reportUnusedDisableDirectives: "off"
  }
  }
];
