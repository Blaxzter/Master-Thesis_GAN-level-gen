/*****************************************************************************
 ** ANGRYBIRDS AI AGENT FRAMEWORK
 ** Copyright (c) 2014,XiaoYu (Gary) Ge, Stephen Gould,Jochen Renz
 **  Sahan Abeyasinghe, Jim Keys,   Andrew Wang, Peng Zhang
 ** All rights reserved.
**This work is licensed under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
**To view a copy of this license, visit http://www.gnu.org/licenses/
 *****************************************************************************/

// Get canvas and webgl context globally
var srcCanvas = document.getElementById("canvas");

// PreserveDrawingBuffer has to be true to get the screenshoots
var context = srcCanvas.getContext("webgl", {preserveDrawingBuffer: true})
           || srcCanvas.getContext("experimental-webgl", {preserveDrawingBuffer: true});

(function() {
    var sock = null;

    function connect() {

        if (sock !== null) {
            return;
        }

        console.log('Connecting...');
        sock = new WebSocket('ws://localhost:9000/');

        sock.onopen = function() {
            console.log('Connected!');
        };

        sock.onclose = function(e) {
            sock = null;
            console.log('Connection closed (' + e.code + ')');
            reconnect();
        };

        sock.onmessage = function(e) {
            // console.log('Message received: ' + e.data);
            var j = JSON.parse(e.data);

            var id = j[0];   // message id
            var type = j[1]; // message type (see handlers)
            var data = j[2]; // message data (depends on handler)

            if (handlers[type]) {
                send(id, handlers[type](data));
            } else {
                console.log('Invalid message: ' + e.type);
            }
        };

        sock.onerror = function(e) {
            sock = null;
            reconnect();
        };
    }

    function reconnect() {
        setTimeout(connect, 1000);
    }

    function send(id, data) {
        var msg = JSON.stringify([id, data || {}]);
        console.log("sending message: " + msg);

        sock.send(msg);
    }

    // define supported message handlers
    var handlers = {
        'click': click,
        'drag': drag,
        'mousewheel': mousewheel,
        'screenshot': screenshot
    };

    // generate a mouse click event
    function click(data) {

        var clickX = data['x'];
        var clickY = data['y'];

        clickX = srcCanvas.offsetLeft + clickX;
        clickY = srcCanvas.offsetTop + clickY;

        console.log("Click");
        console.log("x = " + clickX + " y = " + clickY);

        var evt = new MouseEvent("mousedown", {
            bubbles: true,
            cancelable: false,
            screenX: clickX,
            screenY: clickY,
            button: 0
        });

        srcCanvas.dispatchEvent(evt);

        evt = new MouseEvent("mouseup", {
            bubbles: true,
            cancelable: false,
            screenX: clickX,
            screenY: clickY,
            button: 0
        });

        srcCanvas.dispatchEvent(evt);
    }

    // generate a mouse drag event
    function drag(data) {

        var dragX = data['x'];
        var dragY = data['y'];
        var dragDX = data['dx'];
        var dragDY = data['dy'];

        dragX = srcCanvas.offsetLeft + dragX;
        dragY = srcCanvas.offsetTop + dragY;
        dragDX = dragX + dragDX;
        dragDY = dragY + dragDY;

        console.log("Drag");
        console.log("x = " + dragX + " y = " + dragY);

        var evt = new MouseEvent("mousedown", {
            bubbles: true,
            cancelable: true,
            view: window,
            clientX: dragX,
            clientY: dragY,
            button: 0
        });

        srcCanvas.dispatchEvent(evt);

        evt = new MouseEvent("mousemove", {
            bubbles: true,
            cancelable: true,
            view: window,
            clientX: dragDX,
            clientY: dragDY,
            button: 0
        });

        srcCanvas.dispatchEvent(evt);

        evt = new MouseEvent("mouseup", {
            bubbles: true,
            cancelable: true,
            view: window,
            clientX: dragDX,
            clientY: dragDY,
            button: 0
        });

        srcCanvas.dispatchEvent(evt);
    }

    // generate a mouse wheel event
	function mousewheel(data) {

		var delta = data['delta'];
		// var canvas = $('canvas');
		//var evt = document.createEvent('WheelEvent');
		var eventInit = { deltaX: 0, deltaY: -delta*120 }
		var evt = new WheelEvent("mousewheel", eventInit);
		//evt.initWebKitWheelEvent(0, delta, window, 0, 0, 0, 0, false, false, false, false);
		srcCanvas.dispatchEvent(evt);
	}

    // capture a screenshot and send it to the client
    function screenshot(data) {

        // obtain a png of the canvas
        var imageString = srcCanvas.toDataURL();
        return {'data': imageString, 'time': new Date().getTime()};
    }

    // wait for the client to connect
    connect();
})();
