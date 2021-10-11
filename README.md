# How Hot Is The Shop?
Website to provide the internal temperature of my wife's woodshop

The app itself is a simple flask app that renders a template with data stored in Redis

A cronjob runs a script to update that redis store.

That job calls out to the OpenWeatherMap api and to a Govee api that returns data recorded from a wifi thermometer
living in my wife's shop. This API is the one used by the Govee mobile app.

Hosted https://www.howhotistheshop.com/ or http://howhotistheshop.herokuapp.com/ if I stop paying for the paid heroku plan

## Config Vars

`ADMIN_EMAIL` - Email to send errors to

`SENDER` - Email who owns the sendgrid account and can send email

`SENDGRID_API_KEY` - Api key for sendgrid...

`GOVEE_DEVICE` - Device id measuring the temperature of the shop

`GOVEE_SKU` - Device Stock code for the model of that device

`REDIS_URL` - URL to access the redis instance

`WEATHER_API_KEY` - API key to get weather data

`WEATHER_LAT` - Latitude of rough area of shop

`WEATHER_LONG` - Longitude of rough area of shop

`GOVEE_EMAIL` - Email address for govee account

`GOVEE_PASSWORD` - Password for govee account

`GOVEE_CLIENT` - Client idd for govee account, not sure if I need it. Is returned from the login call



## You dummy you should be using UTC

Yeah, probably... but this is an app designed for one shop in the eastern timezone

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

## Scripts

`backfill_device_history` will update the history cache from scratch wiping the rest out
`update_caches` will update any cached data about the present state of the device. Updating the relevant history value if needed 
