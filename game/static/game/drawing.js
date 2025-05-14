document.addEventListener('DOMContentLoaded', () => { // ensures HTML is loaded before js used
    const c = document.getElementById("active-canvas");
    const ctx = c.getContext("2d");
    
    ctx.lineCap = "round";
    
    let coordX = 0;
    let coordY = 0;
    let active = false;
    let eraser = false;
        
    document.getElementById("color-canvas").onchange = colorPicker;
    document.getElementById("clear-canvas").onclick= clearCanvas;
    document.getElementById("eraser-canvas").onclick= changeEraser;
    document.getElementById("pencil-canvas").onclick= changePencil;
    document.getElementById("myRange").onchange= changeSize;
    function clearCanvas() {
        ctx.clearRect(0, 0, c.width, c.height);
        const message = JSON.stringify(
            {
                type: 'canvas_update_stroke',
                canvas_data: {
                    x: 0,
                    y: 0,
                    x2: c.width,
                    y2: c.height,
                    clear_canvas: true,
                    size: ctx.lineWidth,
                    erase: true,
                    shape: ctx.lineCap,
                    color: ctx.strokeStyle,
                },
                game_id: gameId,
                player_id: playerId
            }
        );
        gameSocket.send(message);

    }
    function changeEraser() {
        eraser=true;
    }
    function changePencil() {
        eraser=false;
    }
    function changeSize() {
        ctx.lineWidth = document.getElementById('myRange').value;
    }
    function colorPicker() {
        ctx.strokeStyle = document.getElementById("color-canvas").value;
    }
    function getMousePosition(c, event) {
        const rect = c.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        return [x, y];
    }

    c.addEventListener("click", function (e) {
        const coords = getMousePosition(c, e);
        ctx.beginPath();
        if (eraser) {
            ctx.clearRect(coords[0] + 1, coords[1] + 1, ctx.lineWidth, ctx.lineWidth);
        }
        else {
            ctx.moveTo(coords[0], coords[1]);
            ctx.lineTo(coords[0] + 1, coords[1] + 1);
            ctx.fill();
            ctx.stroke();
        }
        const message = JSON.stringify(
            {
                type: 'canvas_update_stroke',
                canvas_data: {
                    x: coords[0],
                    y: coords[1],
                    x2: coords[0]+1,
                    y2: coords[1]+1,
                    clear_canvas: false,
                    size: ctx.lineWidth,
                    erase: eraser,
                    shape: ctx.lineCap,
                    color: ctx.strokeStyle,
                },
                game_id: gameId,
                player_id: playerId
            }
        );
        gameSocket.send(message);
    });
    c.addEventListener("mousedown", function (e) {

        active = true;
        const coords = getMousePosition(c, e);
        coordX = coords[0];
        coordY = coords[1];

    });

    // not interacting with canvas 
    // dont need to record mouse movement
    c.addEventListener("mouseup", function (e) {
        active = false;
    });

    c.addEventListener("mouseout", function (e) {
        active = false;
    });

    c.addEventListener("mousemove", function (e) {
        // record the mouse movement
        if (active) {
            const coords = getMousePosition(c, e);
            ctx.beginPath();
            ctx.moveTo(coordX, coordY);
            // eraser is the same step as pencil, but with clearRect instead of lineTo
            if (eraser) {
                ctx.clearRect(coords[0], coords[1], ctx.lineWidth, ctx.lineWidth);
            }
            else {
                ctx.lineTo(coords[0], coords[1]);
            }
            ctx.stroke();
            const message = JSON.stringify(
            {
                type: 'canvas_update_stroke',
                canvas_data: {
                    x: coordX,
                    y: coordY,
                    x2: coords[0],
                    y2: coords[1],
                    clear_canvas: false,
                    size: ctx.lineWidth,
                    erase: eraser,
                    shape: ctx.lineCap,
                    color: ctx.strokeStyle,
                },
                game_id: gameId,
                player_id: playerId
            }
            );
            gameSocket.send(message);
            coordX = coords[0];
            coordY = coords[1];
            
        }

    });


    

});