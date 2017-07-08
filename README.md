# StratOs-XBee
Python APIs for XBee

# Include library
from StratOsXBee import *

# Initialiation
myXB = StratOsXBee('COM7', 9600, 'DEBUG') # 3rd argument optional for logging (DEBUG or INFO)

# StratOs HIGH-LEVEL functinons
myXB.StratOsFullSetup()
myXB.StratOsLightON()
myXB.StratOsLightOFF()
myXB.StratOsLightTOGGLE()
myXB.StratOsDoorON()
myXB.StratOsDoorOFF()



# Low-level functions (won't probably need to call these directly)
*RAW ZDO Commands
myXB.ZDOgetMYAddr('\x00\x13\xa2\x00\x41\x51\x06\xc2') #OK
myXB.ZDOgetMACAddr('\x9b\x93') #OK
myXB.ZDOgetSimpleDesc('\x9B\x93','\x0B')	#OK
myXB.ZDOgetActiveEndpts('\x9b\x93')	#OK
myXB.ZDOgetMatchDesc('\x02', '\x9b\x93', '\x01\x04', ['\x04', ['\x00\x00','\x00\x06','\x00\x08','\x01\x01' ]] )	#OK
myXB.ZDOgetMatchDesc('\x03','\x00\x00', '\xC1\x05', ['\x00', []] )
myXB.ZDOgetLQINeighbor('\x00\x13\xa2\x00\x41\x51\x06\xc2')	# OK
*RAW HA Commands
myXB.HAgetManufacturer('\x00\x17\x88\x01\x02\x1E\xA8\x06', '\x0b')	#OK
myXB.HAgetModelID('\x00\x17\x88\x01\x02\x1E\xA8\x06', '\x0b')	#OK
myXB.HAgetLightStatus('\x00\x17\x88\x01\x02\x1E\xA8\x06', '\x0b')	#OK
myXB.HAturnLightOFF('\x00\x17\x88\x01\x02\x1E\xA8\x06', '\x0b')	#OK
myXB.HAturnLightON('\x00\x17\x88\x01\x02\x1E\xA8\x06', '\x0b')	#OK
myXB.HAturnLightTOGGLE('\x00\x17\x88\x01\x02\x1E\xA8\x06', '\x0b') # OK
*StratOs LOW-LEVEL Commands
myXB.getComponentsList()	# OK ,calls ZDOgetLQINeighbor
myXB.getComponentsHAEndpt()	# OK ,calls ZDOgetMatchDesc
myXB.getComponentsHADeviceInfo # calls ZDOgetSimpleDesc and HAgetManufacturer
myXB.getComponentsDigiEndpt()	# OK
myXB.createLightStoveDoorLists()	# OK
