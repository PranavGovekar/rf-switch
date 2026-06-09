/*
 * RF Switch Controller — Arduino Nano Every
 * ==========================================
 * Controls two H6P-330127 SP6T RF switches via one-hot encoding.
 *
 * Pin Assignment:
 *   Switch 1 (left side)  : D2, D3, D4, D5, D6, D7
 *   Switch 2 (right side) : A0, A1, A2, A3, A4, A5
 *
 * Default state on boot: Channel 6 (matches H6P-330127 hardware default)
 *
 * Serial Protocol (115200 baud, newline-terminated):
 *   S1C<n>   - Set Switch 1 to channel n (1-6), e.g. S1C3
 *   S2C<n>   - Set Switch 2 to channel n (1-6), e.g. S2C5
 *   S1OFF    - All Switch 1 pins LOW (undefined RF state)
 *   S2OFF    - All Switch 2 pins LOW (undefined RF state)
 *   ALLOFF   - Both switches all pins LOW
 *   STATUS   - Print current channel state of both switches
 *   HELP     - Print command reference
 *
 * Commands are case-insensitive. Both \n and \r\n line endings supported.
 *
 * Python example:
 *   import serial
 *   ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
 *   ser.write(b'S1C3\n')
 *   print(ser.readline().decode().strip())
 */

// --- Pin Definitions ---------------------------------------------------------

const uint8_t SW1_PINS[6] = {2, 3, 4, 5, 6, 7};         // Switch 1: D2-D7
const uint8_t SW2_PINS[6] = {A0, A1, A2, A3, A4, A5};   // Switch 2: A0-A5

// --- State Tracking ----------------------------------------------------------

int8_t sw1_channel = 0;   // 0 = all off, 1-6 = active channel
int8_t sw2_channel = 0;

// --- Core Functions ----------------------------------------------------------

void allOff(const uint8_t pins[6], int8_t &channel_state) {
  for (uint8_t i = 0; i < 6; i++) {
    digitalWrite(pins[i], LOW);
  }
  channel_state = 0;
}

// ch: 1-6. Sets only pins[ch-1] HIGH, all others LOW (one-hot guarantee).
bool setChannel(const uint8_t pins[6], int8_t &channel_state, int ch) {
  if (ch < 1 || ch > 6) return false;
  for (uint8_t i = 0; i < 6; i++) {
    digitalWrite(pins[i], (i == (uint8_t)(ch - 1)) ? HIGH : LOW);
  }
  channel_state = (int8_t)ch;
  return true;
}

// --- Serial Helpers ----------------------------------------------------------

void printStatus() {
  Serial.print(F("[STATUS] SW1="));
  if (sw1_channel == 0) Serial.print(F("OFF")); else Serial.print(sw1_channel);
  Serial.print(F("  SW2="));
  if (sw2_channel == 0) Serial.println(F("OFF")); else Serial.println(sw2_channel);
}

void printHelp() {
  Serial.println(F("-------------------------------------"));
  Serial.println(F(" RF Switch Controller - Command Help"));
  Serial.println(F("-------------------------------------"));
  Serial.println(F(" S1C<1-6>  Set Switch 1 to channel"));
  Serial.println(F(" S2C<1-6>  Set Switch 2 to channel"));
  Serial.println(F(" S1OFF     Switch 1 all pins LOW"));
  Serial.println(F(" S2OFF     Switch 2 all pins LOW"));
  Serial.println(F(" ALLOFF    Both switches all LOW"));
  Serial.println(F(" STATUS    Show current channel state"));
  Serial.println(F(" HELP      Show this message"));
  Serial.println(F("-------------------------------------"));
}

void handleCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  if (cmd.length() == 0) return;

  if (cmd == "HELP") {
    printHelp();

  } else if (cmd == "STATUS") {
    printStatus();

  } else if (cmd == "S1DEFAULT") {
    setChannel(SW1_PINS, sw1_channel, 6);
    Serial.println(F("[OK] SW1: CH6 (default)"));

  } else if (cmd == "S2DEFAULT") {
    setChannel(SW2_PINS, sw2_channel, 6);
    Serial.println(F("[OK] SW2: CH6 (default)"));

  } else if (cmd == "ALLDEFAULT") {
    setChannel(SW1_PINS, sw1_channel, 6);
    setChannel(SW2_PINS, sw2_channel, 6);
    Serial.println(F("[OK] Both switches: CH6 (default)"));

  } else if (cmd.startsWith("S1C")) {
    int ch = cmd.substring(3).toInt();
    if (setChannel(SW1_PINS, sw1_channel, ch)) {
      Serial.print(F("[OK] SW1: CH")); Serial.println(ch);
    } else {
      Serial.println(F("[ERR] SW1: channel must be 1-6"));
    }

  } else if (cmd.startsWith("S2C")) {
    int ch = cmd.substring(3).toInt();
    if (setChannel(SW2_PINS, sw2_channel, ch)) {
      Serial.print(F("[OK] SW2: CH")); Serial.println(ch);
    } else {
      Serial.println(F("[ERR] SW2: channel must be 1-6"));
    }

  } else {
    Serial.print(F("[ERR] Unknown command: "));
    Serial.println(cmd);
  }
}

// --- Setup & Loop ------------------------------------------------------------

void setup() {
  Serial.begin(115200);

  // Configure all control pins as outputs
  for (uint8_t i = 0; i < 6; i++) {
    pinMode(SW1_PINS[i], OUTPUT);
    pinMode(SW2_PINS[i], OUTPUT);
  }

  // H6P-330127 hardware defaults to CH6 at power-on.
  // Drive CH6 explicitly so Arduino state matches switch state.
  setChannel(SW1_PINS, sw1_channel, 6);
  setChannel(SW2_PINS, sw2_channel, 6);

  // Wait for Serial port to connect (Nano Every uses native USB CDC)
  unsigned long t0 = millis();
  while (!Serial && (millis() - t0 < 2000));

  Serial.println(F(""));
  Serial.println(F("RF Switch Controller - READY"));
  Serial.println(F("H6P-330127 x2 | 115200 baud"));
  Serial.println(F("Type HELP for command reference."));
  printStatus();
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    handleCommand(cmd);
  }
}