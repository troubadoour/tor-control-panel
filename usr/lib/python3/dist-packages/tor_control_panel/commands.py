#!/usr/bin/python3 -su

import os

whonix = os.path.exists('/usr/share/anon-gw-base-files/gateway')
debian = None

def command(command):

    whonix_commands = {'restart_tor': 'leaprun acw-tor-control-restart',
                                        'stop_tor': 'leaprun acw-tor-control-stop',
                                        'reload_tor': 'leaprun acw-tor-control-reload',
                                        'tor_log': ['leaprun', 'tor-control-panel-read-tor-default-log'],
                                        'tor_status': 'leaprun acw-tor-control-status',
                                        'write_torrc': ['leaprun', 'acw-write-torrc'],
                                        'tor_config_sane': ['leaprun', 'tor-config-sane'],
                                        }

    debian_commands = {'restart_tor': '',
                                        'stop_tor': '',
                                        'reload_tor': '',
                                        'tor_log': '',
                                        'tor_status': '',
                                        'write_torrc': '',
                                        'tor_config_sane': '',
                                        }

    if whonix:
        return whonix_commands[command]

    if debian:
        # return debian_commands[command]
        pass
