#!/usr/bin/env python
#
# send_ip_address.py:   Send the ip address(es) of a Raspberry Pi
#
# 2015-05-09, Heimir Sverrisson (heimir.sverrisson@gmail.com)
#               Based on work by Todd Lawall
#
# Python27

import sys
import re
import os
import time
import socket
import smtplib
import json
from email.MIMEText import MIMEText

with open("creds.json", "r") as read_file:
    data = json.load(read_file)

# Gmail overrides this anyway
fromMe = data['fromMe']
toWhom = data['toWhom']             # Recipient of the message
username = data['username']          # To authenticate to the mail server
# For gmail, you can use app specific password
password = data['password']
# For gmail use 'smpt.gmail.com:587'
mail_server = data['mail_server']
# Must be True for gmail
use_tls = data['use_tls']
# Text file that stores previous ip addressed
ip_file_path = data['ip_file_path']
debug = data['debug']                              # Set to True while testing

# Return the ip address from a the file
# If file does not exist or does not contain
# a well formed ip address on its first line
# then return an empty array
#
def get_prev_ip(file_path):
    ips= []
    try:
        f= open(file_path, 'r')
    except IOError:     # No such file
        return ips
    # File exists, now read it one line at a time
    for line in f:
        aa = line.strip() if os.name == 'nt' else re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",line.strip())
        # aa=re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$",line.strip())
        if aa is not None:
            if os.name == 'nt':
                ips.append(aa)
            else:
                ips.append(aa.group())
    f.close()
    return ips


# Run the ifconfig command to read the ip address(es)
# assigned to all interfaces (but localhost).
# Return the address list and an email message
#
def get_my_ips():
    ipCmd = 'ipconfig' if os.name == 'nt' else 'ifconfig'
    stdin, stdout= os.popen2(ipCmd)
    output = stdout.read()
    pi_hostname = socket.gethostname()
    if os.name == 'nt':
        ipaddrs = output
    else:
        snagAddrRegex = re.compile( r'inet addr:(?P<addr>\S+?) ' )
        ipaddrs = snagAddrRegex.findall( output )
    if ( '127.0.0.1' in ipaddrs ):
        ipaddrs.remove( '127.0.0.1' )  # get rid of the interface we know is always there, it's just noise
    if os.name == 'nt':
        msg= MIMEText("%s has ip(s):\n    %s\n\nOutput of command:\n%s" % (pi_hostname, ''.join(ipaddrs), output))
    else:
        msg = MIMEText("%s has ip(s):\n    %s\n\nOutput of command:\n%s" % (pi_hostname, '\n    '.join( ipaddrs ), output))
    msg["subject"]= "%s: %s has ip(s): %s" % (fromMe ,pi_hostname, ' '.join(ipaddrs))
    msg["to"] = toWhom
    msg["from"] = fromMe
    if debug:
        print msg.as_string()
    return ipaddrs, msg


# Send the msg as email
#
def send_mail(msg):
    s = smtplib.SMTP(mail_server)
    if use_tls:
        s.starttls()
    s.login(username,password)
    s.sendmail( fromMe, toWhom, msg.as_string())
    s.quit()
    if debug:
        print 'Mail was sent!'

# Write an ip address to a file
#
def write_ips(file_path, ips):
    try:
        f = open(file_path, 'w')
        if os.name == 'nt':
            f.write('\n'.join(ips) + '\n')
        else:
            f.write(''.join(ips) + '\n')
        f.close()
    except IOError:
        return          # Igonore any error writing to the file

def main(argv):
    # First command line argument is the file_path
    # use default if nothing is passed
    if len(argv) > 1:
        file_path = argv[1]
    else:
        file_path = ip_file_path
    ips = get_prev_ip(file_path)
    ipaddrs, msg = get_my_ips()
    if len(ips) == 0 or ips != ipaddrs:
        send_mail(msg)
    write_ips(file_path, ipaddrs)     # Save the ips we found
    if debug:
        print 'Prev ips:', ' '.join(ips), ', Current ip(s):', ' '.join(ipaddrs)


if __name__ == "__main__":
    main(sys.argv)
    