/*******************************************************************************
// SWITCHSCIENCE wiki -- http://trac.switch-science.com/
// AMG88 Arduino Sample
// https://github.com/SWITCHSCIENCE/samplecodes/blob/master/AMG88_breakout/Arduino/AMG88_Arduino/AMG88_Arduino.ino
*******************************************************************************/
//---------------------------------- IR Stuff -----------------------------------
#include <Wire.h>
#define PCTL 0x00
#define RST 0x01
#define FPSC 0x02
#define INTC 0x03
#define STAT 0x04
#define SCLR 0x05
#define AVE 0x07
#define INTHL 0x08
#define TTHL 0x0E
//#define INT0 0x10
#define T01L 0x80
// #define AMG88_ADDR 0x69 // in 7bit. AD_SEL tied to VCC
#define AMG88_ADDR 0x68		//Jayco: AD_SEL tied to GND
#define ONEFPS	B00000000
#define TENFPS	B00000001


// -------------------------------- XBee Stuff------------------------------------

#include <Printers.h>
#include <XBee.h>
#include <SoftwareSerial.h>

// Initialize XBee
XBee xbee = XBee();
// This is the XBee broadcast address.  You can use the address of any device you have also.
XBeeAddress64 Coordinator = XBeeAddress64(0x00000000, 0x00000000);
// Arduino Rx <--> Xbee Tx , Arduino Tx <--> Xbee Rx
// This sounds backwards, but remember that output from the Arduino is input to the Xbee

// Define NewSoftSerial TX/RX pins
#define ssRX 3
#define ssTX 4
SoftwareSerial nss(ssRX, ssTX);
// Arduino pin3 <--> Xbee Tx ,  Arduino pin4 <--> Xbee Rx

XBeeResponse response = XBeeResponse();
// create reusable response objects for responses we expect to handle
// ZBRxResponse rx = ZBRxResponse();

#define DEBUG
int count = 1;


void setup()
{
	// Initialize IRSensor
	initIR();

	// start serial
	Serial.begin(9600);
	// and the software serial port
	nss.begin(9600);
	// now that they are started, hook the XBee into Software Serial
	xbee.setSerial(nss);

	Serial.println("Initialization all done!");
	delay(3000);
}

void loop()
{
    // Wire library cannnot contain more than 32 bytes in bufffer
    // 2byte per one data
    // 2 byte * 16 data * 4 times
    int sensorData[32];
    float temperature[64];


    for(int i = 0; i < 4; i++)
    {
        // read each 32 bytes
        dataread(AMG88_ADDR, T01L + i*0x20, sensorData, 32);
        for(int l = 0 ; l < 16 ; l++)
        {
            int16_t temporaryData = (sensorData[l * 2 + 1] * 256 ) + sensorData[l * 2];

            if(temporaryData > 0x800)
            {
                temperature[l+(16*i)] = (-temporaryData +  0xfff) * -0.25;
            }else
            {
                temperature[l+(16*i)] = temporaryData * 0.25;
            }
            
        }
    }

   	Serial.println("[");
   
	char Payload[256]={0};
	char tempstr[3]; // Ex: -15
	// Send 64 pixels each transmission.
		for(int p = 0; p < 64; p++)
		{
            //char* itoa(int val,char *s,int radix)
			itoa( (int)temperature[p], tempstr, 10);
			strcat(Payload, tempstr);
                        Serial.print(tempstr);
			if(p < 63) {
				strcat(Payload, ",");
                                Serial.print(",");
                        }
		}
		
		#ifdef DEBUG
		// Send number of transmissions sent instead of temperature values
		//char *strcpy(char *dest, const char *src)
		char DebugMsg[] = "This is a debug message. Number of transmissions sent since power up = ";
		strcpy(Payload, DebugMsg);
		itoa( count, tempstr, 10);
		strcat(Payload, tempstr );
		#endif		//Serial.println(Payload);
		// ZBExplicitTxRequest(XBeeAddress64 &addr64, uint16_t addr16, uint8_t broadcastRadius,
		//	uint8_t option, uint8_t *payload, uint8_t payloadLength, uint8_t frameId, uint8_t srcEndpoint,
		//	uint8_t dstEndpoint, uint16_t clusterId, uint16_t profileId);
		ZBExplicitTxRequest zbtx = ZBExplicitTxRequest(Coordinator, 0x0000, 0x00,
			0x00, (uint8_t*)Payload, strlen(Payload), 0x01, 0xE8,
			0xE8, 0x0011, 0xC105);
		xbee.send(zbtx);

       Serial.println("]");



    delay(100);
	count++;
}


// IRSensor Functions
void initIR()
{
	Wire.begin();

    int fpsc = B00000001;	// 10fps
    datasend(AMG88_ADDR,FPSC,&fpsc,1);
    int intc = 0x00; // diff interrpt mode, INT output reactive
    datasend(AMG88_ADDR,INTC,&intc,1);
    // moving average output mode active
    int tmp = 0x50;
    datasend(AMG88_ADDR,0x1F,&tmp,1);
    tmp = 0x45;
    datasend(AMG88_ADDR,0x1F,&tmp,1);
    tmp = 0x57;
    datasend(AMG88_ADDR,0x1F,&tmp,1);
    tmp = 0x20;
    datasend(AMG88_ADDR,AVE,&tmp,1);
    tmp = 0x00;
    datasend(AMG88_ADDR,0x1F,&tmp,1);

}

int datasend(int id,int reg,int *data,int datasize)
{
    Wire.beginTransmission(id);
    Wire.write(reg);
    for(int i=0;i<datasize;i++)
    {
        Wire.write(data[i]);
    }
    Wire.endTransmission();
}

int dataread(int id,int reg,int *data,int datasize)
{
    Wire.beginTransmission(id);
    Wire.write(reg);
    Wire.endTransmission(false);
    Wire.requestFrom(id, datasize, false);
    for(int i=0;i<datasize;i++)
    {
        data[i] = Wire.read();
    }
    Wire.endTransmission(true);
}
