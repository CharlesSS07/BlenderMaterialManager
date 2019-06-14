
function set_broadcast_on_click(){
    var socket = io('http://127.0.0.1:6006');
    socket.on('connect', function(){});
    socket.on('disconnect', function(){});
    
    var imgs = document.getElementsByClassName('grid-item');
    for (var i =0;i<imgs.length;i++){
        imgs[i].onclick = function(){
            //alert(this.childNodes[0].childNodes[0].getAttribute('src'));
            socket.emit('submitresource', this.childNodes[1].childNodes[0].childNodes[0].childNodes[0].innerHTML);
            window.location.href = 'https://www.patreon.com/TextureHaven/overview';
            var w = window.innerWidth*0.7;
            var h = window.innerHeight*0.7;
            window.open('https://www.patreon.com/TextureHaven/overview', 'DONATE!!', "height="+w+",width="+h);
            //realized I switched h and w, but like the resulting sidepanel.
        }
    }
}

window.onload = set_broadcast_on_click;

