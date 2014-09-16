////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// USB Switchable Charger//Device connection unit V1.0 Revision 2 ---- Arduino Code
// Author: Jon Findley
// Date: 9//5//2014
//
// Hardware:
//   3x 1//4W 10K Resistors
//   1x 1//4W 100k Resistor
//   1x BC 547B NPN Transistor
//   1x BD139 NPN Transistor
//   1x Arduino Pro Micro - 5V//16MHz ATmega32U4 VENDOR//PART: 2341:8037
//   1x White USB Type A Male cable (Charger control//power cable - TO COMPUTER)
//   1x Black USB Type A Male cable (Source power cable for charging circuit - TO CHARGER)
//   1x Black USB Type A Female cable (Input port for device charging cable - TO DEVICE)
//
// Commands:
//   0x0: get unique identifier
//   0x1: enable charging
//   0x2: disable charging
//   0x3: get status of charger, this is two bytes string with the first byte being if the
//        the device is connected or not (1 or 0) and the second byte means if the device
//        is charging or not (1 or 0)
//
// Notes:
//   When NOT charging,
//       Charger will send 1 when a device is plugged into the female connector
//       Charger will send 0 when a device is removed from the female connector
//
//  When charging,
//       Charger will not send anything
//
//  Charging amperage:
//       Fast charging is only possible on devices that support it (and in some cases, the cable matter).
//       This charging unit is capable of delivering 7.5W continuous, but only if the device wants that
//       much power, and the underlying charger is capable of supplying that much.
//
// WARNING:
//   Charging from a USB port on the same machine powering the charger is not recommended.
//   The reason for this is because the host controller will establish a data link with the device
//   which results in erratic voltage readings. You can still charge from the port, but detection will be
//   unreliable, although detection within the OS should now be possible.
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

struct state {
  int dividerPin;
  int sigPin;
  float last_divider_reading;
  boolean device_is_connected;
  boolean device_is_charging;
};

struct state s;

void version_uid() {
  Serial.println("d58e9cdc-8809-4486-a765-82961d7dc264");
}

boolean update_state(struct state *x) {
  float divider_reading = 0.0;
  divider_reading = x->last_divider_reading = analogRead(x->dividerPin);
  boolean current_connection_status = (divider_reading > 10.00 ? true : false);
  if (x->device_is_charging ) {
    current_connection_status = true;
  }
  else if (x->device_is_connected && !current_connection_status) {
    Serial.println("disconnected");
  }
  else if (!x->device_is_connected && current_connection_status) {
    Serial.println("connected");
  }

  x->device_is_connected = current_connection_status;
  return current_connection_status;
}

void device_status(struct state *x) {
  Serial.print(x->device_is_connected ? "connected:": "disconnected:");
  Serial.println(x->device_is_charging ? "charging": "not charging");
}

void enable_charging(struct state *x) {
  if (!x->device_is_charging) {
    digitalWrite(x->sigPin, HIGH);
    x->device_is_charging=true;
  }
}

void disable_charging(struct state *x) {
  if (x->device_is_charging) {
    digitalWrite(x->sigPin, LOW);
    x->device_is_charging=false;
  }
}

void setup(){
  s.sigPin = 3;
  s.dividerPin = 1;
  s.device_is_connected = false;
  s.device_is_charging = false;
  disable_charging(&s);
  Serial.begin(9600);
}

void loop(){
  delay(500); // this is a hack
  update_state(&s);
  if (!Serial.available())
    return;

    uint8_t c = (uint8_t)Serial.read();
    switch(c) {
      case 'I':
        version_uid();
        break;
      case 'E':
        enable_charging(&s);
        break;
      case 'D':
        disable_charging(&s);
        break;
      case 'S':
        device_status(&s);
        break;
    }
}
