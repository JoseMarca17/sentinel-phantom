#include <Arduino.h>
#include <SPI.h>
#include <Wire.h>
#include <MFRC522.h>
#include <Adafruit_PN532.h>

#define RC522_SS   5
#define RC522_RST  27
#define PN532_SDA  21
#define PN532_SCL  22
#define LED        2

MFRC522     rc522(RC522_SS, RC522_RST);
Adafruit_PN532 pn532(PN532_SDA, PN532_SCL);

bool pn532_ok = false;
bool rc522_ok = false;
String lastUID = "";
unsigned long lastScan = 0;
const unsigned long COOLDOWN = 2000;

// Llave MIFARE por defecto (6 bytes 0xFF)
uint8_t keyA[] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };

String bytesToHex(byte* buf, byte len) {
  String s = "";
  for (byte i = 0; i < len; i++) {
    if (buf[i] < 0x10) s += "0";
    s += String(buf[i], HEX);
  }
  s.toUpperCase();
  return s;
}

void blink(int n, int ms = 100) {
  for (int i = 0; i < n; i++) {
    digitalWrite(LED, HIGH); delay(ms);
    digitalWrite(LED, LOW);  delay(ms);
  }
}

// ─── NUEVA FUNCIÓN: LEER BLOQUE ───
void readBlock(int blockNum) {
  uint8_t success;
  uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };
  uint8_t uidLength;
  uint8_t data[16];

  success = pn532.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 500);
  if (success) {
    // Autenticar para el bloque (Sector = bloque / 4)
    success = pn532.mifareclassic_AuthenticateBlock(uid, uidLength, blockNum, 0, keyA);
    if (success) {
      success = pn532.mifareclassic_ReadDataBlock(blockNum, data);
      if (success) {
        String content = "";
        for (int i = 0; i < 16; i++) {
            if(data[i] >= 32 && data[i] <= 126) content += (char)data[i]; // Solo ASCII legible
            else content += ".";
        }
        Serial.println("{\"event\":\"READ_OK\",\"block\":" + String(blockNum) + ",\"content\":\"" + content + "\"}");
        return;
      }
    }
  }
  Serial.println("{\"event\":\"ERROR\",\"msg\":\"Fallo lectura bloque\"}");
}

// ─── NUEVA FUNCIÓN: ESCRIBIR BLOQUE ───
void writeBlock(int blockNum, String text) {
  uint8_t success;
  uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };
  uint8_t uidLength;
  uint8_t data[16];

  // Rellenar buffer con espacios
  memset(data, ' ', 16);
  for (int i = 0; i < text.length() && i < 16; i++) {
    data[i] = text[i];
  }

  success = pn532.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 500);
  if (success) {
    success = pn532.mifareclassic_AuthenticateBlock(uid, uidLength, blockNum, 0, keyA);
    if (success) {
      success = pn532.mifareclassic_WriteDataBlock(blockNum, data);
      if (success) {
        Serial.println("{\"event\":\"WRITE_OK\",\"status\":\"OK\"}");
        blink(1, 500);
        return;
      }
    }
  }
  Serial.println("{\"event\":\"ERROR\",\"msg\":\"Fallo escritura\"}");
}

void handleCommand(String cmd) {
  cmd.trim();
  if (cmd == "PING") {
    Serial.println("{\"event\":\"PONG\",\"device\":\"PHANTOM-ESP32\"}");
  } 
  else if (cmd == "STATUS") {
    Serial.println("{\"event\":\"STATUS\",\"pn532\":" + String(pn532_ok ? "true" : "false") + "}");
  }
  // COMANDO: READ 4
  else if (cmd.startsWith("READ ")) {
    int b = cmd.substring(5).toInt();
    readBlock(b);
  }
  // COMANDO: WRITE 4 SECRET_DATA
  else if (cmd.startsWith("WRITE ")) {
    int spaceIndex = cmd.indexOf(' ', 6);
    int b = cmd.substring(6, spaceIndex).toInt();
    String val = cmd.substring(spaceIndex + 1);
    writeBlock(b, val);
  }
  else {
    Serial.println("{\"event\":\"ERROR\",\"msg\":\"cmd desconocido\"}");
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED, OUTPUT);
  
  Wire.begin(PN532_SDA, PN532_SCL);
  pn532.begin();
  if (pn532.getFirmwareVersion()) {
    pn532_ok = true;
    pn532.SAMConfig();
  }

  SPI.begin();
  rc522.PCD_Init();
  rc522_ok = true;

  blink(3, 100);
  Serial.println("{\"event\":\"READY\"}");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    handleCommand(cmd);
  }

  // Escaneo normal (Solo si no hay comandos pendientes)
  if (pn532_ok) {
    uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };
    uint8_t uidLength;
    if (pn532.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 100)) {
      String suid = bytesToHex(uid, uidLength);
      if (suid != lastUID || (millis() - lastScan) > COOLDOWN) {
        lastUID = suid; lastScan = millis();
        Serial.println("{\"event\":\"SCAN\",\"uid\":\""+suid+"\",\"source\":\"PN532\"}");
        blink(1, 50);
      }
    }
  }
  
  // (Opcional) Escaneo RC522 para tarjetas de 125khz si tienes el bridge
  if (rc522_ok && rc522.PICC_IsNewCardPresent() && rc522.PICC_ReadCardSerial()) {
     String suid = bytesToHex(rc522.uid.uidByte, rc522.uid.size);
     if (suid != lastUID || (millis() - lastScan) > COOLDOWN) {
        lastUID = suid; lastScan = millis();
        Serial.println("{\"event\":\"SCAN\",\"uid\":\""+suid+"\",\"source\":\"RC522\"}");
     }
     rc522.PICC_HaltA();
     rc522.PCD_StopCrypto1();
  }
}