#include <deprecated.h>
#include <MFRC522.h>
#include <MFRC522Debug.h>
#include <MFRC522Extended.h>
#include <MFRC522Hack.h>
#include <require_cpp11.h>
// -------------------------------- XBee Libs------------------------------------
//#include <Printers.h>
#include <XBee.h>
#include <SoftwareSerial.h>
// --------------------------------  RFID Libs -------------------------------- 
#include <SPI.h>
#include <MFRC522.h>

// ---- XBee vars ----
// Initialize XBee
XBee xbee = XBee();
// This is the XBee broadcast address.  You can use the address of any device you have also.
XBeeAddress64 Coordinator = XBeeAddress64(0x00000000, 0x00000000);
// This sounds backwards, but remember that output from the Arduino is input to the Xbee
// Define NewSoftSerial TX/RX pins
#define ssRX 3
#define ssTX 4
SoftwareSerial nss(ssRX, ssTX);
// Arduino Rx <--> Xbee Tx , Arduino Tx <--> Xbee Rx
// Arduino pin3 <--> Xbee DOUT ,  Arduino pin4 <--> Xbee DIN
// XBeeResponse response = XBeeResponse();   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
// create reusable response objects for responses we expect to handle
ZBExplicitRxResponse explicitrx = ZBExplicitRxResponse();


// ---- RFID vars ----
byte readCard[4];   // Stores scanned ID read from RFID Module
const byte cardUid[4] = { 0xc0, 0xD5, 0x10, 0x7C };
constexpr uint8_t RST_PIN = 9;          // Configurable, see typical pin layout above
constexpr uint8_t SS_PIN = 10;         // Configurable, see typical pin layout above
MFRC522 mfrc522(SS_PIN, RST_PIN);  // Create MFRC522 instance


// door
//int incomingByte = 0;   // for incoming serial data
int mos = 7; // MOsfet gate


void setup() {
        Serial.begin(9600);     // opens serial port, sets data rate to 9600 bps
        pinMode(mos, OUTPUT);   // sets pin 7 as output

        // door
        SPI.begin();      // Init SPI bus
        mfrc522.PCD_Init();   // Init MFRC522
        mfrc522.PCD_DumpVersionToSerial();  // Show details of PCD - MFRC522 Card Reader details
        Serial.println(F("Scan PICC to see UID, SAK, type, and data blocks..."));

        // xBee
        nss.begin(9600);
        // now that they are started, hook the XBee into Software Serial
        xbee.setSerial(nss);

        Serial.println("Initialization all done!");
        delay(3000);
        
}

void loop() {
        // Door default is LOCKED
        digitalWrite(mos, HIGH);

        // doing the read without a timer makes it non-blocking, so
        // you can do other stuff in loop() as well.
        xbee.readPacket();
        if (xbee.getResponse().isAvailable()) {
              // got something
               Serial.print("Frame Type is ");
                // Andrew calls the frame type ApiId, it's the first byte
                // of the frame specific data in the packet.
               Serial.println(xbee.getResponse().getApiId(), HEX);
            
            if (xbee.getResponse().getApiId() == ZB_EXPLICIT_RX_RESPONSE) {
              // got a zb rx packet, the kind this code is looking for
              // now that you know it's a receive packet
              // fill in the values
              xbee.getResponse().getZBExplicitRxResponse(explicitrx);
      
              // this is how you get the 64 bit address out of
              // the incoming packet so you know which device
              // it came from
              Serial.print("Got an rx packet from: ");
              XBeeAddress64 senderLongAddress = explicitrx.getRemoteAddress64();
              print32Bits(senderLongAddress.getMsb());
              Serial.print(" ");
              print32Bits(senderLongAddress.getLsb());
      
              // this is how to get the sender's
              // 16 bit address and show it
              uint16_t senderShortAddress = explicitrx.getRemoteAddress16();
              Serial.print(" (");
              print16Bits(senderShortAddress);
              Serial.println(")");
              
              // this is the actual data you sent
              Serial.println("Received Data: ");
              for (int i = 0; i < explicitrx.getDataLength(); i++) {
                print8Bits(explicitrx.getData()[i]);
                Serial.print(' ');
              }
              // So, for example, you could do something like this:
              handleXbeeRxMessage(explicitrx.getData(), explicitrx.getDataLength());
              Serial.println();
           }

           else if (xbee.getResponse().isError()) {
              // some kind of error happened, I put the stars in so
              // it could easily be found
              Serial.print("************************************* error code:");
              Serial.println(xbee.getResponse().getErrorCode(),DEC);
           }
           
           else {
             Serial.print("Frame Type is not supported");
            
          }  
        
        }
        // 

       // Detect key card for unlocking
       getID(); //
    
}

        




// Helper funtions

void handleXbeeRxMessage(uint8_t *data, uint8_t length){
  // this is just a stub to show how to get the data,
  // and is where you put your code to do something with
  // it.
  for (int i = 0; i < length; i++){
  //    Serial.print(data[i]);
  }
  Serial.println();

  // StratOs Unlock door
  // say what you got:
  Serial.print("I received: ");
  Serial.println(*data);

  if (*data == '0' ){
    // means we received 0
    digitalWrite(mos, LOW);
    delay(7000);
  }
}

void print32Bits(uint32_t dw){
  print16Bits(dw >> 16);
  print16Bits(dw & 0xFFFF);
}


void print16Bits(uint16_t w){
  print8Bits(w >> 8);
  print8Bits(w & 0x00FF);
}

void print8Bits(byte c){
  uint8_t nibble = (c >> 4);
  if (nibble <= 9)
    Serial.write(nibble + 0x30);
  else
    Serial.write(nibble + 0x37);
     
  nibble = (uint8_t) (c & 0x0F);
  if (nibble <= 9)
    Serial.write(nibble + 0x30);
  else
    Serial.write(nibble + 0x37);
}

uint8_t getID() {
  // Getting ready for Reading PICCs
  if ( ! mfrc522.PICC_IsNewCardPresent()) { //If a new PICC placed to RFID reader continue
    return 0;
  }
  if ( ! mfrc522.PICC_ReadCardSerial()) {   //Since a PICC placed get Serial and continue
    return 0;
  }
  // There are Mifare PICCs which have 4 byte or 7 byte UID care if you use 7 byte PICC
  // I think we should assume every PICC as they have 4 byte UID
  // Until we support 7 byte PICCs
  Serial.println(F("Scanned PICC's UID:"));
  for ( uint8_t i = 0; i < 4; i++) {  //
    readCard[i] = mfrc522.uid.uidByte[i];
    Serial.print(readCard[i], HEX);
    
  }
  // stratOS
  bool match = false;
  for ( uint8_t i = 0; i < 4; i++) {  //
            if(readCard[i] == cardUid[i]) {
              match = true;
              Serial.println("Match");
              continue;
            }
            else {
              match = false;
              break;
            }
            
  }

  // unlock stuff
  if(match == true) {
    Serial.println("Unlocking door for 7 seconds");
    digitalWrite(mos, LOW);
    delay(7000);
  }
  
  // end StratOS
  Serial.println("");
  mfrc522.PICC_HaltA(); // Stop reading
  return 1;
}
 

