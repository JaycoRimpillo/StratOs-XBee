import serial
from xbee import ZigBee 
import logging 	#DEBUG, INFO, WARNING, ERROR, CRITICAL
from collections import OrderedDict
import time

# NOTE: ZDO PAYLOAD IS LITTLE ENDIAN FOR EACH FIELD (Least Significant Byte first)
ZDO_Payload = {
	"0000_MYAddr_Req": OrderedDict([
		('Trans', '\x01'),
		('MACAddr', '\xEF\xCD\xAB\x88\x67\x45\x23\x01'),
		('ReqType', '\x00') # 00 = single device response
	]),
	
	"0001_MACAddr_Req": OrderedDict([
		('Trans', '\x01'),
		('MYAddr', '\x34\x12'),
		('ReqType', '\x00') # 00 = single device response
	]),
	
	"0004_SimpleDesc_Req": OrderedDict([
		('Trans', '\x01'),
		('MYAddr', '\x34\x12'),
		('Endpoint', '\x00') # The endpoint on the destination from which to obtain the simple descriptor.
	]),
	
	"0005_ActiveEndpts_Req": OrderedDict([
		('Trans', '\x01'),
		('MYAddr', '\x34\x12')
	]),
	
	"0006_MatchDesc_Req": OrderedDict([
		('Trans', '\x01'),
		('MYAddr', '\x34\x12'),
		('Profile', '\x34\x12')
	]),
	
	"0030_MgmtND_Req": OrderedDict([
		('Trans', '\x01'),
		('ScanChan', '\x00\xF8\xFF\x07'), # Scan all channels ([11 to 26)
		('ScanDur', '\x03'),
		('StartIdx', '\x00')
	]),
	
	"0031_MgmtLQI_Req": OrderedDict([
		('Trans', '\x01'),
		('StartIdx','\x00')
	]),

	"0032_MgmtRtg_Req": OrderedDict([
		('Trans', '\x01'),
		('StartIdx', '\x00')
	])
}

# NOTE: HA PAYLOAD IS LITTLE ENDIAN FOR EACH FIELD (Least Significant Byte first)
HA_Payload = OrderedDict([
		('FrameCtl', '\x01'),
		('Trans', '\x01'),
		('Cmd', '\x00')
])


class StratOsXBee(object):
	
	COORDINATOR_EQUIV_MAC = '\x00\x00\x00\x00\x00\x00\x00\x00'
	UNKNOWN_EQUIV_MAC = '\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'
	BROADCAST_EQUIV_MAC = '\x00\x00\x00\x00\x00\x00\xFF\xFF'
	UNKNOWN_EQUIV_MY = '\xFF\xFE'
	
	def __init__(self, XBeePort, XBeeBaudRate, logLevel = 'WARNING'):
		# Format is : myXB = StratOsXBee('COM7', 9600, 'DEBUG')
		# Create logger
		self.logger = logging.getLogger('XBEE_logger')
		if logLevel == 'DEBUG':
			self.logger.setLevel(logging.DEBUG)
		elif logLevel == 'INFO':
			self.logger.setLevel(logging.INFO)
		else:
			pass # default level is WARNING
			
		self.ch = logging.StreamHandler()
		self.logger.addHandler(self.ch)
		#self.logger.debug('debug')
		#self.logger.info('info')
		#self.logger.warning('warning')
		
		# Initialize Port and XBee instance
		self.XBeePort = XBeePort
		self.XBeeBaudRate = XBeeBaudRate
		self.XBeeSer = serial.Serial(self.XBeePort, self.XBeeBaudRate)
		time.sleep(0.5)
		self.XBeeObj = ZigBee(self.XBeeSer, callback= self.rxHandler )
		time.sleep(0.5)
		
		# Class variables
		self.CoordActualMACList = [0,0,0,0,0,0,0,0]
		self.COORD_ACTUAL_MAC = ''
		self.ComponentsList = []
		self.LightsList = []
		self.StoveList = []
		self.DoorList = []
		
		# Initialization functions
		self.getCoordinatorInfo()	# Call this to get the self values
		
		self.StratOsFullSetup()	# call this to populate the components list, door list, light list, stove list
		
		
		
	#************************ START OF self.RX_Handler() **********
	def rxHandler(self, data):
		self.logger.debug( data )
		# Local AT Command Responses
		if(data["id"]=='at_response'):
			if data["command"]=='NI':
				self.logger.debug( data["command"] + ' ' + data["parameter"] )
			else:
				# print hex values
				temp = []
				for x in data["parameter"]:
					temp.append( hex(ord(x)) )
				self.logger.debug( data["command"] + ' ' + ' '.join(temp) )
				
		
			# Assign values
			if(data["command"]=='SH'):
				for x in range(0,4):
					self.CoordActualMACList[x] = data["parameter"][x]
				self.COORD_ACTUAL_MAC = ''.join(self.CoordActualMACList)
			
			elif(data["command"]=='SL'):
				for x in range(4,8):
					self.CoordActualMACList[x] = data["parameter"][x-4]
				self.COORD_ACTUAL_MAC = ''.join(self.CoordActualMACList)
		
		# Remote AT Command Response
		elif(data["id"]=='remote_at_response'):
		# Print general info
			self.logger.debug( "--------- Start of Remote AT Command response ---------" )
			self.logger.debug( "Source MAC: " + str([ hex(ord(x)) for x in data["source_addr_long"] ]) )
			self.logger.debug( "Source MY: " + str([ hex(ord(x)) for x in data["source_addr"] ]) )
	
			if data["command"]=='NI':
				self.logger.debug( data["command"] + ' ' + data["parameter"] )
			## SAVE DEVICE TYPE IF IN COMPONENTS LIST
				nodeid = data["parameter"]
				for elem in self.ComponentsList:
					if elem['MAC'] == data["source_addr_long"]:
						elem['NodeID'] = nodeid		# StratOsDoor or StratOsStove
			##
			self.logger.debug( "--------- End of Remote AT Command response ---------" )
		
		
		# API RX Explicit Responses
		elif data["id"]=='rx_explicit':
			# Print general info
			self.logger.debug( "--------- Start of RX_Explicit response ---------" )
			self.logger.debug( "Source MAC: " + str([ hex(ord(x)) for x in data["source_addr_long"] ]) )
			self.logger.debug( "Source MY: " + str([ hex(ord(x)) for x in data["source_addr"] ]) )
			self.logger.debug( "Profile: " + str([ hex(ord(x)) for x in data["profile"] ]) )
			self.logger.debug( "Cluster: " + str([ hex(ord(x)) for x in data["cluster"] ]) )
			self.logger.debug( "Src_endpt: " + hex(ord(data["source_endpoint"])) + " Dest_endpt: " + hex(ord(data["dest_endpoint"])) )
				
			# "Normal" Digi Responses (STOVE STUFF)
			if data["profile"]=='\xC1\x05':
				for elem in self.ComponentsList:
					if elem['NodeID'] == "StratOsStove":
						print "GOT STOVE DATA"
						print "MAC:" + str([ hex(ord(x)) for x in data["source_addr_long"] ])
						#print "MAC:" + ''.join(data["source_addr_long"]).encode('utf8')
						print "64-values:" + data["rf_data"]
					elif elem['NodeID'] == "StratOsDoor":
						print "GOT DOOR STATUS"
						print "MAC:" + str([ hex(ord(x)) for x in data["source_addr_long"] ])
						#print "MAC:" + ''.join(data["source_addr_long"]).encode('utf8')
						print data["rf_data"]
					else:
						print "StratOs does not support this device yet"
						
			
			# ZDO Responses (Profile = 0x0000)
			elif data["profile"]=='\x00\x00': 
				# ZDO Network Addr Resp
				if data["cluster"]=='\x00\x13':
					self.logger.info( 'A Device has joined the network. ' + 'MAC = ' +  str([ hex(ord(x)) for x in data["source_addr_long"] ]))
				
				# ZDO Network Addr Resp
				elif data["cluster"]=='\x80\x00':
					self.logger.debug( 'ZDO Network Addr Resp ' + '(Profile = 0x0000 Cluster = 0x8000)' )
					self.logger.debug( 'Trans#: ' + hex(ord(data["rf_data"][0])) )
					self.logger.debug( 'Status: ' + hex(ord(data["rf_data"][1])) )
					self.logger.debug( 'MAC: ' + str([ hex(ord(x)) for x in data["rf_data"][9:1:-1] ]) )
					self.logger.debug( 'MY: ' + str([ hex(ord(x)) for x in data["rf_data"][11:9:-1] ]) )
				
				# ZDO MAC Addr Resp
				elif data["cluster"]=='\x80\x01':
					self.logger.debug( 'ZDO MAC Addr Resp ' + '(Profile = 0x0000 Cluster = 0x8001)' )
					self.logger.debug( 'Trans#: ' + hex(ord(data["rf_data"][0])) )
					self.logger.debug( 'Status: ' + hex(ord(data["rf_data"][1])) )
					self.logger.debug( 'MAC: ' + str([ hex(ord(x)) for x in data["rf_data"][9:1:-1] ]) )
					self.logger.debug( 'MY:' + str([ hex(ord(x)) for x in data["rf_data"][11:9:-1] ]) )
				
				# ZDO Simple Desc Resp
				elif data["cluster"]=='\x80\x04':
					self.logger.debug( 'ZDO Simple Desc Resp ' + '(Profile = 0x0000 Cluster = 0x8004)' )
					self.logger.debug( 'Trans#: ' + hex(ord(data["rf_data"][0])) )
					self.logger.debug( 'Status: ' + hex(ord(data["rf_data"][1])) )
					self.logger.debug( 'MY: ' + str([ hex(ord(x)) for x in data["rf_data"][3:1:-1] ]) )
					self.logger.debug( 'Len: ' + hex(ord(data["rf_data"][4])) )
					self.logger.debug( 'Endpt: '+ hex(ord(data["rf_data"][5])) )
					self.logger.debug( 'Supp Profile: '+ str([ hex(ord(x)) for x in data["rf_data"][7:5:-1] ]) )
					self.logger.debug( 'Device ID: '+ str([ hex(ord(x)) for x in data["rf_data"][9:7:-1] ]) )
					
					## SAVE DEVICE TYPE IF IN COMPONENTS LIST
					deviceid = data["rf_data"][9:7:-1]
					for elem in self.ComponentsList:
						if elem['MAC'] == data["source_addr_long"]:
							elem['DeviceID'] = deviceid
							if deviceid == '\x01\x00':
								elem['DeviceIDName'] = 'ONOFFLight'
							break
					##
					
					self.logger.debug( 'Device Version: ' + hex(ord(data["rf_data"][10])) )
					self.logger.debug( 'In cluster count: ' + hex(ord(data["rf_data"][11])) )
					for c in range(ord(data["rf_data"][11])):
						self.logger.debug( str( [ hex(ord(x)) for x in data["rf_data"][11+2*(c+1):11+2*(c):-1] ] )  )
						
					Outcountidx = 11+2*ord(data["rf_data"][11]) + 1
					self.logger.debug( 'Out cluster count: ' + hex(ord(data["rf_data"][Outcountidx])) )
					for c in range(ord(data["rf_data"][Outcountidx])):
						self.logger.debug( str([ hex(ord(x)) for x in data["rf_data"][Outcountidx+2*(c+1):Outcountidx+2*(c):-1] ]) )
					
				# ZDO Active Endpts Resp
				elif data["cluster"]=='\x80\x05':
					self.logger.debug( 'ZDO Active Endpts Resp ' + '(Profile = 0x0000 Cluster = 0x8005)' )
					self.logger.debug( 'Trans#: ' + hex(ord(data["rf_data"][0])) )
					self.logger.debug( 'Status: ' + hex(ord(data["rf_data"][1])) )
					self.logger.debug( 'MY: ' + str([ hex(ord(x)) for x in data["rf_data"][3:1:-1] ]) )
					self.logger.debug( '# of endpts: ' + hex(ord(data["rf_data"][4])) )
					numendpts = range(ord(data["rf_data"][4]))
					for c in numendpts:
						self.logger.debug(  hex(ord(data["rf_data"][5+c])) )
					
					
				
				# ZDO Match Desc Resp
				elif data["cluster"]=='\x80\x06':
					self.logger.debug( 'ZDO Match Desc Resp '+ '(Profile = 0x0000 Cluster = 0x8006)' )
					self.logger.debug( 'Trans#: ' + hex(ord(data["rf_data"][0])) )
					transnum = ord(data["rf_data"][0])
					self.logger.debug( 'Status: ' + hex(ord(data["rf_data"][1])) )
					self.logger.debug( 'MY: ' + str([ hex(ord(x)) for x in data["rf_data"][3:1:-1] ]) )
					self.logger.debug( '# of endpts: ' + hex(ord(data["rf_data"][4])) )
					numendpts = range(ord(data["rf_data"][4]))
					for c in numendpts:
						self.logger.debug(  hex(ord(data["rf_data"][5+c])) )
					
					# ONLY SAVE VALUES IF THERE ARE ENDPTS AND MATCH MAC !!!
					if numendpts != []:
						lastendpt = data["rf_data"][-1]
						for elem in self.ComponentsList:
							if elem['MAC'] == data["source_addr_long"]:
								if transnum == 0x2:
									elem["HAEndpt"] = lastendpt
									break
								elif transnum == 0x3:
									elem["DigiEndpt"] = lastendpt
									break
								
					# END OF SAVING VALUES

							
				
				# ZDO LQI Neighbor Resp
				elif data["cluster"]=='\x80\x31':
					self.logger.debug( 'ZDO LQI Neighbor Resp '+ '(Profile = 0x0000 Cluster = 0x8031)' )
					self.logger.debug( 'Trans#: ' + hex(ord(data["rf_data"][0])) )
					self.logger.debug( 'Status: ' + hex(ord(data["rf_data"][1])) )
					self.logger.debug( 'TotalCount: ' + hex(ord(data["rf_data"][2])) )
					self.logger.debug( 'StartIdx: ' + hex(ord(data["rf_data"][3])) )
					self.logger.debug( 'Count: ' + hex(ord(data["rf_data"][4])) )
					# ONLY CLEAR COMPONENTS LIST IF SOURCE IS THE COORDINATOR !!!
					if data["source_addr_long"]==self.COORD_ACTUAL_MAC:
						self.ComponentsList = []
					
					# For each neighbor device:
					for c in range(ord(data["rf_data"][4])): # (0 to Ccount-1)
						self.logger.debug( '-----Neighbor #'+str(c+1)+"-----" )
						first = 5+(c*22)
						last = 26+(c*22)
						self.logger.debug( 'PAN_64: ' + str([ hex(ord(x)) for x in data["rf_data"][first+7:first-1:-1] ]) )
						temp_MAC = data["rf_data"][first+15:first+7:-1]
						self.logger.debug( 'MAC: ' + str([ hex(ord(x)) for x in temp_MAC ]) )
						temp_MY = data["rf_data"][first+17:first+15:-1]
						self.logger.debug( 'MY: ' + str([ hex(ord(x)) for x in temp_MY ]) )
						
						devinfo = ord(data["rf_data"][first+18])
						rel = (devinfo >> 4) & (0b1111)
						if rel == 0x0:
							self.logger.debug( "Neighbor is the parent")
						elif rel == 0x1:
							self.logger.debug( "Neighbor is a child")
						elif rel == 0x2:
							self.logger.debug( "Neighbor is a sibling")
						elif rel == 0x3:
							self.logger.debug( "Neighbor is not parent/child/sibling. Probably a router")
						elif rel == 0x4:
							self.logger.debug( "Previous child"	)
						rxonidle = (devinfo >> 2) & (0b11)
						if rxonidle == 0x0:
							self.logger.debug( "Neighbor Receiver is off when idle")
						elif rxonidle == 0x1:
							self.logger.debug( "Neighbor Receiver is on when idle")
						elif rxonidle == 0x2:
							self.logger.debug( "Unknown Neighbor rxonidle"	)
						type = devinfo & (0b11)
						if type == 0x0:
							self.logger.debug( "Neighbor is Zigbee coordinator")
						elif type == 0x1:
							self.logger.debug( "Neighbor is Zigbee router")
						elif type == 0x2:
							self.logger.debug( "Neighbor is Zigbee end device")
						elif type == 0x3:
							self.logger.debug( "Unknown neighbor type")
							
						permitjoin = ord(data["rf_data"][first+19]) & (0b11)
						if permitjoin == 0x0:
							self.logger.debug( "Neighbor not accepting joins")
						elif permitjoin == 0x1:
							self.logger.debug( "Neighbor is accepting joins")
						elif permitjoin == 0x2:
							self.logger.debug( "Unknown Neighbor permit join"	)
						
						self.logger.debug( "Depth: " + str(ord(data["rf_data"][first+20]) ) )
						self.logger.debug( "LQI: " + str( ord(data["rf_data"][first+21]) ) )
						
						# ONLY SAVE VALUES IF SOURCE IS THE COORDINATOR !!!
						if data["source_addr_long"]==self.COORD_ACTUAL_MAC:
							tempdict = {'MAC': temp_MAC,  'MY': temp_MY}
							if tempdict.copy() not in self.ComponentsList:
								# Be careful with .append(dict)!!!!
								# Looks like list gets updated when append with orig dict
								# That's why .append(dict.copy()) is used here instead
								self.ComponentsList.append(tempdict.copy())
						# END OF SAVING VALUES
					# End for each device	
					
					
				# Else Response frame not yet supported		
				else:
					self.logger.debug( 'Processing this ZDO Cluster ID response not implemented yet' )
				
			# HA Responses (Profile = 0x0104)
			elif data["profile"]=='\x01\x04':
				if data["cluster"]=='\x00\x00' and data["rf_data"][2]=='\x01' and (data["rf_data"][4:2:-1]=='\x00\x04' or data["rf_data"][4:2:-1]=='\x00\x05'):
					self.logger.debug( 'HA General Cluster: Read Attr Resp '+ '(Profile = 0x0104 Cluster = 0x0000)' )
					if data["rf_data"][4:2:-1]=='\x00\x04':
						self.logger.debug( 'Read Manufacturer Attr' )
					elif data["rf_data"][4:2:-1]=='\x00\x05':
						self.logger.debug( 'Read Model ID Attr' )
					self.logger.debug( 'Frame Ctl: ' + hex(ord(data["rf_data"][0])) )
					self.logger.debug( 'Trans#: ' + hex(ord(data["rf_data"][1])) )
					self.logger.debug( 'Cmd: ' + hex(ord(data["rf_data"][2])) )
					self.logger.debug( 'Attr: ' + str([hex(ord(x)) for x in data["rf_data"][4:2:-1] ]) )
					self.logger.debug( 'Status: ' + hex(ord(data["rf_data"][5])) )
					self.logger.debug( 'Data type: '+ hex(ord(data["rf_data"][6])) )	#0x42: characters
					self.logger.debug( 'Numel: '+ hex(ord(data["rf_data"][7])) )
					self.logger.debug( ''.join(data["rf_data"][8:]) )
					
					## SAVE DEVICE TYPE IF IN COMPONENTS LIST
					value = ''.join(data["rf_data"][8:])
					for elem in self.ComponentsList:
						if elem['MAC'] == data["source_addr_long"]:
							if data["rf_data"][4:2:-1]=='\x00\x04':
								elem['Manufct'] = value
							elif data["rf_data"][4:2:-1]=='\x00\x05':
								elem['Model'] = value
							break
					##
		
						
				elif data["cluster"]=='\x00\x06' and data["rf_data"][2]=='\x01' and data["rf_data"][4:2:-1]=='\x00\x00':
					self.logger.debug( 'HA On/Off Cluster: Read Attr Resp '+ '(Profile = 0x0104 Cluster = 0x0006)' )
					self.logger.debug( 'Read Status(on/off) of Light' )
					self.logger.debug( 'Frame Ctl: ' + hex(ord(data["rf_data"][0])) )
					self.logger.debug( 'Trans#: ' + hex(ord(data["rf_data"][1])) )
					self.logger.debug( 'Cmd: ' + hex(ord(data["rf_data"][2])) )	#0x01: Read attributes response
					self.logger.debug( 'Attr: ' + str([hex(ord(x)) for x in data["rf_data"][4:2:-1] ]) )
					self.logger.debug( 'Status: ' + hex(ord(data["rf_data"][5])) )
					self.logger.debug( 'Data type: '+ hex(ord(data["rf_data"][6])) )   #0x10: logical
					if ord(data["rf_data"][7])==0x0:
						print "GOT BULB STATUS"
						print "Light is OFF" 
					elif rd(data["rf_data"][7])==0x1:
						print "GOT BULB STATUS"
						print "Light is ON" 
		
						
				elif data["cluster"]=='\x00\x06' and data["rf_data"][2]=='\x0B' and (data["rf_data"][3]=='\x00' or data["rf_data"][3]=='\x01' or data["rf_data"][3]=='\x02'):
					self.logger.debug( 'HA On/Off Cluster: Default Resp '+ '(Profile = 0x0104 Cluster = 0x0006)' )
					self.logger.debug( 'On/Off/Toggle command response' )
					self.logger.debug( 'Frame Ctl: ' + hex(ord(data["rf_data"][0])) )
					self.logger.debug( 'Trans#: ' + hex(ord(data["rf_data"][1])) )
					self.logger.debug( 'AttrCmd: ' + hex(ord(data["rf_data"][2])) ) # xOB = default resp
					self.logger.debug( 'ClusterCmd: ' + hex(ord(data["rf_data"][3])) )
					self.logger.debug( 'Status: ' + hex(ord(data["rf_data"][4])) )
					ClusterCmd = ord(data["rf_data"][3])
					if ClusterCmd == 0x0:
						self.logger.debug( "Turn OFF cmd:" )
					elif ClusterCmd == 0x1:
						self.logger.debug( "Turn ON cmd:" )
					elif ClusterCmd == 0x2:
						self.logger.debug( "TOGGLE cmd:"  )
					Status = ord(data["rf_data"][4])
					if Status == 0x00:
						self.logger.debug( "Success" )
					else:
						self.logger.debug( "Probably failed" )
						
				
					
				# Else Response frame not yet supported	
				else:
					self.logger.debug( 'Processing this HA Cluster ID response not implemented yet' )
			
			
			self.logger.debug( "--------- End of RX_Explicit response ---------" )
	
	#************************ END OF self.RX_Handler() ************
	
	# ************* StratOs LOW-LEVEL COMMANDS *****************
	def getCoordinatorInfo(self):
		self.XBeeObj.send('at', command='OP') # OP 64-bit PAN ID
		self.XBeeObj.send('at', command = 'OI') # OP 16-bit PAN ID
		self.XBeeObj.send('at', command = 'ZS') # ZigBee Stack Profile
		self.XBeeObj.send('at', command = 'CH') # OP channel
		self.XBeeObj.send('at', command = 'CE') # Coordinator enable
		self.XBeeObj.send('at', command = 'SH') # Upper 32 bits of MAC Addr
		self.XBeeObj.send('at', command = 'SL') # Lower 32 bits of MAC Addr
		self.XBeeObj.send('at', command = 'NI') # Node Identifier
		self.XBeeObj.send('at', command = 'EE') # Encryption enabled
		self.XBeeObj.send('at', command = 'AP') # API enabled
		self.XBeeObj.send('at', command = 'AO') # API output mode
		self.XBeeObj.send('at', command = 'AI') # Association indicator
	
		
	def getComponentsList(self):
		# Dicover all devices that are currently connected to coordinator (Hub)
		self.ZDOgetLQINeighbor(self.COORDINATOR_EQUIV_MAC)
		time.sleep(3) # Need delay
		self.logger.info( '----------- In getComponentsList ----------' )
		self.logger.info( 'ComponentsList:' )
		for elem in self.ComponentsList:
			self.logger.info( elem )
			
		self.logger.info( '----------- End of getComponentsList ----------' )
		
	def getComponentsHAEndpt(self):
		#ZDOgetMatchDesc(self, MY, Profile, Clustinfo)
		# MY should have this form: '\x12\x34'
		# Profile should have this form: '\x12\x34'
		# Clustinfo should be list: ['\x04', ['\x00\x00','\x00\x06','\x00\x08','\x01\x01' ] ]
		
		for elem in self.ComponentsList:
			self.ZDOgetMatchDesc( '\x02', elem["MY"], '\x01\x04', ['\x04', ['\x00\x00','\x00\x06','\x00\x08','\x01\x01'] ] )
		
		time.sleep(3)	# delay
		
		self.logger.info( '----------- In getComponentsHAEndpt ----------' )
		self.logger.info( 'ComponentsList:' )
		for elem in self.ComponentsList:
			self.logger.info( elem )
			
		self.logger.info( '----------- End of getComponentsHAEndpt ----------' )
	
	def getComponentsDigiEndpt(self):
		#ZDOgetMatchDesc(self, MY, Profile, Clustinfo)
		# MY should have this form: '\x12\x34'
		# Profile should have this form: '\x12\x34'
		# Clustinfo should be list: ['\x04', ['\x00\x00','\x00\x06','\x00\x08','\x01\x01' ] ]
		
		for elem in self.ComponentsList:
			self.ZDOgetMatchDesc( '\x03', elem["MY"], '\xC1\x05', ['\x00', []])
	
		time.sleep(3)	# delay
	
		self.logger.info( '----------- In getComponentsDigiEndpt ----------' )
		self.logger.info( 'ComponentsList:' )
		for elem in self.ComponentsList:
			self.logger.info( elem )
			
		self.logger.info( '----------- End of getComponentsDigiEndpt ----------' )
	
	
	def getComponentsHADeviceInfo(self):
		# MY should have this form: '\x12\x34'
		# endpt has form: '\x12'
		#ZDOgetSimpleDesc(self, MY, endpt)
		# HAgetManufacturer(self, MAC, destendpt):
		# MAC should have this form: '\x01\x23\x45\x67\x89\xAB\xCD\xEF'
		# destendpt form: '\x12'
		for elem in self.ComponentsList:
			if elem.has_key('HAEndpt'):
				self.ZDOgetSimpleDesc( elem["MY"], elem["HAEndpt"] )	# get devicdeID
				self.HAgetManufacturer( elem["MAC"], elem["HAEndpt"] )
		
		time.sleep(3)	# delay
		
		self.logger.info( '----------- In getComponentsHADeviceInfo ----------' )
		self.logger.info( 'ComponentsList:' )
		for elem in self.ComponentsList:
			self.logger.info( elem )
			
		self.logger.info( '----------- End of getComponentsHADeviceInfo ----------' )		
	
	def getComponentsDigiDeviceInfo(self):
		for elem in self.ComponentsList:
			if elem.has_key('DigiEndpt'):
				self.XBeeObj.send('remote_at',
					frame_id = '\x01', # This is important! Otherwise will get no response
					dest_addr_long = elem['MAC'],
					dest_addr = self.UNKNOWN_EQUIV_MY,
					command = 'NI'
				)

		time.sleep(3)
				
		self.logger.info( '----------- In getComponentsDigiDeviceInfo ----------' )
		self.logger.info( 'ComponentsList:' )
		for elem in self.ComponentsList:
			self.logger.info( elem )
			
		self.logger.info( '----------- End of getComponentsDigiDeviceInfo ----------' )		
	
	
	
	
	def createLightStoveDoorLists(self):
		temp = self.ComponentsList
		for elem in temp:
			if elem.has_key('DeviceIDName'):
				if elem['DeviceIDName'] == 'ONOFFLight':
					self.LightsList.append( elem )
			elif elem.has_key('NodeID'):
				if elem['NodeID'] == 'StratOsStove':
					self.StoveList.append( elem )
				elif elem['NodeID'] == 'StratOsDoor':
					self.DoorList.append( elem )
		
		self.logger.info( '\n' )
		self.logger.info( '-----------------LightsList---------------------' )
		for (idx, elem) in enumerate(self.LightsList):
			self.logger.info( '[' + str(idx) + ']: ' + str(elem) )

		self.logger.info( '\n' )
		self.logger.info( '-----------------StoveList---------------------' )
		for (idx, elem) in enumerate(self.StoveList):
			self.logger.info( '[' + str(idx) + ']: ' + str(elem) )
			
		self.logger.info( '\n' )
		self.logger.info( '-----------------DoorList---------------------' )
		for (idx, elem) in enumerate(self.DoorList):
			self.logger.info( '[' + str(idx) + ']: ' + str(elem) )
	
	############# StratOs HIGH-LEVEL COMMANDS ####################
	def StratOsFullSetup(self):
		self.getComponentsList()		# OK ,calls ZDOgetLQINeighbor
		self.getComponentsHAEndpt()		# OK ,calls ZDOgetMatchDesc
		self.getComponentsHADeviceInfo()	# calls ZDOgetSimpleDesc
		self.getComponentsDigiEndpt()	# OK
		self.getComponentsDigiDeviceInfo()		# Not yet tested
		self.createLightStoveDoorLists()	# OK
	
	def StratOsLightON(self, num = 0):
		if len(self.LightsList) != 0:
			# HAturnLightON(self, MAC, destendpt):
			# MAC should have this form: '\x01\x23\x45\x67\x89\xAB\xCD\xEF'
			# destendpt form: '\x12'
			self.HAturnLightON( self.LightsList[num]['MAC'], self.LightsList[num]['HAEndpt'] )
			
			time.sleep(1)
			
	def StratOsLightOFF(self, num = 0):
		if len(self.LightsList) != 0:
			# HAturnLightOFF(self, MAC, destendpt):
			# MAC should have this form: '\x01\x23\x45\x67\x89\xAB\xCD\xEF'
			# destendpt form: '\x12'
			self.HAturnLightOFF( self.LightsList[num]['MAC'], self.LightsList[num]['HAEndpt'] )
			
			time.sleep(1)
	
	def StratOsLightTOGGLE(self, num = 0):
		if len(self.LightsList) != 0:
			# HAturnLightTOGGLE(self, MAC, destendpt):
			# MAC should have this form: '\x01\x23\x45\x67\x89\xAB\xCD\xEF'
			# destendpt form: '\x12'
			self.HAturnLightTOGGLE( self.LightsList[num]['MAC'], self.LightsList[num]['HAEndpt'] )
			
			time.sleep(1)

	def StratOsDoorON(self, num = 0):
		if len(self.DoorList) != 0:
			self.XBeeObj.send('tx_explicit',
				dest_addr_long = self.DoorList[num]['MAC'],
				dest_addr = self.UNKNOWN_EQUIV_MY,
				src_endpoint = '\xE8',
				dest_endpoint = '\xE8',
				cluster = '\x00\x11', # 
				profile = '\xC1\x05', # Digi profile
				data = '1'
			)
			
			time.sleep(1)			
			
	def StratOsDoorOFF(self, num = 0):
		if len(self.DoorList) != 0:
			self.XBeeObj.send('tx_explicit',
				dest_addr_long = self.DoorList[num]['MAC'],
				dest_addr = self.UNKNOWN_EQUIV_MY,
				src_endpoint = '\xE8',
				dest_endpoint = '\xE8',
				cluster = '\x00\x11', # 
				profile = '\xC1\x05', # Digi profile
				data = '0'
			)
			
			time.sleep(1)	

	def StratOsGetLightStatus(self, num = 0):
		if len(self.DoorList) != 0:
			HAgetLightStatus(self.LightsList[num]['MAC'], self.LightsList[num]['HAEndpt'])
			
			time.sleep(1)
		
		
			
	
	
	############### XBee Low-Level Functions ################
	
	def ZDOgetMYAddr(self, MAC):
		# MAC should have this form: '\x01\x23\x45\x67\x89\xAB\xCD\xEF'
		temp = ZDO_Payload["0000_MYAddr_Req"].copy()
		temp['MACAddr'] = ''.join(list(reversed(MAC)))
		temp = ''.join(temp.values())
		
		self.XBeeObj.send('tx_explicit',
			dest_addr_long = self.BROADCAST_EQUIV_MAC,
			dest_addr = self.UNKNOWN_EQUIV_MY,
			src_endpoint = '\x00',
			dest_endpoint = '\x00',
			cluster = '\x00\x00', # 0000_MYAddr_Req
			profile = '\x00\x00', # ZDO profile
			data = temp
		)
	
	def ZDOgetMACAddr(self, MY):
		# MY should have this form: '\x12\x34'
		temp = ZDO_Payload["0001_MACAddr_Req"].copy()
		temp['MYAddr'] = ''.join(list(reversed(MY)))
		temp = ''.join(temp.values())
	
		self.XBeeObj.send('tx_explicit',
			dest_addr_long = self.BROADCAST_EQUIV_MAC,
			dest_addr = self.UNKNOWN_EQUIV_MY,
			src_endpoint = '\x00',
			dest_endpoint = '\x00',
			cluster = '\x00\x01', # 0001_MACAddr_Req
			profile = '\x00\x00', # ZDO profile
			data = temp
		)
		
	def ZDOgetSimpleDesc(self, MY, endpt):
		# MY should have this form: '\x12\x34'
		# endpt has form: '\x12'
		temp = ZDO_Payload["0004_SimpleDesc_Req"].copy()
		temp['MYAddr'] = ''.join(list(reversed(MY)))
		temp['Endpoint'] = endpt
		temp = ''.join(temp.values())
		
	
		self.XBeeObj.send('tx_explicit',
			dest_addr_long = self.UNKNOWN_EQUIV_MAC,
			dest_addr = MY,
			src_endpoint = '\x00',
			dest_endpoint = '\x00',
			cluster = '\x00\x04', # 0004_SimpleDesc_Req
			profile = '\x00\x00', # ZDO profile
			data = temp
		)
		
	def ZDOgetActiveEndpts(self, MY):
		# MY should have this form: '\x12\x34'
		temp = ZDO_Payload["0005_ActiveEndpts_Req"].copy()
		temp['MYAddr'] = ''.join(list(reversed(MY)))
		temp = ''.join(temp.values())
		
		self.XBeeObj.send('tx_explicit',
			dest_addr_long = self.UNKNOWN_EQUIV_MAC,
			dest_addr = MY,
			src_endpoint = '\x00',
			dest_endpoint = '\x00',
			cluster = '\x00\x05', # 0005_ActiveEndpts_Req
			profile = '\x00\x00', # ZDO profile
			data = temp
		)
	
	def ZDOgetMatchDesc(self, Trans, MY, Profile, Clustinfo):
		# Trans form : '\x01' 		x02 = HA	x03 = Digi
		# MY should have this form: '\x12\x34'
		# Profile should have this form: '\x12\x34'
		# Clustinfo should be list: ['\x03', ['\x00\x00','\x00\x06','\x00\x08'] ]
		temp = ZDO_Payload["0006_MatchDesc_Req"].copy()
		temp['Trans'] = Trans
		temp['MYAddr'] = ''.join(list(reversed(MY)))
		temp['Profile'] = ''.join(list(reversed(Profile)))
		temp['InCount'] = Clustinfo[0]
		tempin = ''
		for x in Clustinfo[1]:
			tempin = tempin + ''.join(list(reversed(x)))
		temp['InList'] = tempin
		temp['OutCount'] = '\x00' # Output clusters not supported yet
		temp = ''.join(temp.values())
				
		self.XBeeObj.send('tx_explicit',
			dest_addr_long = self.UNKNOWN_EQUIV_MAC,
			dest_addr = MY,
			src_endpoint = '\x00',
			dest_endpoint = '\x00',
			cluster = '\x00\x06', # 0006_MatchDesc_Req
			profile = '\x00\x00', # ZDO profile
			data = temp
		)
	
	def ZDOgetLQINeighbor(self, MAC):
		# MAC should have this form: '\x01\x23\x45\x67\x89\xAB\xCD\xEF'
		self.XBeeObj.send('tx_explicit',
			dest_addr_long = MAC,
			dest_addr = self.UNKNOWN_EQUIV_MY,
			src_endpoint = '\x00',
			dest_endpoint = '\x00',
			cluster = '\x00\x31', # 0031_MgmtLQI_Req
			profile = '\x00\x00', # ZDO profile
			data = ''.join(ZDO_Payload["0031_MgmtLQI_Req"].values())
		)
	
	
	def HAgetManufacturer(self, MAC, destendpt):
		# MAC should have this form: '\x01\x23\x45\x67\x89\xAB\xCD\xEF'
		# destendpt form: '\x12'
		temp = HA_Payload.copy()
		temp["FrameCtl"] = '\x00'	# x00 = Attr cmd; x01 = Cluster cmd
		temp["Cmd"] = '\x00'		# Read attr
		temp["Payload"] = '\x04\x00'	# Manufacturer
		temp = ''.join(temp.values())
		
		self.XBeeObj.send('tx_explicit',
			dest_addr_long = MAC,
			dest_addr = self.UNKNOWN_EQUIV_MY,
			src_endpoint = '\x00',
			dest_endpoint = destendpt,
			cluster = '\x00\x00', # HA General
			profile = '\x01\x04', # HA Profile
			data = temp
		)

	def HAgetModelID(self, MAC, destendpt):
		# MAC should have this form: '\x01\x23\x45\x67\x89\xAB\xCD\xEF'
		# destendpt form: '\x12'
		temp = HA_Payload.copy()
		temp["FrameCtl"] = '\x00'	# x00 = Attr cmd; x01 = Cluster cmd
		temp["Cmd"] = '\x00'		# Read attr
		temp["Payload"] = '\x05\x00'	# Model ID
		temp = ''.join(temp.values())
		
		self.XBeeObj.send('tx_explicit',
			dest_addr_long = MAC,
			dest_addr = self.UNKNOWN_EQUIV_MY,
			src_endpoint = '\x00',
			dest_endpoint = destendpt,
			cluster = '\x00\x00', # HA General
			profile = '\x01\x04', # HA Profile
			data = temp
		)
	
	def HAgetLightStatus(self, MAC, destendpt):
		# MAC should have this form: '\x01\x23\x45\x67\x89\xAB\xCD\xEF'
		# destendpt form: '\x12'
		temp = HA_Payload.copy()
		temp["FrameCtl"] = '\x00'	# x00 = Attr cmd; x01 = Cluster cmd
		temp["Cmd"] = '\x00'	# Read attr
		temp["Payload"] = '\x00\x00'	# OnOff status
		temp = ''.join(temp.values())
		
		self.XBeeObj.send('tx_explicit',
			dest_addr_long = MAC,
			dest_addr = self.UNKNOWN_EQUIV_MY,
			src_endpoint = '\x00',
			dest_endpoint = destendpt,
			cluster = '\x00\x06', # HA On/Off Light
			profile = '\x01\x04', # HA Profile
			data = temp
		)
		
		
	def HAturnLightOFF(self, MAC, destendpt):
		# MAC should have this form: '\x01\x23\x45\x67\x89\xAB\xCD\xEF'
		# destendpt form: '\x12'
		temp = HA_Payload.copy()
		temp["FrameCtl"] = '\x01'	# x00 = Attr cmd; x01 = Cluster cmd
		temp["Cmd"] = '\x00'	# turn off
		temp = ''.join(temp.values())
		
		self.XBeeObj.send('tx_explicit',
			dest_addr_long = MAC,
			dest_addr = self.UNKNOWN_EQUIV_MY,
			src_endpoint = '\x00',
			dest_endpoint = destendpt,
			cluster = '\x00\x06', # HA On/Off Light
			profile = '\x01\x04', # HA Profile
			data = temp
		)
		
	def HAturnLightON(self, MAC, destendpt):
		# MAC should have this form: '\x01\x23\x45\x67\x89\xAB\xCD\xEF'
		# destendpt form: '\x12'
		temp = HA_Payload.copy()
		temp["FrameCtl"] = '\x01'	# x00 = Attr cmd; x01 = Cluster cmd
		temp["Cmd"] = '\x01'	# turn on
		temp = ''.join(temp.values())
		
		self.XBeeObj.send('tx_explicit',
			dest_addr_long = MAC,
			dest_addr = self.UNKNOWN_EQUIV_MY,
			src_endpoint = '\x00',
			dest_endpoint = destendpt,
			cluster = '\x00\x06', # HA On/Off Light
			profile = '\x01\x04', # HA Profile
			data = temp
		)

	def HAturnLightTOGGLE(self, MAC, destendpt):
		# MAC should have this form: '\x01\x23\x45\x67\x89\xAB\xCD\xEF'
		# destendpt form: '\x12'
		temp = HA_Payload.copy()
		temp["FrameCtl"] = '\x01'	# x00 = Attr cmd; x01 = Cluster cmd
		temp["Cmd"] = '\x02'	# toggle
		temp = ''.join(temp.values())
		
		self.XBeeObj.send('tx_explicit',
			dest_addr_long = MAC,
			dest_addr = self.UNKNOWN_EQUIV_MY,
			src_endpoint = '\x00',
			dest_endpoint = destendpt,
			cluster = '\x00\x06', # HA On/Off Light
			profile = '\x01\x04', # HA Profile
			data = temp
		)
	
	# def HAturnLightDIM(self, MAC, destendpt): # Can implement in the future
	
	
	def terminate(self):
		# halt() must be called before closing the serial
		# port in order to ensure proper thread shutdown
		self.XBeeObj.halt()
		self.XBeeSer.close()

			
			
			
			
			
			