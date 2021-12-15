---
---

## Form Fields
This page describes and demonstrates the Form Plugin's `fieldValue` and `fieldSerialize` methods.

### fieldValue
`fieldValue` allows you to retrieve the current value of a field. For example, to retrieve the value of the password field in a form with the id of 'myForm' you would write:

```javascript
var pwd = $('#myForm :password').fieldValue()[0];
```

This method *always* returns an array. If no valid value can be determined the array will be empty, otherwise it will contain one or more values.

### fieldSerialize
`fieldSerialize` allows you to serialize a subset of a form into a query string. This is useful when you need to process only certain fields. For example, to serialize only the text inputs of a form you would write:

```javascript
var queryString = $('#myForm :text').fieldSerialize();
```

<form id="inputForm" action="#">
  <div>
    <h4>Demonstration</h4>
    <p>
      Enter a jQuery expression into the textbox below and then click 'Test' to see the results
      of the <code class="inline">fieldValue</code> and <code class="inline">fieldSerialize</code>
      methods. These methods are run against the test form that follows.
    </p>
    jQuery expression:
    <input id="query" type="text" value=":text">
    <span style="color:#555">(ie: textarea, [@type='hidden'], :radio, :checkbox, etc)</span><br>
    <input id="successful" type="checkbox" checked="checked"> [Successful controls](https://www.w3.org/TR/html5/forms.html#constructing-form-data-set) only<br>
    <input type="submit" value="Test">
  </div>
</form>


<form id="test" action="dummy.php" method="post"><div>
    <strong>Test Form</strong>
    <table>
      <tr><td>&lt;input type="hidden" <span class="name">name="Hidden"</span> value="secret"&gt;</td><td><input type="hidden" name="Hidden" value="secret"></td></tr>
      <tr><td>&lt;input <span class="name">name="Name"</span> type="text" value="MyName1"&gt;</td><td><input name="Name" type="text" value="MyName1"></td></tr>
      <tr><td>&lt;input <span class="name">name="Password"</span> type="password"&gt;</td><td><input name="Password" type="password" value=""></td></tr>
      <tr><td>&lt;select <span class="name">name="Multiple"</span> multiple="multiple"&gt;</td><td><select name="Multiple" multiple="multiple">
          <option value="one" selected="selected">One</option>
          <option value="two">Two</option>
          <option value="three">Three</option>
      </select></td></tr>
      <tr><td>&lt;select <span class="name">name="Single"</span>&gt;</td><td><select name="Single">
          <option value="one" selected="selected">One</option>
          <option value="two">Two</option>
          <option value="three">Three</option>
      </select></td></tr>
      <tr><td>&lt;input type="checkbox" <span class="name">name="Check"</span> value="1"&gt;</td><td><input type="checkbox" name="Check" value="1"></td></tr>
      <tr><td>&lt;input type="checkbox" <span class="name">name="Check"</span> value="2"&gt;</td><td><input type="checkbox" name="Check" value="2"></td></tr>
      <tr><td>&lt;input type="checkbox" <span class="name">name="Check"</span> value="3"&gt;</td><td><input type="checkbox" name="Check" value="3"></td></tr>
      <tr><td>&lt;input type="checkbox" <span class="name">name="Check2"</span> value="4"&gt;</td><td><input type="checkbox" name="Check2" value="4"></td></tr>
      <tr><td>&lt;input type="checkbox" <span class="name">name="Check2"</span> value="5"&gt;</td><td><input type="checkbox" name="Check2" value="5"></td></tr>
      <tr><td>&lt;input type="checkbox" <span class="name">name="Check3"</span>&gt;</td><td><input type="checkbox" name="Check3"></td></tr>
      <tr><td>&lt;input type="radio" <span class="name">name="Radio"</span> value="1"&gt;</td><td><input type="radio" name="Radio" value="1"></td></tr>
      <tr><td>&lt;input type="radio" <span class="name">name="Radio"</span> value="2"&gt;</td><td><input type="radio" name="Radio" value="2"></td></tr>
      <tr><td>&lt;input type="radio" <span class="name">name="Radio"</span> value="3"&gt;</td><td><input type="radio" name="Radio" value="3"></td></tr>
      <tr><td>&lt;input type="radio" <span class="name">name="Radio2"</span> value="4"&gt;</td><td><input type="radio" name="Radio2" value="4"></td></tr>
      <tr><td>&lt;input type="radio" <span class="name">name="Radio2"</span> value="5"&gt;</td><td><input type="radio" name="Radio2" value="5"></td></tr>
      <tr><td>&lt;textarea <span class="name">name="Text"</span> rows="2" cols="20"&gt;&lt;/textarea&gt;</td><td><textarea name="Text" rows="2" cols="20"></textarea></td></tr>
      <tr><td>&lt;input type="reset" <span class="name">name="resetButton"</span> value="Reset"&gt;</td><td><input type="reset" name="resetButton" value="Reset"></td></tr>
      <tr><td>&lt;input type="submit" <span class="name">name="sub"</span> value="Submit"&gt;</td><td><input type="submit"  name="submitButton" value="Submit"></td></tr>
    </table>
</div></form>

By default, `fieldValue` and `fieldSerialize` only function on '[successful controls](https://www.w3.org/TR/html5/forms.html#constructing-form-data-set)'. This means that if you run the following code on a checkbox that is not checked, the result will be an empty array.
```javascript
// value will be an empty array if checkbox is not checked:
var value = $('#myUncheckedCheckbox').fieldValue();
// value.length == 0
```

However, if you really want to know the 'value' of the checkbox element, even if it's unchecked, you can write this:
```javascript
// value will hold the checkbox value even if it's not checked:
var value = $('#myUncheckedCheckbox').fieldValue(false);
// value.length == 1
```
