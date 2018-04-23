var msDelay = 0;

var delay = (function(){
    return function(callback, ms){
        clearTimeout(msDelay);
        msDelay = setTimeout(callback, ms);
    };
})();

function cancelTimer(){
    clearTimeout(msDelay);
}