#!/usr/bin/python3 -u

import sys
import os
import json
import shutil
import tempfile
#from anon_connection_wizard import repair_torrc

whonix = os.path.exists('/usr/share/anon-gw-base-files/gateway')
if whonix:
    torrc_file_path = '/usr/local/etc/torrc.d/40_anon_connection_wizard.conf'
    torrc_user_file_path =  '/usr/local/etc/torrc.d/50_user.conf'
else:
    torrc_file_path = '/etc/torrc.d/40_anon_connection_wizard.conf'
    torrc_user_file_path = '/etc/torrc.d/50_user.conf'
torrc_tmp_file_path = ''

bridges_default_path = '/usr/share/anon-connection-wizard/bridges_default'

command_useBridges = 'UseBridges 1'
command_use_custom_bridge = '# Custom Bridge is used:'
command_obfs3 = 'ClientTransportPlugin obfs2,obfs3 exec /usr/bin/obfs4proxy\n'
command_obfs4 = 'ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy\n'
command_fte = 'ClientTransportPlugin fte exec /usr/bin/fteproxy --managed\n'
command_scramblesuit = 'ClientTransportPlugin scramblesuit exec /usr/bin/obfs4proxy\n'
command_meek_lite = 'ClientTransportPlugin meek_lite exec /usr/bin/obfs4proxy\n'
command_meek_amazon_address = 'a0.awsstatic.com\n'
command_meek_azure_address = 'ajax.aspnetcdn.com\n'

bridges_command = ['ClientTransportPlugin obfs2,obfs3 exec /usr/bin/obfs4proxy\n',
                   'ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy\n',
                   'ClientTransportPlugin meek_lite exec /usr/bin/obfs4proxy\n',
                   'ClientTransportPlugin meek_lite exec /usr/bin/obfs4proxy\n']

bridges_type = ['obfs3', 'obfs4', 'meek-amazon', 'meek-azure']

command_http = 'HTTPSProxy '
command_httpAuth = 'HTTPSProxyAuthenticator'
command_sock4 = 'Socks4Proxy '
command_sock5 = 'Socks5Proxy '
command_sock5Username = 'Socks5ProxyUsername'
command_sock5Password = 'Socks5ProxyPassword'

def gen_torrc(args):
    bridge_type =       str(args[0])
    custom_bridges =    str(args[1])
    proxy_type =        str(args[2])
    if not proxy_type == 'None':
        proxy_ip =          str(args[3])
        proxy_port =        str(args[4])
        proxy_username =    str(args[5])
        proxy_password  =   str(args[6])
    print(bridge_type)
    #return()
    #repair_torrc.repair_torrc()  # This guarantees a good set of torrc files

    # Creates a file and returns a tuple containing both the handle and the path.
    # we are responsible for removing tmp file when finished which is the reason we
    # use shutil.move(), not shutil.copy(), below
    handle, torrc_tmp_file_path = tempfile.mkstemp()

    # Temporary. Write directly to torrc. If we create a tempfile and move it to torrc.d,
    # tor daemon cannot open it: 'permission denied'.
    with open(torrc_file_path, "w") as f:
        f.write("\
# This file is generated by and should ONLY be used by anon-connection-wizard.\n\
# User configuration should go to " + torrc_user_file_path + ", not here. Because:\n\
#    1. This file can be easily overwritten by anon-connection-wizard.\n\
#    2. Even a single character change in this file may cause error.\n\
# However, deleting this file will be fine since a new plain file will be generated \
the next time you run anon-connection-wizard.\n\
")
        if bridge_type == 'None':
            f.write('DisableNetwork 0\n')

        elif bridge_type == 'Custom bridges':
            f.write(command_use_custom_bridge + '\n')
            f.write(command_useBridges + '\n')
            f.write('DisableNetwork 0\n')
            if custom_bridges.lower().startswith('obfs4'):
                f.write(command_obfs4 + '\n')
            elif bridge_custom.lower().startswith('obfs3'):
                f.write(command_obfs3 + '\n')
            elif bridge_custom.lower().startswith('fte'):
                f.write(command_fte + '\n')
            elif bridge_custom.lower().startswith('meek_lite'):
                f.write(command_meek_lite + '\n')
            bridge_custom_list = custom_bridges.split('\n')
            for bridge in bridge_custom_list:
                if bridge != '':
                    f.write('bridge {0}\n'.format(bridge))

        else:
            f.write(command_useBridges + '\n')
            if bridge_type in bridges_type:
                command = bridges_command[bridges_type.index(bridge_type)]
                f.write(command)
            bridges = json.loads(open(bridges_default_path).read())
            # The bridges variable are like a multilayer-dictionary
            for bridge in bridges['bridges'][bridge_type]:
                f.write('bridge {0}\n'.format(bridge))
            f.write('DisableNetwork 0\n')

    #''' The part is the IO to torrc for proxy settings.
    #Related official docs: https://www.torproject.org/docs/tor-manual.html.en
    #'''
        if proxy_type == 'HTTP/HTTPS':
            f.write('HTTPSProxy {0}:{1}\n'.format(proxy_ip, proxy_port))
            if (proxy_username != ''):
                f.write('HTTPSProxyAuthenticator {0}:{1}\n'.format(proxy_username,
                                                                   proxy_password))
        elif proxy_type == 'SOCKS4':
            # Notice that SOCKS4 does not support proxy username and password
            f.write('Socks4Proxy {0}:{1}\n'.format(proxy_ip, proxy_port))
        elif proxy_type == 'SOCKS5':
            f.write('Socks5Proxy {0}:{1}\n'.format(proxy_ip, proxy_port))
            if (proxy_username != ''):
                f.write('Socks5ProxyUsername {0}\n'.format(proxy_username))
                f.write('Socks5ProxyPassword {0}\n'.format(proxy_password))

    #shutil.move(torrc_tmp_file_path, torrc_file_path)

def parse_torrc():
    if os.path.exists(torrc_file_path):
        use_bridge = False
        use_proxy = False
        if 'Proxy' in open(torrc_file_path).read():
            use_proxy = True
        if 'UseBridges' in open(torrc_file_path).read():
            use_bridge = True

        if use_bridge:
            with open(torrc_file_path, 'r') as f:
                ## This flag is for parsing meek_lite
                use_meek_lite = False
                for line in f:
                    #if line.startswith(command_use_custom_bridge):  # this condition must be above '#' condition, because it also contains '#'
                        #use_default_bridge = False
                    #elif line.startswith('#'):
                        #pass  # add this line to improve efficiency
                    #elif line.startswith(command_useBridges):
                        #use_bridges = True
                    if line.startswith(command_obfs3):
                        bridge_type = 'obfs3'
                    elif line.startswith(command_obfs4):
                        bridge_type = 'obfs4'
                    elif line.startswith(command_meek_lite):
                        use_meek_lite = True
                    elif use_meek_lite and line.endswith(command_meek_amazon_address):
                        bridge_type = 'meek-amazon'
                        #bridge_custom += ' '.join(line.split(' ')[1:])  # eliminate the 'Bridge'
                    elif use_meek_lite and line.endswith(command_meek_azure_address):
                        bridge_type = 'meek-azure'
                        #bridge_custom += ' '.join(line.split(' ')[1:])  # eliminate the 'Bridge'
                    elif line.startswith(command_fte):
                        bridge_type = 'fte'
                    elif line.startswith(command_scramblesuit):
                        bridge_type = 'scramblesuit'
                    #elif line.startswith(command_use_custom_bridge):
                        #bridges_type = 'Custom bridges'
                    #elif line.startswith(command_bridgeInfo):
                        #bridge_custom += ' '.join(line.split(' ')[1:])  # eliminate the 'Bridge'
                if bridge_type == 'obfs4':
                    bridge_type = 'obfs4 (recommended)'
                elif bridge_type == 'meek-amazon':
                    bridge_type = 'meek-amazon (works in China)'
                elif bridge_type == 'meek-azure':
                    bridge_type = 'meek-azure (works in China)'
        else:
            bridge_type = 'None'

        if use_proxy:
            with open(torrc_file_path, 'r') as f:
                for line in f:
                    if line.startswith(command_http):
                        #use_proxy = True
                        proxy_type = 'HTTP/HTTPS'
                        ''' Using the following parsing fragments is too fixed,
                        which is not good implementation.
                        But as long as leave .conf untouched by user, it will be Okay.
                        We should also be careful when changing the command line format in this app
                        '''
                        proxy_ip = line.split(' ')[1].split(':')[0]
                        proxy_port = line.split(' ')[1].split(':')[1].split('\n')[0]

                    elif line.startswith(command_httpAuth):
                        proxy_username = line.split(' ')[1].split(':')[0]
                        proxy_password = line.split(' ')[1].split(':')[1]
                    elif line.startswith(command_sock4):
                        use_proxy = True
                        proxy_type = 'SOCKS4'
                        proxy_ip = line.split(' ')[1].split(':')[0]
                        proxy_port = line.split(' ')[1].split(':')[1].split('\n')[0]
                    elif line.startswith(command_sock5):
                        use_proxy = True
                        proxy_type = 'SOCKS5'
                        proxy_ip = line.split(' ')[1].split(':')[0]
                        proxy_port = line.split(' ')[1].split(':')[1].split('\n')[0]
                    elif line.startswith(command_sock5Username):
                        proxy_username = line.split(' ')[1]
                    elif line.startswith(command_sock5Password):
                        proxy_password = line.split(' ')[1]
                    #if 'Proxy' in line:
                        #proxy_type = line.split()[0]
                        #proxy_socket = line.split()[1]
        else:
            proxy_type = 'None'
            proxy_ip = 'None'
            proxy_port = ''
            proxy_username = ''
            proxy_password = ''

        return(bridge_type, proxy_type, proxy_ip, proxy_port, proxy_username, proxy_password)
