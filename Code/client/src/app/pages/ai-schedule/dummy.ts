const forecastData = [
  { time: 'Hiện tại', temp: 28, humidity: 65, pressure: 1013 },
  { time: '+1h', temp: 29, humidity: 63, pressure: 1013 },
  { time: '+2h', temp: 30, humidity: 60, pressure: 1012 },
  { time: '+3h', temp: 31, humidity: 58, pressure: 1012 },
  { time: '+4h', temp: 29, humidity: 62, pressure: 1011 },
  { time: '+5h', temp: 27, humidity: 68, pressure: 1011 },
  { time: '+6h', temp: 26, humidity: 70, pressure: 1012 }
]

const suggestedActions = [
  {
    time: '06:00',
    probability: '0.82',
    action: 'Hoãn 90m'
  },
  {
    time: '10:00',
    probability: '0.30',
    action: 'Tưới 20m'
  }
]
export { forecastData, suggestedActions }
