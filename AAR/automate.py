#!/usr/bin/python
import nanostation as ns
import time
import datetime
import RPi.GPIO as GPIO
import piggyback as pb
import logging
logging.basicConfig(filename='/home/pi/log/arr.log',level=logging.DEBUG)


date=datetime.date.today().strftime("%d_%b_%y")

from time import mktime
t =datetime.datetime.now()
unix_secs = mktime(t.timetuple())

ip,log,piggyback=ns.getConfig()
boat,cpe_ip=ns.getBoatData()
ssid=ns.extssid()

data=dict()
diri=""
#cpe_ip="192.168.179.123"
if log=='on':
	logging.info("Connection Successful\n Boat Name: " + str (boat)+ "\n" + "IP Address: "+str(cpe_ip) + ". Controller Connnected to "+str(ssid))
	
cj,opener=ns.login(cpe_ip)
print("Logged in to " + boat + " " +cpe_ip)
if log=='on':
	logging.info("login success")

ns.statusled(1)
pos=ns.fromdb()
#pos=0
hide=0
while 1:
	ns.stop()
	ns.statusled(0)
	signal,rssi,noise,ccq,distance,txrate,rxrate,freq,channel = ns.fetchstatus(cj,opener,cpe_ip)
	try:
		bs_ip,ping_ms=ns.fetchip(cj,opener,cpe_ip)
	except:
		bs_ip="0.0.0.0"
		ping_ms=0
	th,hide=ns.thmap(distance)
	signalinv=signal*-1
	ns.rssiled(rssi)
	data={'ping_ms':ping_ms,'TIME':unix_secs,'dir':diri,'boat':1,'ss':signal,'nf':noise,'rssi':rssi,'pos':pos,'ccq':ccq,'d':distance,'txrate':txrate,'rxrate':rxrate,'freq':freq,'channel':channel,'bs_ip':bs_ip}
# 	if log==1:
# 		print data
	#automation:
	if signalinv > th:
		hide=0
		if pos>36:
			pos=0
			diri='Calibration'
		elif pos >18 and pos <36:
			ns.rev()
			pos=pos+1
			diri='Reverse'
		else:
			ns.fwd()
			diri='Forward'
			pos=pos+1
	elif signalinv ==0:
		if pos >36:
			pos=0
			diri='Calibration'
		elif pos >18 and pos<36:
			ns.rev()
			pos=pos+1
			diri='Rescan & Reverse'
		else:
			ns.fwd()
			diri='Rescan & Forward'
			pos=pos+1
	else:
		hide=10
		ns.stop()
		diri='Stop'
		
	#Data storage
	data={'ping_ms':ping_ms,'TIME':unix_secs,'dir':diri,'boat':1,'ss':signal,'nf':noise,'rssi':rssi,'pos':pos,'ccq':ccq,'d':distance,'txrate':txrate,'rxrate':rxrate,'freq':freq,'channel':channel,'bs_ip':bs_ip}
	if log=='on':
		logging.info(data)
	if piggyback ==1:
		pb.helper(data)
	ns.todb(data)
	ns.breathe(5,hide)
GPIO.cleanup()



