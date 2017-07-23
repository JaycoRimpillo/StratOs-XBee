from StratOsXBee import *
import time

# StratOsXBee object
myXB = StratOsXBee('COM7', 9600, 'INFO') # 3rd argument optional for logging (DEBUG or INFO)


# Run until keyboard interrupt
while True:
	try:
		time.sleep(0.001)
		# print "Enter a command: 0 = Full Setup, 1 = LightsON, 2 = LightsOFF, 3 = LightsTOGGLE, 4 = LockON, 5 = LockOFF, 6 = GetLightStatus"
		# input = raw_input("")
		
		# if input == '0':
			# myXB.StratOsFullSetup()
		# elif input == '1':
			# #num = raw_input("Enter which light:")
			# #myXB.StratOsLightON(int(num))
			# myXB.StratOsLightON()
		# elif input == '2':
			# #num = raw_input("Enter which light:")
			# #myXB.StratOsLightOFF(int(num))
			# myXB.StratOsLightOFF()
		# elif input == '3':
			# #num = raw_input("Enter which light:")
			# #myXB.StratOsLightTOGGLE(int(num))
			# myXB.StratOsLightTOGGLE()
		# #elif input == '4':
			# #myXB.StratOsDoorON()	
		# elif input == '5':
			# myXB.StratOsDoorOFF()	
		# elif input == '6':
			# myXB.StratOsGetLightStatus()
	except KeyboardInterrupt:
		myXB.terminate()
		break




