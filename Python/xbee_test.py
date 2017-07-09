from StratOsXBee import *
import time

# StratOsXBee object
myXB = StratOsXBee('COM7', 9600, 'INFO') # 3rd argument optional for logging (DEBUG or INFO)


# RAW ZDO Commands
#myXB.ZDOgetMYAddr('\x00\x13\xa2\x00\x41\x51\x06\xc2') #OK
#myXB.ZDOgetMACAddr('\x9b\x93') #OK
#myXB.ZDOgetSimpleDesc('\x9B\x93','\x0B')	#OK
#myXB.ZDOgetActiveEndpts('\x9b\x93')	#OK
#myXB.ZDOgetMatchDesc('\x02', '\x9b\x93', '\x01\x04', ['\x04', ['\x00\x00','\x00\x06','\x00\x08','\x01\x01' ]] )	#OK
#time.sleep(3)
#myXB.ZDOgetMatchDesc('\x03','\x00\x00', '\xC1\x05', ['\x00', []] )

#myXB.ZDOgetLQINeighbor('\x00\x17\x88\x01\x02\x1E\xA8\x06')	# OK
#myXB.ZDOgetLQINeighbor('\x00\x13\xa2\x00\x41\x51\x06\xc2')	# OK
#myXB.ZDOgetLQINeighbor('\x00\x00\x00\x00\x00\x00\x00\x00')	# OK

# RAW HA Commands
#myXB.HAgetManufacturer('\x00\x17\x88\x01\x02\x1E\xA8\x06', '\x0b')	#OK
#myXB.HAgetModelID('\x00\x17\x88\x01\x02\x1E\xA8\x06', '\x0b')	#OK
#myXB.HAgetLightStatus('\x00\x17\x88\x01\x02\x1E\xA8\x06', '\x0b')	#OK
#myXB.HAturnLightOFF('\x00\x17\x88\x01\x02\x1E\xA8\x06', '\x0b')	#OK
#myXB.HAturnLightON('\x00\x17\x88\x01\x02\x1E\xA8\x06', '\x0b')	#OK
#myXB.HAturnLightTOGGLE('\x00\x17\x88\x01\x02\x1E\xA8\x06', '\x0b') # OK

# StratOs LOW-LEVEL Commands
# myXB.getComponentsList()	# OK ,calls ZDOgetLQINeighbor
# myXB.getComponentsHAEndpt()	# OK ,calls ZDOgetMatchDesc
# myXB.getComponentsHADeviceInfo # calls ZDOgetSimpleDesc and HAgetManufacturer
# myXB.getComponentsDigiEndpt()	# OK
# myXB.createLightStoveDoorLists()	# OK

# StratOs HIGH-LEVEL Commands
#myXB.StratOsFullSetup()
#myXB.StratOsLightON( num = 0 )	# Turn on light #1
#myXB.StratOsLightOFF( num = 0 )	# Turn off light #1
#myXB.StratOsLightTOGGLE( num = 0 )	# Toggle light #1






# Todo - High level function for turning on/off


# Run until keyboard interrupt
while True:
	try:
		#time.sleep(0.001)
		print "Enter a command: 0 = Full Setup, 1 = LightsON, 2 = LightsOFF, 3 = LightsTOGGLE, 4 = LockON, 5 = LockOFF"
		input = raw_input("")
		
		if input == '0':
			myXB.StratOsFullSetup()
		elif input == '1':
			#num = raw_input("Enter which light:")
			#myXB.StratOsLightON(int(num))
			myXB.StratOsLightON()
		elif input == '2':
			#num = raw_input("Enter which light:")
			#myXB.StratOsLightOFF(int(num))
			myXB.StratOsLightOFF()
		elif input == '3':
			#num = raw_input("Enter which light:")
			#myXB.StratOsLightTOGGLE(int(num))
			myXB.StratOsLightTOGGLE()
		elif input == '4':
			myXB.StratOsDoorON()	
		elif input == '5':
			myXB.StratOsDoorOFF()	
		
	except KeyboardInterrupt:
		
		myXB.terminate()
		break



