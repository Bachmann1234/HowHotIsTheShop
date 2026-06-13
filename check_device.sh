#!/usr/bin/env bash
# Query the live Govee cloud reading for the shop thermometer.
#
# Prints the temperature, humidity and battery that Govee's servers currently
# report -- i.e. exactly what the site shows. If this disagrees with the
# physical unit's display, the device has lost its cloud sync (re-pair its
# WiFi); it is not a bug in this app.
set -euo pipefail
IFS=$'\n\t'

cd "$(dirname "$0")"

if [[ ! -f .env ]]; then
  echo "error: .env not found (need GOVEE_EMAIL/PASSWORD/CLIENT/DEVICE)" >&2
  exit 1
fi
set -a; source .env; set +a

# Govee rejects requests without a recent appVersion header on both endpoints.
APP_VERSION="6.8.30"

# Govee returns HTTP 200 even on failure, with the real error in the body,
# so we validate the body rather than trusting the status code.
login=$(curl -s https://app2.govee.com/account/rest/account/v1/login \
  -H 'Content-Type: application/json' \
  -H "appVersion: $APP_VERSION" \
  -d "{\"email\":\"$GOVEE_EMAIL\",\"password\":\"$GOVEE_PASSWORD\",\"client\":\"$GOVEE_CLIENT\"}")

token=$(echo "$login" | jq -r '.client.token // empty')
if [[ -z "$token" ]]; then
  echo "login failed: $(echo "$login" | jq -r '.message // "unknown error"')" >&2
  exit 1
fi

devices=$(curl -s -X POST https://app2.govee.com/device/rest/devices/v1/list \
  -H 'Content-Type: application/json' \
  -H "appVersion: $APP_VERSION" \
  -H "Authorization: Bearer $token")

device=$(echo "$devices" | jq --arg d "$GOVEE_DEVICE" '.devices[]? | select(.device == $d)')
if [[ -z "$device" ]]; then
  echo "device $GOVEE_DEVICE not found: $(echo "$devices" | jq -r '.message // "unknown error"')" >&2
  exit 1
fi

echo "$device" | jq -r '
  (.deviceExt.lastDeviceData | fromjson) as $d |
  (.deviceExt.deviceSettings | fromjson) as $s |
  ($d.tem / 100) as $c |
  ($d.hum / 100) as $h |
  ($d.lastTime / 1000 | strftime("%Y-%m-%d %H:%M:%S UTC")) as $t |
  "Temperature: \(($c * 1.8 + 32) | .*10 | round / 10)F (\($c)C)",
  "Humidity:    \($h)%",
  "Battery:     \($s.battery)%",
  "Online:      \($d.online)",
  "Reading at:  \($t)"
'
