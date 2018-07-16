#!/usr/bin/python3 -u

import fileinput, os, shutil

'''repair_torrc() function will be called when we want to gurantee the existence of:
1. /etc/torrc.d/95_whonix.conf
2. /etc/tor/torrc
3. "%include /etc/torrc.d/95_whonix.conf" line in /etc/tor/torrc file

In addition, we create 40_tor_control_panel.conf
and 50_user.conf here if they do not exist.
'''

whonix = os.path.exists('/usr/share/anon-gw-base-files/gateway')
#qubes = os.path.exists('/var/lib/qubes')

def repair_torrc():
    repair_torrc_d()

    if not os.path.exists('/etc/tor/torrc'):
        with open('/etc/tor/torrc', "w+") as f:
            if whonix:
                f.write("%include /etc/torrc.d/95_whonix.conf\n")
            else:
                f.write('%include /etc/torrc.d/40_tor_control_panel.conf\n')
                f.write('%include /etc/torrc.d/50_user.conf\n')
    else:
        with open('/etc/tor/torrc', "r") as f:
            lines = f.readlines()

        torrcd_line_exists = False
        for line in lines:
            line = line.strip()
            if (line.startswith('%include /etc/torrc.d')):
                torrcd_line_exists = True

        if not torrcd_line_exists:
            with open('/etc/tor/torrc', "a") as f:
                if whonix:
                    f.write("%include /etc/torrc.d/95_whonix.conf\n")
                else:
                    f.write('%include /etc/torrc.d/40_tor_control_panel.conf\n')
                    f.write('%include /etc/torrc.d/50_user.conf\n')

    if whonix and not os.path.exists('/etc/torrc.d/95_whonix.conf'):
        with open('/etc/torrc.d/95_whonix.conf', "w+") as f:
            f.write("%include /usr/local/etc/torrc.d/40_tor_control_panel.conf\n")
            f.write("%include /usr/local/etc/torrc.d/50_user.conf\n")

    torrc_text = '# This file is generated by and should ONLY be used by anon-connection-wizard.\n\
# User configuration should go to " + Common.torrc_user_file_path + ", not here. Because:\n\
#    1. This file can be easily overwritten by anon-connection-wizard.\n\
#    2. Even a single character change in this file may cause error.\n\
# However, deleting this file will be fine since a new plain file will be generated \
the next time you run anon-connection-wizard.\nDisableNetwork 0\n'

    user_text = '# Use this file for your own Tor configuration.\n'

    if whonix:
        if not os.path.exists('/usr/local/etc/torrc.d/40_tor_control_panel.conf'):
            with open('/usr/local/etc/torrc.d/40_tor_control_panel.conf', "w+") as f:
                f.write(toorc_text)
        if not os.path.exists('/usr/local/etc/torrc.d/50_user.conf'):
            with open('/usr/local/etc/torrc.d/50_user.conf', "w+") as f:
                f.write(user_text)
    else:
        if not os.path.exists('/etc/torrc.d/40_tor_control_panel.conf'):
            with open('/etc/torrc.d/40_tor_control_panel.conf', "w+") as f:
                f.write()
        if not os.path.exists('/etc/torrc.d/50_user.conf'):
            with open('/etc/torrc.d/50_user.conf', "w+") as f:
                f.write(text2)

'''repair_torrc_d() will gurantee the existence of /etc/torrc.d/
and if anon-connection-wizard is in Whonix,
then also gurantee the existence of /usr/local/etc/torrc.d/
'''
def repair_torrc_d():
    if not os.path.exists('/etc/torrc.d/'):
        os.makedirs('/etc/torrc.d/')
    if whonix and not os.path.exists('/usr/local/etc/torrc.d/'):
        os.makedirs('/usr/local/etc/torrc.d/')
