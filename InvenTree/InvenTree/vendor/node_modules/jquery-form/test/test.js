/* global chai, scriptCount */

'use strict';

// helper method
var arrayCount = function(arr, key) {
	var count = 0;
	for (var i = 0; i < arr.length; i++) {
		if (arr[i].name === key) {
			count++;
		}
	}
	return count;
};

// helper method
var arrayValue = function(arr, key) {
	for (var i = 0; i < arr.length; i++) {
		if (arr[i].name === key) {
			return arr[i].value;
		}
	}
	return undefined;
};


var assert = chai.assert;
var fixture;

describe('form', function() {
	before(function() {
		fixture = $('#main').html();
	});

	beforeEach(function() {
		$('#main').html(fixture);
	});


	it('"action" and "method" form attributes', function() {
		var f = $('#form1');
		assert.strictEqual(f.attr('action'), 'ajax/text.html', 'form "action"');
		assert.strictEqual(f.attr('method'), 'get', 'form "method"');
	});

	it('formToArray: multi-select', function() {
		var a = $('#form1').formToArray();
		assert.strictEqual(a.constructor, Array, 'type check');
		assert.strictEqual(a.length, 13, 'array length');
		assert.strictEqual(arrayCount(a, 'Multiple'), 3, 'multi-select');
	});

	it('formToArray: "action" and "method" inputs', function() {
		var a = $('#form1').formToArray();
		assert.strictEqual(a.constructor, Array, 'type check');
		assert.strictEqual(arrayValue(a, 'action'), '1', 'input name=action');
		assert.strictEqual(arrayValue(a, 'method'), '2', 'input name=method');
	});

	it('formToArray: semantic test', function() {
		var formData = $('#form2').formToArray(true);
		var testData = ['a','b','c','d','e','f'];
		for (var i = 0; i < 6; i++) {
			assert.strictEqual(formData[i].name, testData[i], 'match value at index=' + i);
		}
	});

	it('formToArray: text promotion for missing value attributes', function() {
		var expected = [
			{ name: 'A', value: ''},
			{ name: 'B', value: 'MISSING_ATTR'},
			{ name: 'C', value: ''},
			{ name: 'C', value: 'MISSING_ATTR'}
		];
		var a = $('#form6').formToArray(true);

		// verify all the option values
		for (var i = 0; i < a.length; i++) {
			assert.strictEqual(a[i].name, expected[i].name, 'Name: ' + a[i].name + ' = ' + expected[i].name);
			assert.strictEqual(a[i].value, expected[i].value, 'Value: ' + a[i].value + ' = ' + expected[i].value);
		}
	});

	it('formToArray: outside fields', function() {
		var formData = $('#form10').formToArray();
		assert.strictEqual(formData.length, 2, 'There are two "successful" elements of the form');
	});

	// test string serialization
	it('serialize: param count', function() {
		var s = $('#form1').formSerialize();
		assert.ok(s.constructor == String, 'type check');
		assert.ok(s.split('&').length == 13, 'string array length');
	});

	// test support for input elements not contained within a form
	it('serialize: pseudo form', function() {
		var s = $('#pseudo *').fieldSerialize();
		assert.ok(s.constructor == String, 'type check');
		assert.ok(s.split('&').length == 3, 'string array length');
	});


	// test resetForm
	it('resetForm (text input)', function() {
		var $el = $('#form1 input[name=Name]');
		var val = $el.val();
		assert.ok('MyName1' == val, 'beforeSubmit: ' + val);
		$el.val('test');
		val = $el.val();
		assert.ok('test' == $el.val(), 'update: ' + val);
		$('#form1').resetForm();
		val = $el.val();
		assert.ok('MyName1' == val, 'success: ' + val);
	});

	// test resetForm
	it('resetForm (select)', function() {
		var $el = $('#form1 select[name=Single]');
		var val = $el.val();
		assert.ok('one' == val, 'beforeSubmit: ' + val);
		$el.val('two');
		val = $el.val();
		assert.ok('two' == $el.val(), 'update: ' + val);
		$('#form1').resetForm();
		val = $el.val();
		assert.ok('one' == val, 'success: ' + val);
	});

	// test resetForm
	it('resetForm (textarea)', function() {
		var $el = $('#form1 textarea');
		var val = $el.val();
		assert.ok('This is Form1' == val, 'beforeSubmit: ' + val);
		$el.val('test');
		val = $el.val();
		assert.ok('test' == val, 'udpate: ' + val);
		$('#form1').resetForm();
		val = $el.val();
		assert.ok('This is Form1' == val, 'success: ' + val);
	});

	// test resetForm
	it('resetForm (checkbox)', function() {
		var el = $('#form1 input:checkbox:checked')[0];
		var val = el.value;
		assert.ok(el.checked, 'beforeSubmit: ' + el.checked);
		el.checked = false;
		assert.ok(!el.checked, 'update: ' + el.checked);
		$('#form1').resetForm();
		assert.ok(el.checked, 'success: ' + el.checked);
	});

	// test resetForm
	it('resetForm (radio)', function() {
		var el = $('#form1 input:radio:checked')[0];
		var val = el.value;
		assert.ok(el.checked, 'beforeSubmit: ' + el.checked);
		el.checked = false;
		assert.ok(!el.checked, 'update: ' + el.checked);
		$('#form1').resetForm();
		assert.ok(el.checked, 'success: ' + el.checked);
	});


	// test clearForm
	it('clearForm (text input)', function() {
		var $el = $('#form1 input[name=Name]');
		var val = $el.val();
		assert.ok('MyName1' == val, 'beforeSubmit: ' + val);
		$('#form1').clearForm();
		val = $el.val();
		assert.ok('' == val, 'success: ' + val);
	});

	// test clearForm
	it('clearForm (select)', function() {
		var $el = $('#form1 select[name=Single]');
		var val = $el.val();
		assert.ok('one' == val, 'beforeSubmit: ' + val);
		$('#form1').clearForm();
		val = $el.val();
		assert.ok(!val, 'success: ' + val);
	});

	// test clearForm; here we're testing that a hidden field is NOT cleared
	it('clearForm: (hidden input)', function() {
		var $el = $('#form1 input:hidden');
		var val = $el.val();
		assert.ok('hiddenValue' == val, 'beforeSubmit: ' + val);
		$('#form1').clearForm();
		val = $el.val();
		assert.ok('hiddenValue' == val, 'success: ' + val);
	});


	// test clearForm; here we're testing that a submit element is NOT cleared
	it('clearForm: (submit input)', function() {
		var $el = $('#form1 input:submit');
		var val = $el.val();
		assert.ok('Submit1' == val, 'beforeSubmit: ' + val);
		$('#form1').clearForm();
		val = $el.val();
		assert.ok('Submit1' == val, 'success: ' + val);
	});

	// test clearForm
	it('clearForm (checkbox)', function() {
		var el = $('#form1 input:checkbox:checked')[0];
		assert.ok(el.checked, 'beforeSubmit: ' + el.checked);
		$('#form1').clearForm();
		assert.ok(!el.checked, 'success: ' + el.checked);
	});

	// test clearForm
	it('clearForm (radio)', function() {
		var el = $('#form1 input:radio:checked')[0];
		assert.ok(el.checked, 'beforeSubmit: ' + el.checked);
		$('#form1').clearForm();
		assert.ok(!el.checked, 'success: ' + el.checked);
	});

	// test ajaxSubmit target update
	it('ajaxSubmit: target == String', function() {
		$('#targetDiv').empty();
		// stop();
		var opts = {
			target: '#targetDiv',
			success: function() { // post-callback
				assert.ok(true, 'post-callback');
				assert.ok($('#targetDiv').text().match('Lorem ipsum'), 'targetDiv updated');
				// start();
			}
		};

		// expect(2);
		$('#form3').ajaxSubmit(opts);
	});

	// test passing jQuery object as the target
	it('ajaxSubmit: target == jQuery object', function() {
		// stop();
		var target = $('#targetDiv');
		target.empty();

		var opts = {
			target: target,
			success: function(responseText) { // post-callback
				assert.ok(true, 'post-callback');
				assert.ok($('#targetDiv').text().match('Lorem ipsum'), 'targetDiv updated');
				// start();
			}
		};

		// expect(2);
		$('#form2').ajaxSubmit(opts);
	});

	// test passing DOM element as the target
	it('ajaxSubmit: target == DOM element', function() {
		// stop();
		$('#targetDiv').empty();
		var el = $('#targetDiv')[0];

		var opts = {
			target: '#targetDiv',
			success: function(responseText) { // post-callback
				assert.ok(true, 'post-callback');
				assert.ok($('#targetDiv').text().match('Lorem ipsum'), 'targetDiv updated');
				// start();
			}
		};

		// expect(2);
		$('#form2').ajaxSubmit(opts);
	});

	// test simulated $.load behavior
	it('ajaxSubmit: load target with scripts', function() {
		// stop();
		$('#targetDiv').empty();

		var opts = {
			target: '#targetDiv',
			url:	'ajax/doc-with-scripts.html?' + new Date().getTime(),
			success: function(responseText) { // post-callback
				assert.ok(true, 'success-callback');
				assert.ok($('#targetDiv').text().match('Lorem ipsum'), 'targetDiv updated');
				assert.ok(typeof unitTestVariable1 != 'undefined', 'first script block executed');
				assert.ok(typeof unitTestVariable2 != 'undefined', 'second script block executed');
				assert.ok(typeof scriptCount != 'undefined', 'third script block executed');
				assert.ok(scriptCount == 1, 'scripts executed once: ' + scriptCount);
				// start();
			}
		};

		// expect(6);
		$('#form2').ajaxSubmit(opts);
	});

	// test ajaxSubmit pre-submit callback
	it('ajaxSubmit: pre-submit callback', function() {
		var opts = {
			beforeSubmit: function(a, jq) { // pre-submit callback
				assert.ok(true, 'pre-submit callback');
				assert.ok(a.constructor == Array, 'type check array');
				assert.ok(jq.jquery, 'type check jQuery');
				assert.ok(jq[0].tagName.toLowerCase() == 'form', 'jQuery arg == "form": ' + jq[0].tagName.toLowerCase());
			}
		};

		// expect(4);
		$('#form3').ajaxSubmit(opts);
	});

	// test ajaxSubmit post-submit callback for response and status text
	it('ajaxSubmit: post-submit callback', function() {
		// stop();

		var opts = {
			success: function(responseText, statusText) { // post-submit callback
				assert.ok(true, 'post-submit callback');
				assert.ok(responseText.match('Lorem ipsum'), 'responseText');
				assert.ok(statusText == 'success', 'statusText');
				// start();
			}
		};

		// expect(3);
		$('#form3').ajaxSubmit(opts);
	});

	// test ajaxSubmit with function argument
	it('ajaxSubmit: function arg', function() {
		// stop();

		// expect(1);
		$('#form3').ajaxSubmit(function() {
			assert.ok(true, 'callback hit');
			// start();
		});
	});

	// test semantic support via ajaxSubmit's pre-submit callback
	it('ajaxSubmit: semantic test', function() {
		var testData = ['a','b','c','d','e','f'];

		var opts = {
			semantic: true,
			beforeSubmit: function(a, jq) { // pre-submit callback
				assert.ok(true, 'pre-submit callback');
				assert.ok(a.constructor == Array, 'type check');
				assert.ok(jq.jquery, 'type check jQuery');
				for (var i = 0; i < a.length; i++) {
					assert.ok(a[i].name == testData[i], 'match value at index=' + i);
				}
			}
		};

		// expect(9);
		$('#form2').ajaxSubmit(opts);
	});

	// test json datatype
	it('ajaxSubmit: dataType == json', function() {
		// stop();

		var opts = {
			url: 'ajax/json.json',
			dataType: 'json',
			success: function(data, statusText) { // post-submit callback
				// assert that the json data was evaluated
				assert.ok(typeof data == 'object', 'json data type');
				assert.ok(data.name == 'jquery-test', 'json data contents');
				// start();
			}
		};

		// expect(2);
		$('#form2').ajaxSubmit(opts);
	});


	// test script datatype
	it('ajaxSubmit: dataType == script', function() {
		// stop();

		var opts = {
			url: 'ajax/script.txt?' + new Date().getTime(), // don't let ie cache it
			dataType: 'script',
			success: function(responseText, statusText) { // post-submit callback
				assert.ok(typeof formScriptTest == 'function', 'script evaluated');
				assert.ok(responseText.match('formScriptTest'), 'script returned');
				// start();
			}
		};

		// expect(2);
		$('#form2').ajaxSubmit(opts);
	});

	// test xml datatype
	it('ajaxSubmit: dataType == xml', function() {
		// stop();

		var opts = {
			url: 'ajax/test.xml',
			dataType: 'xml',
			success: function(responseXML, statusText) { // post-submit callback
				assert.ok(typeof responseXML == 'object', 'data type xml');
				assert.ok($('test', responseXML).length == 3, 'xml data query');
				// start();
			}
		};

		// expect(2);
		$('#form2').ajaxSubmit(opts);
	});


	// test that args embedded in the action are honored; no real way
	// to assert this so successful callback is used to signal success
	it('ajaxSubmit: existing args in action attr', function() {
		// stop();

		var opts = {
			success: function() { // post-submit callback
				assert.ok(true, 'post callback');
				// start();
			}
		};

		// expect(1);
		$('#form5').ajaxSubmit(opts);
	});

	// test ajaxSubmit using pre-submit callback to cancel submit
	it('ajaxSubmit: cancel submit', function() {

		var opts = {
			beforeSubmit: function(a, jq) {		// pre-submit callback
				assert.ok(true, 'pre-submit callback');
				assert.ok(a.constructor == Array, 'type check');
				assert.ok(jq.jquery, 'type check jQuery');
				return false;		// return false to abort submit
			},
			success: function() {	// post-submit callback
				assert.ok(false, 'should not hit this post-submit callback');
			}
		};

		// expect(3);
		$('#form3').ajaxSubmit(opts);
	});

	// test submitting a pseudo-form
	it('ajaxSubmit: pseudo-form', function() {
		// stop();

		var opts = {
			beforeSubmit: function(a, jq) { // pre-submit callback
				assert.ok(true, 'pre-submit callback');
				assert.ok(a.constructor == Array, 'type check');
				assert.ok(jq.jquery, 'type check jQuery');
				assert.ok(jq[0].tagName.toLowerCase() == 'div', 'jQuery arg == "div"');
			},
			success: function() { // post-submit callback
				assert.ok(true, 'post-submit callback');
				// start();
			},
			// url and method must be provided for a pseudo form since they can
			// not be extracted from the markup
			url:  'ajax/text.html',
			type: 'post'
		};

		// expect(5);
		$('#pseudo').ajaxSubmit(opts);
	});

	// test eval of json response
	it('ajaxSubmit: evaluate response', function() {
		// stop();

		var opts = {
			success: function(responseText) { // post-callback
				assert.ok(true, 'post-callback');
				var data = eval.call(window, '(' + responseText + ')');
				assert.ok(data.name == 'jquery-test', 'evaled response');
				// start();
			},
			url: 'ajax/json.txt'
		};

		// expect(2);
		$('#form2').ajaxSubmit(opts);
	});


	// test pre and post callbacks for ajaxForm
	it('ajaxForm: pre and post callbacks', function() {
		// stop();

		var opts = {
			beforeSubmit: function(a, jq) {	// pre-submit callback
				assert.ok(true, 'pre-submit callback');
				assert.ok(a.constructor == Array, 'type check');
				assert.ok(jq.jquery, 'type check jQuery');
			},
			success: function() {			// post-submit callback
				assert.ok(true, 'post-submit callback');
				// start();
			}
		};

		// expect(4);
		$('#form4').ajaxForm(opts);
		$('#submitForm4')[0].click();		// trigger the submit button
	});

	// test that the value of the submit button is captured
	it('ajaxForm: capture submit element', function() {

		var opts = {
			beforeSubmit: function(a, jq) { // pre-callback
				assert.ok(true, 'pre-callback');
				assert.ok(a.constructor == Array, 'type check');
				assert.ok(jq.jquery, 'type check jQuery');
				assert.ok(arrayValue(a, 'form4inputName') !== null, 'submit button');
			}
		};

		// expect(4);
		$('#form4').ajaxForm(opts);
		$('#submitForm4withName')[0].click();
	});

	// test image submit support
	it('ajaxForm: capture submit image coordinates', function() {

		var opts = {
			beforeSubmit: function(a, jq) { // pre-callback
				assert.ok(true, 'pre-callback');
				assert.ok(a.constructor == Array, 'type check');
				assert.ok(jq.jquery, 'type check jQuery');
				assert.ok(arrayValue(a, 'myImage.x') !== null, 'x coord');
				assert.ok(arrayValue(a, 'myImage.y') !== null, 'y coord');
			}
		};

		// expect(5);
		$('#form4').ajaxForm(opts);
		$('#form4imageSubmit')[0].click();
	});

	// test image submit support
	it('ajaxForm: capture submit image coordinates (semantic=true)', function() {

		var opts = {
			semantic: true,
			beforeSubmit: function(a, jq) { // pre-callback
				assert.ok(true, 'pre-callback');
				assert.ok(a.constructor == Array, 'type check');
				assert.ok(jq.jquery, 'type check jQuery');
				assert.ok(arrayValue(a, 'myImage.x') !== null, 'x coord');
				assert.ok(arrayValue(a, 'myImage.y') !== null, 'y coord');
			}
		};

		// expect(5);
		$('#form4').ajaxForm(opts);
		$('#form4imageSubmit')[0].click();
	});

	// test that the targetDiv gets updated
	it('ajaxForm: update target div', function() {
		$('#targetDiv').empty();
		// stop();

		var opts = {
			target: '#targetDiv',
			beforeSubmit: function(a, jq) { // pre-callback
				assert.ok(true, 'pre-callback');
				assert.ok(a.constructor == Array, 'type check');
				assert.ok(jq.jquery, 'type check jQuery');
			},
			success: function() {
				assert.ok(true, 'post-callback');
				assert.ok($('#targetDiv').text().match('Lorem ipsum'), 'targetDiv updated');
				// start();
			}
		};

		// expect(5);
		$('#form4').ajaxForm(opts);
		$('#submitForm4')[0].click();
	});

	it('"success" callback', function() {
		$('#targetDiv').empty();
		// stop();

		var opts = {
			success: function() {
				assert.ok(true, 'post-callback');
				// start();
			}
		};

		// expect(1);
		$('#form3').ajaxSubmit(opts);
	});

	it('"error" callback', function() {
		$('#targetDiv').empty();
		// stop();

		var opts = {
			url: 'ajax/404.html',
			error: function() {
				assert.ok(true, 'error-callback');
				// start();
			},
			success: function() { // post-submit callback
				assert.ok(false, 'should not hit post-submit callback');
			}
		};

		// expect(1);
		$('#form3').ajaxSubmit(opts);
	});


	it('fieldValue(true)', function() {
		var i;

		assert.ok('5'  == $('#fieldTest input').fieldValue(true)[0], 'input');
		assert.ok('1'  == $('#fieldTest :input').fieldValue(true)[0], ':input');
		assert.ok('5'  == $('#fieldTest input:hidden').fieldValue(true)[0], ':hidden');
		assert.ok('14' == $('#fieldTest :password').fieldValue(true)[0], ':password');
		assert.ok('12' == $('#fieldTest :radio').fieldValue(true)[0], ':radio');
		assert.ok('1'  == $('#fieldTest select').fieldValue(true)[0], 'select');

		var expected = ['8','10'];
		var result = $('#fieldTest :checkbox').fieldValue(true);
		assert.ok(result.length == expected.length, 'result size check (checkbox): ' + result.length + '=' + expected.length);
		for (i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i]);
		}

		expected = ['3','4'];
		result = $('#fieldTest [name=B]').fieldValue(true);
		assert.ok(result.length == expected.length, 'result size check (select-multiple): ' + result.length + '=' + expected.length);
		for (i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i]);
		}
	});

	it('fieldValue(false)', function() {
		var i;

		assert.ok('5'  == $('#fieldTest input').fieldValue(false)[0], 'input');
		assert.ok('1'  == $('#fieldTest :input').fieldValue(false)[0], ':input');
		assert.ok('5'  == $('#fieldTest input:hidden').fieldValue(false)[0], ':hidden');
		assert.ok('14' == $('#fieldTest :password').fieldValue(false)[0], ':password');
		assert.ok('1'  == $('#fieldTest select').fieldValue(false)[0], 'select');

		var expected = ['8','9','10'];
		var result = $('#fieldTest :checkbox').fieldValue(false);
		assert.ok(result.length == expected.length, 'result size check (checkbox): ' + result.length + '=' + expected.length);
		for (i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i]);
		}

		expected = ['11','12','13'];
		result = $('#fieldTest :radio').fieldValue(false);
		assert.ok(result.length == expected.length, 'result size check (radio): ' + result.length + '=' + expected.length);
		for (i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i]);
		}

		expected = ['3','4'];
		result = $('#fieldTest [name=B]').fieldValue(false);
		assert.ok(result.length == expected.length, 'result size check (select-multiple): ' + result.length + '=' + expected.length);
		for (i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i]);
		}
	});

	it('fieldSerialize(true) input', function() {
		var expected = ['C=5', 'D=6', 'F=8', 'F=10', 'G=12', 'H=14'];

		var result = $('#fieldTest input').fieldSerialize(true);
		result = result.split('&');

		assert.ok(result.length == expected.length, 'result size check: ' + result.length + '=' + expected.length);
		for (var i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i] + ' = ' + result[i]);
		}
	});

	it('fieldSerialize(true) :input', function() {
		var expected = ['A=1','B=3','B=4','C=5','D=6','E=7','F=8','F=10','G=12','H=14'];

		var result = $('#fieldTest :input').fieldSerialize(true);
		result = result.split('&');

		assert.ok(result.length == expected.length, 'result size check: ' + result.length + '=' + expected.length);
		for (var i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i] + ' = ' + result[i]);
		}
	});

	it('fieldSerialize(false) :input', function() {
		var expected = ['A=1','B=3','B=4','C=5','D=6','E=7','F=8','F=9','F=10','G=11','G=12','G=13','H=14','I=15','J=16'];

		var result = $('#fieldTest :input').fieldSerialize(false);
		result = result.split('&');

		assert.ok(result.length == expected.length, 'result size check: ' + result.length + '=' + expected.length);
		for (var i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i] + ' = ' + result[i]);
		}
	});

	it('fieldSerialize(true) select-mulitple', function() {
		var expected = ['B=3','B=4'];

		var result = $('#fieldTest [name=B]').fieldSerialize(true);
		result = result.split('&');

		assert.ok(result.length == expected.length, 'result size check: ' + result.length + '=' + expected.length);
		for (var i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i] + ' = ' + result[i]);
		}
	});

	it('fieldSerialize(true) :checkbox', function() {
		var expected = ['F=8','F=10'];

		var result = $('#fieldTest :checkbox').fieldSerialize(true);
		result = result.split('&');

		assert.ok(result.length == expected.length, 'result size check: ' + result.length + '=' + expected.length);
		for (var i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i] + ' = ' + result[i]);
		}
	});

	it('fieldSerialize(false) :checkbox', function() {
		var expected = ['F=8','F=9','F=10'];

		var result = $('#fieldTest :checkbox').fieldSerialize(false);
		result = result.split('&');

		assert.ok(result.length == expected.length, 'result size check: ' + result.length + '=' + expected.length);
		for (var i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i] + ' = ' + result[i]);
		}
	});

	it('fieldSerialize(true) :radio', function() {
		var expected = ['G=12'];

		var result = $('#fieldTest :radio').fieldSerialize(true);
		result = result.split('&');

		assert.ok(result.length == expected.length, 'result size check: ' + result.length + '=' + expected.length);
		for (var i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i] + ' = ' + result[i]);
		}
	});

	it('fieldSerialize(false) :radio', function() {
		var expected = ['G=11','G=12','G=13'];

		var result = $('#fieldTest :radio').fieldSerialize(false);
		result = result.split('&');

		assert.ok(result.length == expected.length, 'result size check: ' + result.length + '=' + expected.length);
		for (var i = 0; i < result.length; i++) {
			assert.ok(result[i] == expected[i], expected[i] + ' = ' + result[i]);
		}
	});

	it('ajaxForm - auto unbind', function() {
		$('#targetDiv').empty();
		// stop();

		var opts = {
			target: '#targetDiv',
			beforeSubmit: function(a, jq) { // pre-callback
				assert.ok(true, 'pre-callback');
			},
			success: function() {
				assert.ok(true, 'post-callback');
				// start();
			}
		};

		// expect(2);
		// multiple binds
		$('#form8').ajaxForm(opts).ajaxForm(opts).ajaxForm(opts);
		$('#submitForm8')[0].click();
	});

	it('ajaxFormUnbind', function() {
		$('#targetDiv').empty();
		// stop();

		var opts = {
			target: '#targetDiv',
			beforeSubmit: function(a, jq) { // pre-callback
				assert.ok(true, 'pre-callback');
			},
			success: function() {
				assert.ok(true, 'post-callback');
				// start();
			}
		};

		// expect(0);
		// multiple binds
		$('#form9').ajaxForm(opts).submit(function() {
			return false;
		});
		$('#form9').ajaxFormUnbind(opts);
		$('#submitForm9')[0].click();

		// setTimeout(start, 500);
	});

	it('naked hash', function() {
		$('#actionTest1').ajaxSubmit({
			beforeSerialize: function($f, opts) {
				assert.ok(true, 'url=' + opts.url);
			}
		});
		assert.ok(true, 'ajaxSubmit passed');
	});
	it('hash only', function() {
		$('#actionTest2').ajaxSubmit({
			beforeSerialize: function($f, opts) {
				assert.ok(true, 'url=' + opts.url);
			}
		});
		assert.ok(true, 'ajaxSubmit passed');
	});
	it('empty action', function() {
		$('#actionTest3').ajaxSubmit({
			beforeSerialize: function($f, opts) {
				assert.ok(true, 'url=' + opts.url);
			}
		});
		assert.ok(true, 'ajaxSubmit passed');
	});
	it('missing action', function() {
		$('#actionTest4').ajaxSubmit({
			beforeSerialize: function($f, opts) {
				assert.ok(true, 'url=' + opts.url);
			}
		});
		assert.ok(true, 'ajaxSubmit passed');
	});

	it('success callback params', function() {
		var $testForm;

		$('#targetDiv').empty();
		// stop();

		if (/^1\.3/.test($.fn.jquery)) {
			// expect(3);
			$testForm = $('#form3').ajaxSubmit({
				success: function(data, status, $form) { // jQuery 1.4+ signature
					assert.ok(true, 'success callback invoked');
					assert.ok(status === 'success', 'status === success');
					assert.ok($form === $testForm, '$form param is valid');
					// start();
				}
			});

		} else {	// if (/^1\.4/.test($.fn.jquery)) {
			// expect(6);
			$testForm = $('#form3').ajaxSubmit({
				success: function(data, status, xhr, $form) { // jQuery 1.4+ signature
					assert.ok(true, 'success callback invoked');
					assert.ok(status === 'success', 'status === success');
					assert.ok(true, 'third arg: ' + typeof xhr != undefined);
					assert.ok(!!xhr != false, 'xhr != false');
					assert.ok(xhr.status, 'xhr.status == ' + xhr.status);
					assert.ok($form === $testForm, '$form param is valid');
					// start();
				}
			});
		}
	});

	it('forceSync', function() {
		$('#targetDiv').empty();
		// stop();

		// expect(2);
		var $testForm = $('#form3').ajaxSubmit({
			forceSync: true,
			success: function(data, status, $form) { // jQuery 1.4+ signature
				assert.ok(true, 'success callback invoked');
				assert.ok(status === 'success', 'status === success');
				// start();
			}
		});
	});

});
