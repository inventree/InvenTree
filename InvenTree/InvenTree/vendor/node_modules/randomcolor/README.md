# [Random Color](https://randomcolor.lllllllllllllllll.com)

A tiny script for generating attractive random colors. See the demo for [an explanation](https://randomcolor.lllllllllllllllll.com) and [some samples](https://randomcolor.lllllllllllllllll.com). randomColor has been ported to [C#](https://github.com/nathanpjones/randomColorSharped), [C++](https://github.com/xuboying/randomcolor-cpp), [Go](https://github.com/hansrodtang/randomcolor), [Haskell](http://hackage.haskell.org/package/palette-0.3/docs/Data-Colour-Palette-RandomColor.html), [Mathematica](https://github.com/yuluyan/PrettyRandomColor), [PHP](https://github.com/mistic100/RandomColor.php), [Python](https://github.com/kevinwuhoo/randomcolor-py), [Swift](https://github.com/onevcat/RandomColorSwift), [Perl6](https://github.com/Xliff/p6-RandomColor), [Objective-C](https://github.com/yageek/randomColor), [Java](https://github.com/lzyzsd/AndroidRandomColor), [R](https://github.com/ronammar/randomcoloR), [Reason](https://github.com/ktrzos/bs-randomColor) and [Rust](https://github.com/elementh/random_color).

[![Demo](http://i.imgur.com/lOLCqvu.gif)](https://randomcolor.lllllllllllllllll.com)

To use randomColor **in the browser**, download the [latest minified version of randomColor](http://cdnjs.com/libraries/randomcolor) and include it on your page. Then call the script:

```javascript
var color = randomColor(); // a hex code for an attractive color
```

To use randomColor **on the server with node.js**, install [randomColor from npm](https://www.npmjs.org/package/randomcolor) then call the script:

```bash
npm install randomcolor
```
```javascript
var randomColor = require('randomcolor'); // import the script
var color = randomColor(); // a hex code for an attractive color
```

## Options

You can pass an options object to influence the type of color it produces. The options object accepts the following properties:

```hue``` – Controls the hue of the generated color. You can pass a string representing a color name: ```red```, ```orange```, ```yellow```, ```green```, ```blue```, ```purple```, ```pink``` and ```monochrome``` are currently supported. If you pass a  hexidecimal color string such as ```#00FFFF```, randomColor will extract its hue value and use that to generate colors.

```luminosity``` – Controls the luminosity of the generated color. You can specify a string containing ```bright```, ```light``` or ```dark```.

```count``` – An integer which specifies the number of colors to generate.

```seed``` - An integer or string which when passed will cause randomColor to return the same color each time.

```format``` – A string which specifies the format of the generated color. Possible values are ```rgb```, ```rgba```, ```rgbArray```, ```hsl```, ```hsla```, ```hslArray``` and ```hex``` (default).

```alpha``` – A decimal between 0 and 1. Only relevant when using a format with an alpha channel (```rgba``` and ```hsla```). Defaults to a random value.

## Examples

```javascript

// Returns a hex code for an attractive color
randomColor(); 

// Returns an array of ten green colors
randomColor({
   count: 10,
   hue: 'green'
});

// Returns a hex code for a light blue
randomColor({
   luminosity: 'light',
   hue: 'blue'
});

// Returns a hex code for a 'truly random' color
randomColor({
   luminosity: 'random',
   hue: 'random'
});

// Returns a bright color in RGB
randomColor({
   luminosity: 'bright',
   format: 'rgb' // e.g. 'rgb(225,200,20)'
});

// Returns a dark RGB color with random alpha
randomColor({
   luminosity: 'dark',
   format: 'rgba' // e.g. 'rgba(9, 1, 107, 0.6482447960879654)'
});

// Returns a dark RGB color with specified alpha
randomColor({
   luminosity: 'dark',
   format: 'rgba',
   alpha: 0.5 // e.g. 'rgba(9, 1, 107, 0.5)',
});

// Returns a light HSL color with random alpha
randomColor({
   luminosity: 'light',
   format: 'hsla' // e.g. 'hsla(27, 88.99%, 81.83%, 0.6450211517512798)'
});

```

## To do

*More generally, it might be a good idea to consider using other color models.*

1. Use this on the demo
http://jsfiddle.net/dpLp318f/
https://www.vis4.net/blog/posts/avoid-equidistant-hsv-colors/
https://www.vis4.net/blog/posts/mastering-multi-hued-color-scales/
2. When returning an array of multiple colors, try to make each color as distinct as possible. Make sure each color is distinct to its neighbours.
3. Improve attractive dark color generation, currently they're a touch murky.
4. Improve the color dictionary
  - definition of hue values and attractive luminosity bounds
  - think about how to store hue aliases (e.g. fuschia) or subranges (e.g teal)
  - think about making a little point and click tool for defining your own luminosity bounds and customizing the color dictionary
5. Think about how to return seeds.
6. Think about adding feature to return complementary & contrasting colors, as well as color triads, tetrads etc. Other libraries might already do this better though.
7. Think about adding a scheme options which would return a dominant color, as well as secondary, tertiary color and primary and secondary text colors. This might be a bad idea.
8. Add a nice visualization of the 'attractive color space' to the demo https://www.youtube.com/watch?v=x0-qoXOCOow
9. Add a feature to return random colors close to a provided hex 

## In use

* [The Daily Show](http://maketrumptweetseightagain.com/) used it to make an extension which [converts Trump's tweets into a child's scribble](https://twitter.com/riseuphes/status/929579600354693120).
* [Initial.js](https://github.com/judesfernando/initial.js) used it to generate Gmail-style avatars.
* [ng2-Logger](https://github.com/darekf77/ng2-logger) used it to make logs a little more colorful.
* [vue-randomcolor](https://github.com/alebeck/vue-randomcolor) adds attractive random colors to Vue.js.

Did you use randomColor.js for something? [Tell me about it](https://lllllllllllllllll.com).
