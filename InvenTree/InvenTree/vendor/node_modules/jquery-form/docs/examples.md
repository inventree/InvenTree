---
---

## Examples

### ajaxForm

The following code controls the HTML form beneath it. It uses `ajaxForm` to bind the form and demonstrates how to use pre- and post-submit callbacks.

```javascript
// prepare the form when the DOM is ready
$(document).ready(function() {
  var options = {
    target:        '#output1',   // target element(s) to be updated with server response
    beforeSubmit:  showRequest,  // pre-submit callback
    success:       showResponse  // post-submit callback

    // other available options:
    //url:       url         // override for form's 'action' attribute
    //type:      type        // 'get' or 'post', override for form's 'method' attribute
    //dataType:  null        // 'xml', 'script', or 'json' (expected server response type)
    //clearForm: true        // clear all form fields after successful submit
    //resetForm: true        // reset the form after successful submit

    // $.ajax options can be used here too, for example:
    //timeout:   3000
  };

  // bind form using 'ajaxForm'
  $('#myForm1').ajaxForm(options);
});

// pre-submit callback
function showRequest(formData, jqForm, options) {
  // formData is an array; here we use $.param to convert it to a string to display it
  // but the form plugin does this for you automatically when it submits the data
  var queryString = $.param(formData);

  // jqForm is a jQuery object encapsulating the form element. To access the
  // DOM element for the form do this:
  // var formElement = jqForm[0];

  alert('About to submit: \n\n' + queryString);

  // here we could return false to prevent the form from being submitted;
  // returning anything other than false will allow the form submit to continue
  return true;
}

// post-submit callback
function showResponse(responseText, statusText, xhr, $form)  {
  // for normal html responses, the first argument to the success callback
  // is the XMLHttpRequest object's responseText property

  // if the ajaxForm method was passed an Options Object with the dataType
  // property set to 'xml' then the first argument to the success callback
  // is the XMLHttpRequest object's responseXML property

  // if the ajaxForm method was passed an Options Object with the dataType
  // property set to 'json' then the first argument to the success callback
  // is the json data object returned by the server

  alert('status: ' + statusText + '\n\nresponseText: \n' + responseText +
    '\n\nThe output div should have already been updated with the responseText.');
}
```

<form id="myForm1" action="http://malsup.com/jquery/form/dummy.php" method="post"><div>
  <input type="hidden" name="Hidden" value="hiddenValue">
  <table>
  <tr><td>Name:</td><td><input name="Name" type="text" value="MyName1"></td></tr>
  <tr><td>Password:</td><td><input name="Password" type="password"></td></tr>
  <tr><td>Multiple:</td><td><select name="Multiple" multiple="multiple">
    <optgroup label="Group 1">
      <option value="one" selected="selected">One</option>
      <option value="two">Two</option>
      <option value="three">Three</option>
    </optgroup>
    <optgroup label="Group 2">
      <option value="four">Four</option>
      <option value="five">Five</option>
      <option value="six">Six</option>
    </optgroup>
  </select></td></tr>
  <tr><td>Single:</td><td><select name="Single">
    <option value="one" selected="selected">One</option>
    <option value="two">Two</option>
    <option value="three">Three</option>
  </select></td></tr>
  <tr><td>Single2:</td><td><select name="Single2">
    <optgroup label="Group 1">
      <option value="A" selected="selected">A</option>
      <option value="B">B</option>
      <option value="C">C</option>
    </optgroup>
    <optgroup label="Group 2">
      <option value="D">D</option>
      <option value="E">E</option>
      <option value="F">F</option>
    </optgroup>
  </select></td></tr>
  <tr><td>Check:</td><td>
    <input type="checkbox" name="Check" value="1">
    <input type="checkbox" name="Check" value="2">
    <input type="checkbox" name="Check" value="3">
  </td></tr>
  <tr><td>Radio:</td><td>
    <input type="radio" name="Radio" value="1">
    <input type="radio" name="Radio" value="2">
    <input type="radio" name="Radio" value="3">
  </td></tr>
  <tr><td>Text:</td><td><textarea name="Text" rows="2" cols="20">This is Form1</textarea></td></tr>
  </table>
  <input type="reset"   name="resetButton " value="Reset">
  <input type="submit"  name="submitButton" value="Submit1">
  <input type="image"   name="submitButton" value="Submit2" src="http://malsup.com/jquery/form/submit.gif">
  <input type="image"   name="submitButton" value="Submit3" src="http://malsup.com/jquery/form/submit.gif">
  <input type="image"   name="submitButton" value="Submit4" src="http://malsup.com/jquery/form/submit.gif">
  <button type="submit" name="submitButton" value="Submit5"><span>submit 5</span></button>
</div></form>

#### Output Div (#output1):
<div id="output1">AJAX response will replace this content.</div>

---

### ajaxSubmit

The following code controls the HTML form beneath it. It uses `ajaxSubmit` to submit the form.
```javascript
// prepare the form when the DOM is ready
$(document).ready(function() {
    var options = {
        target:        '#output2',   // target element(s) to be updated with server response
        beforeSubmit:  showRequest,  // pre-submit callback
        success:       showResponse  // post-submit callback

        // other available options:
        //url:       url         // override for form's 'action' attribute
        //type:      type        // 'get' or 'post', override for form's 'method' attribute
        //dataType:  null        // 'xml', 'script', or 'json' (expected server response type)
        //clearForm: true        // clear all form fields after successful submit
        //resetForm: true        // reset the form after successful submit

        // $.ajax options can be used here too, for example:
        //timeout:   3000
    };

    // bind to the form's submit event
    $('#myForm2').submit(function() {
        // inside event callbacks 'this' is the DOM element so we first
        // wrap it in a jQuery object and then invoke ajaxSubmit
        $(this).ajaxSubmit(options);

        // !!! Important !!!
        // always return false to prevent standard browser submit and page navigation
        return false;
    });
});

// pre-submit callback
function showRequest(formData, jqForm, options) {
    // formData is an array; here we use $.param to convert it to a string to display it
    // but the form plugin does this for you automatically when it submits the data
    var queryString = $.param(formData);

    // jqForm is a jQuery object encapsulating the form element. To access the
    // DOM element for the form do this:
    // var formElement = jqForm[0];

    alert('About to submit: \n\n' + queryString);

    // here we could return false to prevent the form from being submitted;
    // returning anything other than false will allow the form submit to continue
    return true;
}

// post-submit callback
function showResponse(responseText, statusText, xhr, $form)  {
    // for normal html responses, the first argument to the success callback
    // is the XMLHttpRequest object's responseText property

    // if the ajaxSubmit method was passed an Options Object with the dataType
    // property set to 'xml' then the first argument to the success callback
    // is the XMLHttpRequest object's responseXML property

    // if the ajaxSubmit method was passed an Options Object with the dataType
    // property set to 'json' then the first argument to the success callback
    // is the json data object returned by the server

    alert('status: ' + statusText + '\n\nresponseText: \n' + responseText +
        '\n\nThe output div should have already been updated with the responseText.');
}
```

<form id="myForm2" action="http://malsup.com/jquery/form/dummy2.php" method="post"><div>
  <input type="hidden" name="Hidden" value="hiddenValue">
  <table>
    <tr><td>Name:</td><td><input name="Name" type="text" value="MyName2"></td></tr>
    <tr><td>Password:</td><td><input name="Password" type="password"></td></tr>
    <tr><td>Multiple:</td><td><select name="Multiple" multiple="multiple">
      <optgroup label="Group 1">
        <option value="one" selected="selected">One</option>
        <option value="two">Two</option>
        <option value="three">Three</option>
      </optgroup>
      <optgroup label="Group 2">
        <option value="four">Four</option>
        <option value="five">Five</option>
        <option value="six">Six</option>
      </optgroup>
    </select></td></tr>
    <tr><td>Single:</td><td><select name="Single">
      <option value="one" selected="selected">One</option>
      <option value="two">Two</option>
      <option value="three">Three</option>
    </select></td></tr>
    <tr><td>Single2:</td><td><select name="Single2">
      <optgroup label="Group 1">
        <option value="A" selected="selected">A</option>
        <option value="B">B</option>
        <option value="C">C</option>
      </optgroup>
      <optgroup label="Group 2">
        <option value="D">D</option>
        <option value="E">E</option>
        <option value="F">F</option>
      </optgroup>
    </select></td></tr>
    <tr><td>Check:</td><td>
      <input type="checkbox" name="Check" value="1">
      <input type="checkbox" name="Check" value="2">
      <input type="checkbox" name="Check" value="3">
    </td></tr>
    <tr><td>Radio:</td><td>
      <input type="radio" name="Radio" value="1">
      <input type="radio" name="Radio" value="2">
      <input type="radio" name="Radio" value="3">
    </td></tr>
    <tr><td>Text:</td><td><textarea name="Text" rows="2" cols="20">This is Form2</textarea></td></tr>
  </table>
  <input type="reset"   name="resetButton " value="Reset">
  <input type="submit"  name="submitButton" value="Submit1">
  <input type="image"   name="submitButton" value="Submit2" src="http://malsup.com/jquery/form/submit.gif">
</div></form>

#### Output Div (#output2):
<div id="output2">AJAX response will replace this content.</div>


---

### Validation
This section gives several examples of how form data can be validated before it is sent to the server. The secret is in the `beforeSubmit` option. If this pre-submit callback returns false, the submit process is aborted.

The following login form is used for each of the examples that follow. Each example will validate that both the *username* and *password* fields have been filled in by the user.

#### Form Markup:

```html
  <form id="validationForm" action="http://malsup.com/jquery/form/dummy.php" method="post">
    Username: <input type="text" name="username">
    Password: <input type="password" name="password">
    <input type="submit" value="Submit">
  </form>
```

First, we initialize the form and give it a `beforeSubmit` callback function - this is the validation function.

```javascript
// prepare the form when the DOM is ready
$(document).ready(function() {
    // bind form using ajaxForm
    $('#myForm2').ajaxForm( { beforeSubmit: validate } );
});
```

#### Validate Using the `formData` Argument
<form id="validateForm1" action="http://malsup.com/jquery/form/dummy.php" method="post"><div>
    Username: <input type="text" name="username">
    Password: <input type="password" name="password">
    <input type="submit" value="Submit">
</div></form>

```javascript
function validate(formData, jqForm, options) {
  // formData is an array of objects representing the name and value of each field
  // that will be sent to the server;  it takes the following form:
  //
  // [
  //     { name:  username, value: valueOfUsernameInput },
  //     { name:  password, value: valueOfPasswordInput }
  // ]
  //
  // To validate, we can examine the contents of this array to see if the
  // username and password fields have values. If either value evaluates
  // to false then we return false from this method.

  for (var i=0; i < formData.length; i++) {
    if (!formData[i].value) {
      alert('Please enter a value for both Username and Password');
      return false;
    }
  }
  alert('Both fields contain values.');
}
```

#### Validate Using the `jqForm` Argument
<form id="validateForm2" action="http://malsup.com/jquery/form/dummy.php" method="post"><div>
    Username: <input type="text" name="username">
    Password: <input type="password" name="password">
    <input type="submit" value="Submit">
</div></form>

```javascript
function validate(formData, jqForm, options) {
    // jqForm is a jQuery object which wraps the form DOM element
    //
    // To validate, we can access the DOM elements directly and return true
    // only if the values of both the username and password fields evaluate
    // to true

    var form = jqForm[0];
    if (!form.username.value || !form.password.value) {
        alert('Please enter a value for both Username and Password');
        return false;
    }
    alert('Both fields contain values.');
}
```

#### Validate Using the `fieldValue` Method
<form id="validateForm3" action="http://malsup.com/jquery/form/dummy.php" method="post"><div>
    Username: <input type="text" name="username">
    Password: <input type="password" name="password">
    <input type="submit" value="Submit">
</div></form>

```javascript
function validate(formData, jqForm, options) {
    // fieldValue is a Form Plugin method that can be invoked to find the
    // current value of a field
    //
    // To validate, we can capture the values of both the username and password
    // fields and return true only if both evaluate to true

    var usernameValue = $('input[name=username]').fieldValue();
    var passwordValue = $('input[name=password]').fieldValue();

    // usernameValue and passwordValue are arrays but we can do simple
    // "not" tests to see if the arrays are empty
    if (!usernameValue[0] || !passwordValue[0]) {
        alert('Please enter a value for both Username and Password');
        return false;
    }
    alert('Both fields contain values.');
}
```

#### Note
You can find jQuery plugins that deal specifically with field validation on the [jQuery Plugins Page](http://docs.jquery.com/Plugins#Forms).


---

### JSON

This page shows how to handle JSON data returned from the server. The form below submits a message to the server and the server echos it back in JSON format.

#### Form markup:

```html
<form id="jsonForm" action="http://malsup.com/jquery/form/json-echo.php" method="post">
    Message: <input type="text" name="message" value="Hello JSON">
    <input type="submit" value="Echo as JSON">
</form>
```

<form id="jsonForm" action="http://malsup.com/jquery/form/json-echo.php" method="post"><div>
    Message: <input type="text" name="message" value="Hello JSON">
    <input type="submit" value="Echo as JSON">
</div></form>

#### Server code in `json-echo.php`:
```php
<?php  echo '{ "message": "' . $_POST['message'] . '" }';  ?>
```

#### JavaScript:

```javascript
// prepare the form when the DOM is ready
$(document).ready(function() {
    // bind form using ajaxForm
    $('#jsonForm').ajaxForm({
        // dataType identifies the expected content type of the server response
        dataType:  'json',

        // success identifies the function to invoke when the server response
        // has been received
        success:   processJson
    });
});
```

#### Callback function

```javascript
function processJson(data) {
    // 'data' is the json object returned from the server
    alert(data.message);
}
```

---

### XML
This page shows how to handle XML data returned from the server. The form below submits a message to the server and the server echos it back in XML format.

#### Form markup:

```html
<form id="xmlForm" action="http://malsup.com/jquery/form/xml-echo.php" method="post">
  Message: <input type="text" name="message" value="Hello XML">
  <input type="submit" value="Echo as XML">
</form>
```

<form id="xmlForm" action="http://malsup.com/jquery/form/xml-echo.php" method="post"><div>
  Message: <input type="text" name="message" value="Hello XML">
  <input type="submit" value="Echo as XML">
</div></form>

#### Server code in `xml-echo.php`:

```php
<?php
// !!! IMPORTANT !!! - the server must set the content type to XML
header('Content-type: text/xml');
echo '<root><message>' . $_POST['message'] . '</message></root>';
?>
```

#### JavaScript:

```javascript
// prepare the form when the DOM is ready
$(document).ready(function() {
    // bind form using ajaxForm
    $('#xmlForm').ajaxForm({
        // dataType identifies the expected content type of the server response
        dataType:  'xml',

        // success identifies the function to invoke when the server response
        // has been received
        success:   processXml
    });
});
```

#### Callback function

```javascript
function processXml(responseXML) {
    // 'responseXML' is the XML document returned by the server; we use
    // jQuery to extract the content of the message node from the XML doc
    var message = $('message', responseXML).text();
    alert(message);
}
```

---

### HTML
This page shows how to handle HTML data returned from the server. The form below submits a message to the server and the server echos it back in an HTML div. The response is added to this page in the `htmlExampleTarget` div below.

#### Form markup:

```html
<form id="htmlForm" action="http://malsup.com/jquery/form/html-echo.php" method="post">
    Message: <input type="text" name="message" value="Hello HTML">
    <input type="submit" value="Echo as HTML">
</form>
```

<form id="htmlForm" action="http://malsup.com/jquery/form/html-echo.php" method="post"><div>
  Message: <input type="text" name="message" value="Hello HTML">
  <input type="submit" value="Echo as HTML">
</div></form>

#### Server code in `html-echo.php`:

```php
<?php
echo '<div style="background-color:#ffa; padding:20px">' . $_POST['message'] . '</div>';
?>
```

#### JavaScript:

```javascript
// prepare the form when the DOM is ready
$(document).ready(function() {
    // bind form using ajaxForm
    $('#htmlForm').ajaxForm({
        // target identifies the element(s) to update with the server response
        target: '#htmlExampleTarget',

        // success identifies the function to invoke when the server response
        // has been received; here we apply a fade-in effect to the new content
        success: function() {
            $('#htmlExampleTarget').fadeIn('slow');
        }
    });
});
```

#### htmlExampleTarget (output will be added below):
<div id="htmlExampleTarget"></div>

---

### File Upload
This page demonstrates the Form Plugin's file upload capabilities. There is no special coding required to handle file uploads. File input elements are automatically detected and processed for you.
      
Browsers that support the [XMLHttpRequest Level 2](http://www.w3.org/TR/XMLHttpRequest/) will be able to upload files seamlessly and even get progress updates as the upload proceeds. For older browsers, a fallback technology is used which involves iframes since it is not possible to upload files using the level 1 implmenentation of the XMLHttpRequest object. This is a common fallback technique, but it has inherent limitations. The iframe element is used as the target of the form's submit operation which means that the server response is written to the iframe. This is fine if the response type is HTML or XML, but doesn't work as well if the response type is             script or JSON, both of which often contain characters that need to be repesented using entity             references when found in HTML markup. 

To account for the challenges of script and JSON responses when using the iframe mode, the Form Plugin allows these responses to be embedded in a `textarea` element and it is recommended that you do so for these response types when used in conjuction with file uploads and older browsers. 

It is important to note that even when the dataType option is set to 'script', and the server is actually responding with some javascript to a multipart form submission, the response's Content-Type header should be forced to `text/html`, otherwise Internet Explorer will prompt the user to download a "file".

Also note that if there is no file input in the form then the request uses normal XHR to submit the form (not an iframe). This puts the burden on your server code to know when to use a textarea and when not to. If you like, you can use the `iframe` option of the plugin to force it to always use an *iframe mode* and then your server can always embed the response in a textarea. But the recommended solution is to test for the 'X-Requested-With' request header. If the value of that header is 'XMLHttpRequest' then you know that the form was posted via ajax.

The following PHP snippet shows how you can be sure to return content successfully:

```php
<?php
$xhr = $_SERVER['HTTP_X_REQUESTED_WITH'] == 'XMLHttpRequest';
if (!$xhr) 
  echo '<textarea>';
?>

// main content of response here
        
<?php
if (!$xhr)  
  echo '</textarea>';
?>
```

The form below provides an input element of type "file" along with a select element to specify the dataType of the response. The form is submitted to `files.php` which uses the dataType to determine what type of response to return.

<form id="uploadForm" action="http://malsup.com/jquery/form/files.php" method="POST" enctype="multipart/form-data">
    <input type="hidden" name="MAX_FILE_SIZE" value="100000">
    File: <input type="file" name="file">
    Return Type: <select id="uploadResponseType" name="mimetype">
        <option value="html">html</option>
        <option value="json">json</option>
        <option value="script">script</option>
        <option value="xml">xml</option>
    </select>
    <input type="submit" value="Submit 1" name="uploadSubmitter1">
    <input type="submit" value="Submit 2" name="uploadSubmitter2">
</form>
<label>Output:</label>
<div id="uploadOutput"></div>

Examples that show how to display upload progress:
- [Progress Demo 1](http://malsup.com/jquery/form/progress.html)
- [Progress Demo 2](http://malsup.com/jquery/form/progress2.html)
- [Progress Demo 3](http://malsup.com/jquery/form/progress3.html)
