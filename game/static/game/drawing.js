document.addEventListener('DOMContentLoaded', () => { // ensures HTML is loaded before js used
    const c = document.getElementById("active-canvas");
    const ctx = c.getContext("2d");
    
    ctx.lineCap = "round";
    
    let coordX = 0;
    let coordY = 0;
    let active = false;
    let eraser = false;
    // let fill = false;
    
    document.getElementById("color-canvas").onchange = colorPicker;
    document.getElementById("clear-canvas").onclick= clearCanvas;
    document.getElementById("eraser-canvas").onclick= changeEraser;
    document.getElementById("pencil-canvas").onclick= changePencil;
    document.getElementById("myRange").onchange= changeSize;
    function clearCanvas() {
        ctx.clearRect(0, 0, c.width, c.height);
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
    });
    c.addEventListener("mousedown", function (e) {

        active = true;
        const coords = getMousePosition(c, e);
        coordX = coords[0];
        coordY = coords[1];

    });

    c.addEventListener("mouseup", function (e) {
        active = false;
    });

    c.addEventListener("mouseout", function (e) {
        active = false;
    });


    c.addEventListener("mousemove", function (e) {

        if (active) {
            const coords = getMousePosition(c, e);
            ctx.beginPath();
            if (eraser) {
                ctx.moveTo(coordX, coordY);
                ctx.clearRect(coords[0], coords[1], ctx.lineWidth, ctx.lineWidth);
                ctx.stroke();
                coordX = coords[0];
                coordY = coords[1];
            }
            else {
                ctx.moveTo(coordX, coordY);
                ctx.lineTo(coords[0], coords[1]);
                ctx.stroke();
                coordX = coords[0];
                coordY = coords[1];
            }
        }

    });

});