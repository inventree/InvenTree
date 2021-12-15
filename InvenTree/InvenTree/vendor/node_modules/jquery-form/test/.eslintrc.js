module.exports = {
	"env": {
		"browser": true,
		"jquery": true,
		"node": true,
		"mocha": true
	},
	"parserOptions": {
		"ecmaVersion": 5,
		"sourceType": "script"
	},
	"rules": {
		"comma-spacing": "warn",
		"eqeqeq": "warn",
		"newline-after-var": "off",
		"newline-before-return": "off",
		"no-multi-spaces": "warn",
		"object-curly-spacing": [
			"warn",
			"never",
			{
				"arraysInObjects": true,
				"objectsInObjects": true
			}
		],
		"strict": [
			"warn",
			"global"
		],
		"yoda": "warn"
	}
};
