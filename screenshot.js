var page = require('webpage').create();
var args = require('system').args;
var parsed = require('phantom-url')(args[1]);

var url = args[1];

page.viewportSize = {
  width: args[2]||1365,
  height: args[3]||768 
};

page.open(url, function() {
  var isMobile = args[2] < 1365 && args[3] < 768;
  var filename = (parsed.hostname+parsed.pathname).replace(/(\/|\-|\.)/g, '')+'-full-'+(isMobile ? 'mobile' : 'desktop')+'.png';
  page.render('./static/'+filename);
  console.log(filename);
  phantom.exit();
});
