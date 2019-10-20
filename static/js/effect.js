(function (AudioContext) {
    'use strict';

    var actx = new AudioContext();
    var $audioPlayer = document.getElementById('audio-player');
    var $audioInput = document.getElementById('file');
    var $audioPlay = document.getElementById('btn-play');
    var $audioStop = document.getElementById('btn-stop');
    var $audioClear = document.getElementById('btn-clear');
    var canvas = document.getElementsByTagName('canvas')[0];
    var canvasWidth = canvas.width;
    var canvasHeight = canvas.height;
    var canvasCtx = canvas.getContext('2d');

    $audioInput.addEventListener('change', function (event) {
        if (!event.target.files[0]) {
            $audioClear.click();
            return;
        }

        $audioPlayer.src = window.URL.createObjectURL(event.target.files[0]);
        createWaveform($audioPlayer.src);
    }, false);
    $audioPlay.addEventListener('click', function () {
        if ($audioPlayer.src) {
            $audioPlayer.play();
        }
    }, false);
    $audioStop.addEventListener('click', function () {
        $audioPlayer.pause();
        $audioPlayer.currentTime = 0;
    }, false);
    $audioClear.addEventListener('click', function () {
        $audioPlayer.pause();
        $audioPlayer.removeAttribute('src');
        $audioInput.value = '';
        clearCanvas();
    }, false);

    if ($audioPlayer.src) {
        createWaveform($audioPlayer.src);
    }

    function clearCanvas() {
        canvasWidth = canvas.width;
        canvasHeight = canvas.height;
        canvasCtx.clearRect(0, 0, canvasWidth, canvasHeight);
        canvasCtx.beginPath();
    }

    function getAudioBuffer(url, func) {
        var xhr = new XMLHttpRequest();

        xhr.responseType = 'arraybuffer';
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4) {
                return;
            }

            actx.decodeAudioData(xhr.response, function (audioBuffer) {
                func(audioBuffer);
            });
        };

        xhr.open('GET', url, true);
        xhr.send();
    }

    function createWaveform(url) {
        clearCanvas();

        getAudioBuffer(url, function (audioBuffer) {
            var bufferFl32 = new Float32Array(audioBuffer.length);
            var msec = Math.floor(1 * Math.pow(10, -3) * actx.sampleRate);
            var leng = bufferFl32.length;

            bufferFl32.set(audioBuffer.getChannelData(0));

            for (var idx = 0; idx < leng; idx++) {
                if (idx % msec === 0) {
                    var x = canvasWidth * (idx / leng);
                    var y = (1 - bufferFl32[idx]) / 2 * canvasHeight;

                    if (idx === 0) {
                        canvasCtx.moveTo(x, y);
                    } else {
                        canvasCtx.lineTo(x, y);
                    }
                }
            }

            canvasCtx.strokeStyle = '#6cc7ff';
            canvasCtx.stroke();
        });
    }

    var source = actx.createMediaElementSource($audioPlayer);
    var gain = actx.createGain();
    var comp = actx.createDynamicsCompressor();
    var compGain = actx.createGain();
    var dist = actx.createWaveShaper();
    var distGain = actx.createGain();
    var eqGain = actx.createGain();
    var eqFreqs = [64, 256, 1024, 2048, 8192];
    var eqs = [];

    for (var i = 0; i < eqFreqs.length; i++) {
        var bqFilter = actx.createBiquadFilter();
        bqFilter.frequency.value = eqFreqs[i];
        bqFilter.Q.value = 1;
        bqFilter.type = 'peaking';
        bqFilter.gain.value = 0;
        eqs[i] = bqFilter;
    }

    gain.gain.value = 1;
    dist.curve = makeDistortionCurve(200);
    dist.oversample  = '4x';

    source.connect(gain);
    gain.connect(compGain);
    compGain.connect(distGain);
    distGain.connect(eqGain);
    eqGain.connect(actx.destination);

    /**
     * @see https://developer.mozilla.org/ja/docs/Web/API/AudioContext/createWaveShaper#Example
     */
    function makeDistortionCurve(amount) {
        var k = typeof amount === 'number' ? amount : 50;
        var nSamples = 44100;
        var curve = new Float32Array(nSamples);
        var deg = Math.PI / 180;
        var x;
        for (var i = 0; i < nSamples; ++i) {
            x = i * 2 / nSamples - 1;
            curve[i] = (3 + k) * x * 20 * deg / (Math.PI + k * Math.abs(x));
        }
        return curve;
    }


}(window.AudioContext));
