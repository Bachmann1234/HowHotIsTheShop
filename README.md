# How Hot Is The Shop?
Website to provide the internal temperature of my wife's woodshop

The app itself is a simple flask app that renders a template with data stored in Redis

A cronjob runs a script to update that redis store.

That job calls out to the OpenWeatherMap api and to a Govee api that returns data recorded from a wifi thermometer
living in my wife's shop. This API is the one used by the Govee mobile app.

Hosted https://www.howhotistheshop.com/ or http://howhotistheshop.herokuapp.com/ if I stop paying for the paid heroku plan

## Note on data

The current weather/shop data has no backup as it's not intended to persist

When I added historical data I wanted to back that up. Its a tiny amount of data, so I back it up via a google app script which runs dailly

```
function backupShopData() {
  const response = UrlFetchApp.fetch("https://www.howhotistheshop.com/history_raw");
  Logger.log(response.getContentText());  

  const resultingSheet = SpreadsheetApp.openById('redacted').getSheetByName('Sheet1')
  resultingSheet.clear();
  
  const jsonData = JSON.parse(response.getContentText())
  for (const dateString in jsonData) {
    resultingSheet.appendRow([dateString, jsonData[dateString]])
  }
  
}
```
