var page = require('webpage').create();
var args = require('system').args;
var parsed = require('phantom-url')(args[1]);

var url = args[1];

page.viewportSize = {
  width: 1365,
  height: 768 
};

page.open(url, function() {
  var filename = (parsed.hostname+parsed.pathname).replace(/(\/|\-|\.)/g, '')+'-full.png';
  page.render('./static/'+filename);
  console.log(filename);
  phantom.exit();
});
