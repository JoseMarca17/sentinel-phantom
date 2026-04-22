// /*
//  * SENTINEL PHANTOM — ESP32 RFID/NFC Bridge
//  * Maneja PN532 (NFC/MIFARE) y RC522 (125kHz)
//  * Comunicación UART con Raspberry Pi
//  * Modo standalone para pruebas en Windows
//  */

// #include <Arduino.h>
// #include <SPI.h>
// #include <Wire.h>
// #include <MFRC522.h>
// #include <Adafruit_PN532.h>

// // ── Pines RC522 (SPI) ────────────────────────────────────────────────────────
// #define RC522_SS_PIN   5
// #define RC522_RST_PIN  27

// // ── Pines PN532 (I2C) ────────────────────────────────────────────────────────
// #define PN532_SDA      21
// #define PN532_SCL      22

// // ── Pin LED de estado ────────────────────────────────────────────────────────
// #define LED_PIN        2   // LED interno del ESP32

// // ── Instancias ────────────────────────────────────────────────────────────────
// MFRC522 rc522(RC522_SS_PIN, RC522_RST_PIN);
// Adafruit_PN532 pn532(PN532_SDA, PN532_SCL);

// // ── Estado del sistema ────────────────────────────────────────────────────────
// bool pn532_ok  = false;
// bool rc522_ok  = false;
// String lastUID = "";
// unsigned long lastScanTime = 0;
// const unsigned long SCAN_COOLDOWN = 2000;  // ms entre lecturas del mismo UID

// // ── Whitelist de UIDs autorizados ─────────────────────────────────────────────
// // Agregar/quitar UIDs según necesidad, en mayúsculas sin espacios
// const char* WHITELIST[] = {
//     "DEADBEEF",
//     "A1B2C3D4",
//     "12345678"
// };
// const int WHITELIST_SIZE = 3;

// // ── Modo de operación ─────────────────────────────────────────────────────────
// // true  = espera comandos de la Pi via Serial
// // false = modo standalone (imprime todo al monitor serial)
// bool PI_MODE = false;

// // ── Helpers ───────────────────────────────────────────────────────────────────

// String bytesToHex(byte* buf, byte len) {
//     String hex = "";
//     for (byte i = 0; i < len; i++) {
//         if (buf[i] < 0x10) hex += "0";
//         hex += String(buf[i], HEX);
//     }
//     hex.toUpperCase();
//     return hex;
// }

// bool isWhitelisted(String uid) {
//     for (int i = 0; i < WHITELIST_SIZE; i++) {
//         if (uid == String(WHITELIST[i])) return true;
//     }
//     return false;
// }

// void blinkLED(int times, int ms = 100) {
//     for (int i = 0; i < times; i++) {
//         digitalWrite(LED_PIN, HIGH);
//         delay(ms);
//         digitalWrite(LED_PIN, LOW);
//         delay(ms);
//     }
// }

// // ── Respuesta estandarizada ───────────────────────────────────────────────────
// // Formato JSON simple para que la Pi lo parsee fácil
// void sendResponse(String event, String uid, String status, String source) {
//     String json = "{";
//     json += "\"event\":\"" + event + "\",";
//     json += "\"uid\":\"" + uid + "\",";
//     json += "\"status\":\"" + status + "\",";
//     json += "\"source\":\"" + source + "\",";
//     json += "\"authorized\":" + String(status == "AUTORIZADO" ? "true" : "false");
//     json += "}";
//     Serial.println(json);
// }

// // ── Inicialización ────────────────────────────────────────────────────────────

// void setup() {
//     Serial.begin(115200);
//     delay(500);
//     pinMode(LED_PIN, OUTPUT);

//     Serial.println("[PHANTOM] RFID/NFC Bridge iniciando...");

//     // ── Init PN532 (I2C) ──────────────────────────────────────────────────────
//     Wire.begin(PN532_SDA, PN532_SCL);
//     pn532.begin();
//     uint32_t versiondata = pn532.getFirmwareVersion();
//     if (versiondata) {
//         pn532_ok = true;
//         pn532.SAMConfig();
//         Serial.print("[PN532] OK — Firmware v");
//         Serial.print((versiondata >> 16) & 0xFF);
//         Serial.print(".");
//         Serial.println((versiondata >> 8) & 0xFF);
//     } else {
//         Serial.println("[PN532] ERROR — No detectado");
//     }

//     // ── Init RC522 (SPI) ──────────────────────────────────────────────────────
//     SPI.begin();
//     rc522.PCD_Init();
//     byte v = rc522.PCD_ReadRegister(MFRC522::VersionReg);
//     if (v == 0x91 || v == 0x92) {
//         rc522_ok = true;
//         Serial.print("[RC522] OK — Version 0x");
//         Serial.println(v, HEX);
//     } else {
//         Serial.println("[RC522] ERROR — No detectado (o versión desconocida)");
//         rc522_ok = true;  // intentar igual, algunos módulos reportan diferente
//     }

//     blinkLED(3, 150);
//     Serial.println("[PHANTOM] Listo. Comandos: STATUS | WHITELIST | ADD:<uid> | REMOVE:<uid> | MODE:PI | MODE:STANDALONE");
//     Serial.println("[PHANTOM] Acerca una tarjeta al PN532 o RC522...");
// }

// // ── Lectura PN532 ─────────────────────────────────────────────────────────────

// String readPN532() {
//     uint8_t uid[7];
//     uint8_t uidLen;
//     bool found = pn532.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLen, 300);
//     if (!found) return "";
//     return bytesToHex(uid, uidLen);
// }

// // ── Lectura RC522 ─────────────────────────────────────────────────────────────

// String readRC522() {
//     if (!rc522.PICC_IsNewCardPresent()) return "";
//     if (!rc522.PICC_ReadCardSerial())   return "";
//     String uid = bytesToHex(rc522.uid.uidByte, rc522.uid.size);
//     rc522.PICC_HaltA();
//     rc522.PCD_StopCrypto1();
//     return uid;
// }

// // ── Procesar UID detectado ────────────────────────────────────────────────────

// void processUID(String uid, String source) {
//     if (uid == "") return;

//     // Anti-rebote: ignorar si es el mismo UID en menos de SCAN_COOLDOWN ms
//     unsigned long now = millis();
//     if (uid == lastUID && (now - lastScanTime) < SCAN_COOLDOWN) return;

//     lastUID = uid;
//     lastScanTime = now;

//     bool auth = isWhitelisted(uid);
//     String status = auth ? "AUTORIZADO" : "DENEGADO";

//     if (auth) {
//         blinkLED(2, 100);   // 2 blinks rápidos = autorizado
//     } else {
//         blinkLED(5, 50);    // 5 blinks rápidos = denegado
//     }

//     sendResponse("SCAN", uid, status, source);
// }

// // ── Procesar comandos Serial de la Pi ─────────────────────────────────────────

// void processCommand(String cmd) {
//     cmd.trim();

//     if (cmd == "STATUS") {
//         String resp = "{\"event\":\"STATUS\",";
//         resp += "\"pn532\":" + String(pn532_ok ? "true" : "false") + ",";
//         resp += "\"rc522\":" + String(rc522_ok ? "true" : "false") + ",";
//         resp += "\"whitelist_size\":" + String(WHITELIST_SIZE) + ",";
//         resp += "\"last_uid\":\"" + lastUID + "\"}";
//         Serial.println(resp);

//     } else if (cmd == "WHITELIST") {
//         Serial.print("{\"event\":\"WHITELIST\",\"uids\":[");
//         for (int i = 0; i < WHITELIST_SIZE; i++) {
//             Serial.print("\"");
//             Serial.print(WHITELIST[i]);
//             Serial.print("\"");
//             if (i < WHITELIST_SIZE - 1) Serial.print(",");
//         }
//         Serial.println("]}");

//     } else if (cmd.startsWith("CHECK:")) {
//         // La Pi manda un UID para verificar: CHECK:DEADBEEF
//         String uid = cmd.substring(6);
//         uid.toUpperCase();
//         bool auth = isWhitelisted(uid);
//         sendResponse("CHECK", uid, auth ? "AUTORIZADO" : "DENEGADO", "PI_REQUEST");

//     } else if (cmd.startsWith("RFID:")) {
//         // Compatibilidad con el bridge de la Pi
//         String uid = cmd.substring(5);
//         uid.toUpperCase();
//         bool auth = isWhitelisted(uid);
//         sendResponse("SCAN", uid, auth ? "AUTORIZADO" : "DENEGADO", "PI_BRIDGE");

//     } else if (cmd == "MODE:PI") {
//         PI_MODE = true;
//         Serial.println("{\"event\":\"MODE\",\"mode\":\"PI\"}");

//     } else if (cmd == "MODE:STANDALONE") {
//         PI_MODE = false;
//         Serial.println("{\"event\":\"MODE\",\"mode\":\"STANDALONE\"}");

//     } else if (cmd == "PING") {
//         Serial.println("{\"event\":\"PONG\",\"device\":\"PHANTOM-ESP32\"}");

//     } else if (cmd == "LAST_UID") {
//         sendResponse("LAST_UID", lastUID, isWhitelisted(lastUID) ? "AUTORIZADO" : "DENEGADO", "CACHED");

//     } else {
//         Serial.println("{\"event\":\"ERROR\",\"msg\":\"Comando desconocido: " + cmd + "\"}");
//     }
// }

// // ── Loop principal ────────────────────────────────────────────────────────────

// void loop() {
//     // Leer comandos desde Serial (Pi o monitor)
//     if (Serial.available()) {
//         String cmd = Serial.readStringUntil('\n');
//         processCommand(cmd);
//     }

//     // Lectura PN532
//     if (pn532_ok) {
//         String uid = readPN532();
//         if (uid != "") processUID(uid, "PN532");
//     }

//     // Lectura RC522
//     if (rc522_ok) {
//         String uid = readRC522();
//         if (uid != "") processUID(uid, "RC522");
//     }

//     delay(50);
// }

#include <Wire.h>
#include <Adafruit_PN532.h>

// Configuración de pines para el bus I2C
#define SDA_PIN 21
#define SCL_PIN 22

Adafruit_PN532 pn532(SDA_PIN, SCL_PIN);

/**
 * Función forense: Intenta detectar si el chip es una "Magic Card" (Gen1).
 * Envía el comando de backdoor 0x40. Las tarjetas originales NO responden a esto.
 */
bool checkMagicCard() {
  uint8_t magicCmd[] = { 0x40 };
  uint8_t response[64];
  uint8_t responseLen;
  
  // Si hay intercambio exitoso con este comando, el hardware es clonable
  if (pn532.inDataExchange(magicCmd, 1, response, &responseLen)) {
    return true; 
  }
  return false;
}

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);

  pn532.begin();

  uint32_t versiondata = pn532.getFirmwareVersion();
  if (!versiondata) {
    // Si no detecta el módulo, el error sale en JSON para que Python lo entienda
    Serial.println("{\"status\":\"ERROR\",\"msg\":\"PN532_NOT_FOUND\"}");
    while (1);
  }

  pn532.SAMConfig(); // Configurar para lectura de tarjetas
  Serial.println("{\"status\":\"READY\",\"msg\":\"PHANTOM_BRIDGE_ACTIVE\"}");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    // --- COMANDO: SCAN (Auditoría Forense) ---
    if (cmd == "SCAN") {
      uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };
      uint8_t uidLength;

      // Timeout corto (300ms) para no bloquear el sistema si no hay tarjeta
      if (pn532.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 300)) {
        bool is_magic = checkMagicCard();
        
        Serial.print("{\"event\":\"SCAN\",\"status\":\"OK\",\"is_clone\":");
        Serial.print(is_magic ? "true" : "false");
        Serial.print(",\"uid\":\"");
        for (uint8_t i = 0; i < uidLength; i++) {
          if (uid[i] < 0x10) Serial.print("0");
          Serial.print(uid[i], HEX);
        }
        Serial.println("\"}");
      } else {
        Serial.println("{\"event\":\"SCAN\",\"status\":\"ERROR\",\"msg\":\"NO_CARD\"}");
      }
    }

    // --- COMANDO: READ:bloque ---
    else if (cmd.startsWith("READ:")) {
      int block = cmd.substring(5).toInt();
      uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };
      uint8_t uidLength;

      if (pn532.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 500)) {
        uint8_t key[] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
        if (pn532.mifareclassic_AuthenticateBlock(uid, uidLength, block, 0, key)) {
          uint8_t data[16];
          if (pn532.mifareclassic_ReadDataBlock(block, data)) {
            Serial.print("{\"status\":\"READ_OK\",\"block\":" + String(block) + ",\"data\":\"");
            for (int i = 0; i < 16; i++) {
              if (data[i] < 0x10) Serial.print("0");
              Serial.print(data[i], HEX);
            }
            Serial.println("\"}");
          } else {
            Serial.println("{\"status\":\"ERROR\",\"msg\":\"READ_FAILED\"}");
          }
        } else {
          Serial.println("{\"status\":\"ERROR\",\"msg\":\"AUTH_FAILED\"}");
        }
      }
    }

    // --- COMANDO: WRITE:bloque:dataHex ---
    else if (cmd.startsWith("WRITE:")) {
      int firstColon = cmd.indexOf(':');
      int secondColon = cmd.indexOf(':', firstColon + 1);
      int block = cmd.substring(firstColon + 1, secondColon).toInt();
      String hexData = cmd.substring(secondColon + 1);

      uint8_t data[16];
      for (int i = 0; i < 16; i++) {
        String bytePart = hexData.substring(i * 2, i * 2 + 2);
        data[i] = (uint8_t) strtol(bytePart.c_str(), NULL, 16);
      }

      uint8_t uid[] = { 0, 0, 0, 0, 0, 0, 0 };
      uint8_t uidLength;
      if (pn532.readPassiveTargetID(PN532_MIFARE_ISO14443A, uid, &uidLength, 500)) {
        uint8_t key[] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
        if (pn532.mifareclassic_AuthenticateBlock(uid, uidLength, block, 0, key)) {
          if (pn532.mifareclassic_WriteDataBlock(block, data)) {
            Serial.println("{\"status\":\"WRITE_OK\",\"block\":" + String(block) + "}");
          } else {
            Serial.println("{\"status\":\"ERROR\",\"msg\":\"WRITE_FAILED\"}");
          }
        }
      }
    }
  }
}