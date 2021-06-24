var chart = LightweightCharts.createChart(document.getElementById("chart"), {
	width: 600,
    height: 300,
	layout: {
		backgroundColor: '#FFFFFF',
		textColor: 'rgba(0, 0, 0, 0.9)',
	},
	grid: {
		vertLines: {
			color: 'rgba(197, 203, 206, 0.5)',
		},
		horzLines: {
			color: 'rgba(197, 203, 206, 0.5)',
		},
	},
	crosshair: {
		mode: LightweightCharts.CrosshairMode.Normal,
	},
	rightPriceScale: {
		borderColor: 'rgba(197, 203, 206, 0.8)',
	},
	timeScale: {
		borderColor: 'rgba(197, 203, 206, 0.8)',
	},
});

var candleSeries = chart.addCandlestickSeries({
  upColor: 'green',
  downColor: 'red',
  borderDownColor: 'red',
  borderUpColor: 'green',
  wickDownColor: 'red',
  wickUpColor: 'green',
});

fetch('http://localhost:5000/history')
    .then((r) => r.json())
    .then((response) => {
        candleSeries.setData(response);
    })

var binanceSocket = new WebSocket("wss://stream.binance.com:9443/ws/tfuelusdt@kline_1m");
binanceSocket.onmessage = function (event) {
    var messageObject = JSON.parse(event.data);
    candlestick = messageObject.k;

    candleSeries.update({
        time:  int(candlestick.t/1000),
        open:  candlestick.o,
        high:  candlestick.h,
        low:   candlestick.l,
        close: candlestick.c
    })
};

