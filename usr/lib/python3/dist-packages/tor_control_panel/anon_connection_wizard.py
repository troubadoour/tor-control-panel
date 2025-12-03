#!/usr/bin/python3 -su

## Copyright (C) 2018 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
## See the file COPYING for copying conditions.

import json
import os
import signal
import sys
from cProfile import label

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from guimessages.translations import _translations

from . import tor_status, repair_torrc, tor_bootstrap, torrc_gen, info
from .edit_etc_resolv_conf import edit_etc_resolv_conf_add, edit_etc_resolv_conf_remove
from .tor_status import cat, write_to_temp_then_move


def signal_handler(sig, frame):
   sys.exit(128 + sig)


class Common:
    translations_path = '/usr/share/anon-connection-wizard/translations.yaml'

    torrc_file_path = torrc_gen.torrc_path()
    torrc_user_file_path = torrc_gen.user_path()
    acw_comm_file_path = '/run/anon-connection-wizard/tor.conf'
    # torrc_file_path = ''

    bridges_default_path = '/usr/share/anon-connection-wizard/bridges_default'
    control_cookie_path = '/run/tor/control.authcookie'
    control_socket_path = '/run/tor/control'

    use_default_bridges = False
    bridge_type = ''
    use_custom_bridges = False
    bridge_custom = ''

    use_proxy = False
    proxy_type = 'HTTP / HTTPS'
    proxy_ip = ''
    proxy_port = ''
    proxy_username = ''
    proxy_password = ''

    init_tor_status = ''  # it records the initial status of Tor, serving as a backup
    disable_tor = False

    command_useBridges = 'UseBridges 1'
    command_use_custom_bridge = '# Custom Bridge is used:'
    command_obfs4 = 'ClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy'
    command_snowflake = 'ClientTransportPlugin snowflake exec /usr/bin/snowflake-client'
    command_meek_lite = 'ClientTransportPlugin meek_lite exec /usr/bin/obfs4proxy'
    command_meek_azure_address = 'ajax.aspnetcdn.com\n'

    command_http = 'HTTPSProxy '
    command_httpAuth = 'HTTPSProxyAuthenticator'
    command_sock4 = 'Socks4Proxy '
    command_sock5 = 'Socks5Proxy '
    command_sock5Username = 'Socks5ProxyUsername'
    command_sock5Password = 'Socks5ProxyPassword'

    ''' The following is a variable serves as a flag to work around the bug
    that a "blank IP/Port" message show up even when switching from proxy_wizard_page_1
    to proxy_wizard_page_2.
    '''
    # from_proxy_page_1 = True
    # from_bridge_page_1 = True

    font_title = QtGui.QFont()
    font_title.setPointSize(13)
    font_title.setBold(True)
    font_title.setWeight(95)

    font_description_main = QtGui.QFont()
    font_description_main.setPointSize(11)
    font_description_main.setBold(True)
    font_description_main.setWeight(85)

    font_description_minor = QtGui.QFont()
    font_description_minor.setPointSize(10)
    font_description_minor.setBold(False)
    font_description_minor.setWeight(30)

    font_option = QtGui.QFont()
    font_option.setPointSize(11)
    font_option.setBold(True)
    font_option.setWeight(65)

    groupBox_width = 350
    groupBox_height = 345

    wizard_steps = ['connection_main_page',
                    'bridge_wizard_page',
                    'proxy_wizard_page',
                    'torrc_page',
                    'tor_status_page']

    # TODO: may replace the URL with a better one for usability and accessibility
    assistance = 'For assistance, visit torproject.org/about/contact.html#support'



class ConnectionMainPage(QWizardPage):
    def __init__(self):
        super(ConnectionMainPage, self).__init__(None)

        self.steps = Common.wizard_steps

        self.page_layout = QVBoxLayout(self)

        self.label_1 = QLabel()
        self.page_layout.addWidget(self.label_1)
        self.label_2 = QLabel()
        self.page_layout.addWidget(self.label_2)
        self.label_3 = QLabel()
        self.page_layout.addWidget(self.label_3)
        self.connect_option = QRadioButton()
        self.page_layout.addWidget(self.connect_option)
        self.label_4 = QLabel()
        self.page_layout.addWidget(self.label_4)
        self.configure_option = QRadioButton()
        self.page_layout.addWidget(self.configure_option)
        self.label_5 = QLabel()
        self.page_layout.addWidget(self.label_5)
        self.disable_option = QRadioButton()
        self.page_layout.addWidget(self.disable_option)

        self.setLayout(self.page_layout)

        self.setup_ui()

    def setup_ui(self):
        font_description_minor = Common.font_description_minor
        font_description_main = Common.font_description_main
        font_option = Common.font_option

        self.label_1.setWordWrap(True)
        self.label_1.setText('''
<br>Before you connect to the Tor network, you need to provide information about this computer
Internet connection.''')
        self.label_1.setFont(font_description_minor)

        self.label_2.setFont(font_description_main)
        self.label_2.setText('Which of the following best describes your situation?<br>')

        self.label_3.setWordWrap(True)
        self.label_3.setText(
'I would like to connect directly to the Tor network. This will work in most situations.')
        self.label_3.setFont(font_description_minor)

        self.connect_option.setFont(font_option)
        self.connect_option.setText('Connect')
        self.connect_option.setChecked(True)
        self.configure_option.setFont(font_option)
        self.configure_option.setText('Configure')
        self.disable_option.setFont(font_option)
        self.disable_option.setText('Disable Tor')
        self.disable_option.show()

        self.label_4.setWordWrap(True)
        self.label_4.setText(
'''<br>This computer Internet connection is censored or proxied.<br>
I need to configure bridges or local proxy settings.''')
        self.label_4.setFont(font_description_minor)

        self.label_5.setWordWrap(True)
        self.label_5.setText(
'''<br>I do not want to connect automatically to the Tor network.<br>
Choosing this option will prevent browsing or any internet related activity.<br>
See next page for more details.''')
        self.label_5.setFont(font_description_minor)
        self.label_5.show()

        if Common.use_default_bridges or Common.use_proxy:
            self.configure_option.setChecked(True)
        else:
            self.connect_option.setChecked(True)

    def nextId(self):
        if self.connect_option.isChecked():
            # clear all setting
            Common.disable_tor = False
            Common.use_default_bridges = False
            Common.use_proxy = False
            return self.steps.index('torrc_page')
        elif self.configure_option.isChecked():
            Common.disable_tor = False
            return self.steps.index('bridge_wizard_page')
        elif self.disable_option.isChecked():
            Common.disable_tor = True
            return self.steps.index('tor_status_page')
        return None


class BridgesWizardPage(QWizardPage):
    def __init__(self):
        super(BridgesWizardPage, self).__init__(None)

        self.steps = Common.wizard_steps

        self.bridges = ['obfs4',
                        'snowflake',
                        'meek-azure',
                       ]

        self.header_frame = QFrame()

        self.header_layout = QGridLayout(self.header_frame)
        self.header_label = QLabel()
        self.bridges_checkbox = QCheckBox()
        self.show_help_censorship = QPushButton()

        self.header_layout.addWidget(self.header_label, 1, 0)
        self.header_layout.addWidget(self.bridges_checkbox, 2, 0)
        self.header_layout.addWidget(self.show_help_censorship, 2, 1)

        self.bridges_frame = QFrame()

        self.bridges_layout = QGridLayout(self.bridges_frame)
        self.hline_1 = QFrame()
        self.default_option = QRadioButton()
        self.bridges_label = QLabel()
        self.bridges_combo = QComboBox()
        self.hline_2 = QFrame()
        self.custom_option = QRadioButton()
        self.custom_bridges_help = QPushButton()
        self.custom_label = QLabel()
        self.custom_bridges = QTextEdit()

        self.bridges_layout.addWidget(self.default_option, 1, 0)
        self.bridges_layout.addWidget(self.bridges_label, 2, 0)
        self.bridges_layout.addWidget(self.bridges_combo, 2, 1)
        self.bridges_layout.addWidget(self.hline_2, 3, 0)
        self.bridges_layout.addWidget(self.custom_option, 4, 0)
        self.bridges_layout.addWidget(self.custom_bridges_help, 4, 1)
        self.bridges_layout.addWidget(self.custom_label, 5, 0)
        self.bridges_layout.addWidget(self.custom_bridges, 6, 0, 1, 2)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.header_frame)
        self.layout.addWidget(self.bridges_frame)
        self.setLayout(self.layout)

        self.setup_ui()

    def setup_ui(self):
        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor

        self.bridges_frame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        self.bridges_frame.setVisible(self.bridges_checkbox.isChecked())

        self.header_label.setText('Tor Bridges Configuration<br>')
        self.header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.header_label.setFont(font_title)

        self.bridges_checkbox.setChecked(Common.use_default_bridges)
        self.bridges_checkbox.stateChanged.connect(self.enable_bridge)
        self.bridges_checkbox.setText("I need Tor bridges to bypass the Tor censorship.")
        self.bridges_checkbox.setFont(font_description_main)
        self.bridges_combo.setMinimumWidth(160)

        self.show_help_censorship.setEnabled(True)
        self.show_help_censorship.setText('&Help ?')
        self.show_help_censorship.clicked.connect(info.show_help_censorship)

        self.default_option.setChecked(True)
        self.default_option.setText('Select a built-in bridge')
        self.default_option.setFont(font_description_minor)

        self.hline_2.setFrameShape(QFrame.HLine)
        self.hline_2.setFrameShadow(QFrame.Sunken)
        self.hline_2.setMinimumWidth(520)

        self.custom_option.setText('Provide bridges I know')
        self.custom_option.setFont(font_description_minor)

        self.default_option.toggled.connect(self.show_default_bridge, True)

        self.bridges_label.setText('     Select a bridge type:')
        self.bridges_label.setFont(font_description_minor)

        for bridge in self.bridges:
            self.bridges_combo.addItem(bridge)

        ''' Remember previous state '''
        index = self.bridges_combo.findText(Common.bridge_type)
        self.bridges_combo.setCurrentIndex(index)

        self.custom_label.setEnabled(False)
        self.custom_label.setText('Enter at least 2 bridge relays (one per line).')

        self.custom_bridges.setEnabled(True)
        self.custom_bridges.setStyleSheet("background-color:white;")

        if not Common.use_default_bridges:
            self.custom_bridges.setText(Common.bridge_custom)  # adjust the line according to value in Common

        self.custom_bridges_help.setEnabled(True)
        self.custom_bridges_help.setText('&How to get Bridges?')
        self.custom_bridges_help.clicked.connect(info.custom_bridges_help)

        self.default_option.setVisible(Common.use_default_bridges)
        self.hline_2.setVisible(Common.use_default_bridges)
        self.custom_option.setVisible(Common.use_default_bridges)

        self.bridges_label.setVisible(Common.use_default_bridges)
        self.bridges_combo.setVisible(Common.use_default_bridges)

        self.custom_label.setVisible(Common.use_custom_bridges)
        self.custom_bridges.setVisible(Common.use_custom_bridges)
        self.custom_bridges_help.setVisible(Common.use_custom_bridges)

    def enable_bridge(self, state):
        Common.use_default_bridges = state
        self.bridges_frame.setVisible(state)
        self.default_option.setVisible(state)
        self.hline_2.setVisible(state)
        self.custom_option.setVisible(state)

        self.bridges_label.setVisible(state and self.default_option.isChecked())
        self.bridges_combo.setVisible(state and self.default_option.isChecked())

        self.custom_label.setVisible(state and (self.custom_option.isChecked()))
        self.custom_bridges.setVisible(state and (self.custom_option.isChecked()))
        self.custom_bridges_help.setVisible(state and (self.custom_option.isChecked()))

    def show_default_bridge(self, default_option_checked):
        if default_option_checked:
            # self.bridges_frame.show()
            self.bridges_label.show()
            self.bridges_combo.show()
            self.bridges_label.setEnabled(True)
            self.bridges_combo.setEnabled(True)

            self.custom_label.hide()
            self.custom_bridges.hide()
            self.custom_bridges_help.hide()
        else:
            self.bridges_label.setEnabled(False)
            self.bridges_combo.setEnabled(False)

            self.custom_label.show()
            self.custom_bridges.show()
            self.custom_bridges_help.show()

    def nextId(self):
        if not self.bridges_checkbox.isChecked():
            Common.use_default_bridges = False
            return self.steps.index('proxy_wizard_page')
        else:
            Common.use_default_bridges = True

            if self.default_option.isChecked():
                bridge_type = str(self.bridges_combo.currentText())
                if bridge_type.startswith('obfs4'):
                    bridge_type = 'obfs4'
                elif bridge_type.startswith('meek-azure'):
                    bridge_type = 'meek-azure'
                    ## Required for meek and snowflake only.
                    ## https://forums.whonix.org/t/censorship-circumvention-tor-pluggable-transports/2601/9
                    edit_etc_resolv_conf_add()
                elif bridge_type.startswith('snowflake'):
                   bridge_type = 'snowflake'
                   edit_etc_resolv_conf_add()
                ''' TODO: Other options can be implemented once there are supported.
                elif bridge_type.startswith('fte'):
                bridge_type = 'fte'
                '''
                Common.bridge_type = bridge_type
                Common.use_default_bridges = True

                return self.steps.index('proxy_wizard_page')

            elif self.custom_option.isChecked():
                Common.use_custom_bridges = True
                Common.bridge_custom = str(self.custom_bridges.toPlainText())
                Common.use_default_bridges = False

                self.reformat_custom_bridge_input()
                # TODO: a more general RE will help filter the case where bridge_custom input is invalid
                if not self.valid_custom_bridges():
                    return self.steps.index('bridge_wizard_page')
                else:
                    return self.steps.index('proxy_wizard_page')
            return None

    def reformat_custom_bridge_input(self):
        reformat_lines = []
        for bridge in self.custom_bridges.toPlainText().split('\n'):
            elements = bridge.split()
            # auto-remove prepending commonly misuse 'bridge' string
            try:
                while elements[0].lower() == 'bridge':
                    elements.pop(0)
            except:
                continue
            reformat_lines.append(' '.join(elements))
        self.custom_bridges.setText('\n'.join(reformat_lines))

    def valid_custom_bridges(self):
        bridges = self.custom_bridges.toPlainText()
        bridge_defined_type = bridges.split(' ')[0]
        bridge_defined_type = bridge_defined_type.lower()

        return (bridge_defined_type.startswith('obfs4')
                or (('.' in bridge_defined_type) and (':' in bridge_defined_type)))


class ProxyWizardPage(QWizardPage):
    def __init__(self):
        super(ProxyWizardPage, self).__init__(None)

        translation = _translations(Common.translations_path, 'anon-connection-wizard')
        self._ = translation.gettext
        self.steps = Common.wizard_steps

        self.proxies = [#'-',
            'HTTP / HTTPS',
            'SOCKS4',
            'SOCKS5'
        ]

        self.layout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.layout.addWidget(self.label)

        self.groupBox = QGroupBox(self)
        self.layout.addWidget(self.groupBox)

        self.checkBox = QCheckBox(self.groupBox)  # proxy checkBox

        self.horizontal_line = QFrame(self.groupBox)

        self.label_2 = QLabel(self.groupBox)  # instructions
        self.label_3 = QLabel(self.groupBox)  # Proxy type label
        self.comboBox = QComboBox(self.groupBox) # Proxy type comboBox
        self.label_4 = QLabel(self.groupBox)  # assistance info
        self.label_5 = QLabel(self.groupBox)  # Address label
        self.label_6 = QLabel(self.groupBox)  # username label
        self.label_7 = QLabel(self.groupBox)  # Port label
        self.label_8 = QLabel(self.groupBox)  # password label

        self.lineEdit = QLineEdit(self.groupBox)  # IP
        self.lineEdit_2 = QLineEdit(self.groupBox)  # Port input
        self.lineEdit_3 = QLineEdit(self.groupBox)  # Username input
        self.lineEdit_4 = QLineEdit(self.groupBox)  # password input
        self.lineEdit_4.setEchoMode(QLineEdit.Password)  # password mask
        self.show_proxy_help = QPushButton(self.groupBox)

        self.setup_ui()

    def setup_ui(self):
        self.label.setMinimumSize(QtCore.QSize(16777215, 35))

        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor
        font_option = Common.font_option

        self.label.setText('Local Proxy Configuration')
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(font_title)

        self.groupBox.setMinimumSize(QtCore.QSize(Common.groupBox_width, Common.groupBox_height))
        self.groupBox.setGeometry(QtCore.QRect(0, 20, 0, 0))
        self.groupBox.setFlat(True)

        self.checkBox.setChecked(Common.use_proxy)
        self.checkBox.stateChanged.connect(self.enable_proxy)
        self.checkBox.setText("Use proxy before connecting to the Tor network")
        self.checkBox.setFont(font_description_main)
        self.checkBox.setToolTip('''<p>In some situations, you may want to transfer your traffic through a proxy server before connecting to the Tor network. </p><p>For example, if you are trying to use a third-party censorship circumvention tool to bypass the Tor censorship, you need to configure Tor to connect to the listening port of that circumvention tools. </p>''')
        self.checkBox.setGeometry(QtCore.QRect(20, 35, 500, 20))
        self.comboBox.currentIndexChanged[str].connect(self.option_changed)

        self.horizontal_line.setFrameShape(QFrame.HLine)
        self.horizontal_line.setFrameShadow(QFrame.Sunken)
        self.horizontal_line.setGeometry(15, 65, 510, 5)

        self.label_2.setGeometry(QtCore.QRect(20, 80, 201, 16))
        self.label_2.setText("Enter the proxy settings.")
        self.label_2.setFont(font_description_minor)

        self.label_3.setGeometry(QtCore.QRect(10, 110, 106, 20))
        self.label_3.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|
                                  QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_3.setText("Proxy type: ")
        self.label_3.setFont(font_description_minor)

        # Here we are going to implement the proxy type selection
        # Change it to larger so  that all options fit
        self.comboBox.setGeometry(QtCore.QRect(118, 110, 121, 27))
        for proxy in self.proxies:
            self.comboBox.addItem(proxy)

        # The default value is adjust according to Common.proxy_type
        if Common.use_proxy:
            self.comboBox.setCurrentIndex(self.proxies.index(Common.proxy_type))

        self.label_5.setGeometry(QtCore.QRect(10, 150, 106, 20))
        self.label_5.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|
                                  QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_5.setText("Address: ")
        self.label_5.setFont(font_description_minor)

        '''Username and Password options should be hide
        using "advance" button because it is not used rarely,
        according to recommendation from previous research.
        '''
        self.label_6.setGeometry(QtCore.QRect(10, 180, 106, 20))
        self.label_6.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|
                                  QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_6.setText("Username: ")
        self.label_6.setFont(font_description_minor)

        self.label_7.setGeometry(QtCore.QRect(394, 150, 41, 20))
        self.label_7.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|
                                  QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_7.setText("Port: ")
        self.label_7.setFont(font_description_minor)

        self.label_8.setGeometry(QtCore.QRect(280, 180, 70, 20))
        self.label_8.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|
                                  QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.label_8.setText("Password: ")
        self.label_8.setFont(font_description_minor)

        self.lineEdit.setGeometry(QtCore.QRect(118, 150, 260, 25))
        self.lineEdit.setStyleSheet("background-color:white;")
        self.lineEdit.setPlaceholderText('Example: 127.0.0.1')
        self.lineEdit.setText(Common.proxy_ip)

        self.lineEdit_2.setGeometry(QtCore.QRect(437, 150, 60, 25))
        self.lineEdit_2.setStyleSheet("background-color:white;")
        self.lineEdit_2.setPlaceholderText('1-65535')
        self.lineEdit_2.setText(Common.proxy_port)

        self.lineEdit_3.setGeometry(QtCore.QRect(118, 180, 150, 25))
        self.lineEdit_3.setStyleSheet("background-color:white;")
        self.lineEdit_3.setPlaceholderText('Optional')
        self.lineEdit_3.setText(Common.proxy_username)

        self.lineEdit_4.setGeometry(QtCore.QRect(352, 180, 145, 25))
        self.lineEdit_4.setStyleSheet("background-color:white;")
        self.lineEdit_4.setPlaceholderText('Optional')
        self.lineEdit_4.setText(Common.proxy_password)

        self.label_4.setGeometry(QtCore.QRect(10, 280, 500, 15))
        self.label_4.setText(Common.assistance)
        self.label_4.setFont(font_description_minor)

        self.show_proxy_help.setGeometry(QtCore.QRect(400, 235, 86, 25))
        self.show_proxy_help.setText('&Help')
        self.show_proxy_help.clicked.connect(info.show_proxy_help)

        self.label_2.setVisible(Common.use_proxy)
        self.label_3.setVisible(Common.use_proxy)
        self.comboBox.setVisible(Common.use_proxy)
        self.label_5.setVisible(Common.use_proxy)
        self.label_6.setVisible(Common.use_proxy)
        self.label_7.setVisible(Common.use_proxy)
        self.label_8.setVisible(Common.use_proxy)
        self.lineEdit.setVisible(Common.use_proxy)
        self.lineEdit_2.setVisible(Common.use_proxy)
        self.lineEdit_3.setVisible(Common.use_proxy)
        self.lineEdit_4.setVisible(Common.use_proxy)
        self.lineEdit_4.setVisible(Common.use_proxy)
        self.show_proxy_help.setVisible(Common.use_proxy)

    def nextId(self):
        if not self.checkBox.isChecked():
            Common.use_proxy = False
            return self.steps.index('torrc_page')
        else:
            Common.use_proxy = True

            if self.valid_ip(self.lineEdit.text()) and self.valid_port(self.lineEdit_2.text()):
                proxy_type = str(self.comboBox.currentText())

                if proxy_type.startswith('SOCKS4'):
                    proxy_type = 'SOCKS4'
                elif proxy_type.startswith('SOCKS5'):
                    proxy_type = 'SOCKS5'
                elif proxy_type.startswith('HTTP / HTTPS'):
                    proxy_type = 'HTTP/HTTPS'

                Common.proxy_type = proxy_type
                Common.proxy_ip = str(self.lineEdit.text())
                Common.proxy_port = str(self.lineEdit_2.text())
                Common.proxy_username = str(self.lineEdit_3.text())
                Common.proxy_password = str(self.lineEdit_4.text())

                return self.steps.index('torrc_page')
            else:
                return self.steps.index('proxy_wizard_page') # stay at the page until a proxy type is selected'''

    def valid_ip(self, ip):
        # TODO: use re to detect if the format of IP is not correct
        # The difficulty is that the IP can be hostname which is almost free form
        # However, we should at least check if it is empty
        return True #(ip == "" or ip.isspace())

    def valid_port(self, port):
        try:
            if int(port) >= 1 and int(port) <= 65535:
                return True
            else:
                return False
        except (ValueError, TypeError):
            return False

    # called by button toggled signal.
    def set_next_button_state(self, state):
        if state:
            self.button(QWizard.NextButton).setEnabled(False)
        else:
            self.button(QWizard.NextButton).setEnabled(True)

    ''' This function will be called by
    self.comboBox.currentIndexChanged[str].connect(self.option_changed)
    It will pass a parameter text which is the context in the current comboBox
    '''
    def option_changed(self, text):
        if text == 'HTTP / HTTPS':
            self.label_6.show()  # username label
            self.lineEdit_3.show()  # username input

            self.label_8.show()  # password label
            self.lineEdit_4.show()  # password input

        elif text == 'SOCKS4':
            # Notice that SOCKS4 does not support proxy username and password
            # Therefore, should the input be disabled for usability

            self.label_6.setVisible(False)
            self.lineEdit_3.setVisible(False)

            self.label_8.setVisible(False)
            self.lineEdit_4.setVisible(False)

        elif text == 'SOCKS5':
            self.label_6.show()
            self.lineEdit_3.show()

            self.label_8.show()
            self.lineEdit_4.show()

    def enable_proxy(self, state):
        ## state is a boolean indicating if checkBox is checked or not
        self.label_2.setVisible(state)
        self.label_3.setVisible(state)
        self.comboBox.setVisible(state)
        self.label_5.setVisible(state)
        self.label_6.setVisible(state)
        self.label_7.setVisible(state)
        self.label_8.setVisible(state)
        self.lineEdit.setVisible(state)
        self.lineEdit_2.setVisible(state)
        self.lineEdit_3.setVisible(state)
        self.lineEdit_4.setVisible(state)
        self.lineEdit_4.setVisible(state)
        self.show_proxy_help.setVisible(state)



class TorrcPage(QWizardPage):
    def __init__(self):
        super(TorrcPage, self).__init__(None)

        self.steps = Common.wizard_steps

        self.layout = QVBoxLayout(self)

        self.label = QLabel(self)
        self.layout.addWidget(self.label)

        self.groupBox = QGroupBox(self)
        self.layout.addWidget(self.groupBox)

        self.label_2 = QLabel(self.groupBox)
        self.label_3 = QLabel(self.groupBox)
        self.label_4 = QLabel(self.groupBox)
        self.label_5 = QLabel(self.groupBox)
        self.label_6 = QLabel(self.groupBox)
        self.label_7 = QLabel(self.groupBox)
        self.pushButton = QPushButton(self.groupBox)
        self.horizontal_line = QFrame(self.groupBox)
        self.torrc = QTextBrowser(self.groupBox)

        self.show_detail = False
        self.setup_ui()

    def setup_ui(self):
        font_title = Common.font_title
        font_description_main = Common.font_description_main
        font_description_minor = Common.font_description_minor
        font_option = Common.font_option

        self.label.setText('   Summary')
        self.label.setFont(font_title)
        self.label.setGeometry(QtCore.QRect(0, 0, 0, 0))

        self.groupBox.setMinimumSize(QtCore.QSize(Common.groupBox_width, Common.groupBox_height))
        self.groupBox.setGeometry(QtCore.QRect(0, 20, 0, 0))
        self.groupBox.setFlat(True)

        self.label_2.setGeometry(QtCore.QRect(80, 20, 100, 50))
        self.label_2.setText(" Status: ")
        self.label_2.setFont(font_description_minor)

        self.label_3.setGeometry(QtCore.QRect(140, 20, 500, 50))
        self.label_3.setText("Probably an error occurred")
        self.label_3.setFont(font_option)

        self.label_4.setGeometry(QtCore.QRect(80, 47, 100, 50))
        self.label_4.setText("Bridges: ")
        self.label_4.setFont(font_description_minor)

        self.label_5.setGeometry(QtCore.QRect(140, 47, 500, 50))

        self.label_5.setText("Custom vanilla")

        self.label_5.setFont(font_option)

        self.label_6.setGeometry(QtCore.QRect(80, 75, 100, 50))
        self.label_6.setText("   Proxy: ")
        self.label_6.setFont(font_description_minor)

        self.label_7.setGeometry(QtCore.QRect(140, 75, 500, 50))
        self.label_7.setText("Probably an error occurred")
        self.label_7.setFont(font_option)

        self.setLayout(self.layout)

        self.pushButton.setEnabled(True)
        self.pushButton.setGeometry(QtCore.QRect(430, 100, 86, 25))
        self.pushButton.setText('Show torrc')
        self.pushButton.clicked.connect(self.detail)

        self.horizontal_line.setFrameShape(QFrame.HLine)
        self.horizontal_line.setFrameShadow(QFrame.Sunken)
        self.horizontal_line.setGeometry(15, 130, 510, 5)

        # This is the QTextEdit that shows torrc files
        self.torrc.setVisible(self.show_detail)
        self.torrc.setGeometry(QtCore.QRect(20, 145, 500, 190))
        self.torrc.setStyleSheet("background-color:white;")
        # Allow long input appears in one line.
        self.torrc.setLineWrapColumnOrWidth(1500)
        self.torrc.setLineWrapMode(QTextEdit.FixedPixelWidth)

    def nextId(self):
        return self.steps.index('tor_status_page')

    def detail(self):
        self.show_detail = not self.show_detail
        self.torrc.setVisible(self.show_detail)
        if self.show_detail:
            self.pushButton.setText('&Hide')
        else:
            self.pushButton.setText('&Show torrc')


class TorStatusPage(QWizardPage):
    def __init__(self):
        super(TorStatusPage, self).__init__()
        self.steps = Common.wizard_steps
        self.bootstrap_text = QLabel(self)
        self.text = QLabel(self)
        self.bootstrap_progress = QProgressBar(self)
        self.layout = QGridLayout()
        self.setup_ui()

    def setup_ui(self):
        font_description_minor = Common.font_description_minor
        font_description_main = Common.font_description_main
        font_option = Common.font_option

        self.text.setFont(font_description_main)
        self.text.setWordWrap(True)
        self.text.setAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.text.setMinimumSize(0, 290)

        self.bootstrap_progress.setMinimumSize(400, 0)
        self.bootstrap_progress.setMinimum(0)
        self.bootstrap_progress.setMaximum(100)
        self.bootstrap_progress.setVisible(False)

        self.layout.addWidget(self.text, 0, 1, 1, 2)
        self.layout.addWidget(self.bootstrap_progress, 1, 1, 1, 1)
        self.setLayout(self.layout)


app = QApplication(sys.argv)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

timer = QtCore.QTimer()
timer.start(500)
timer.timeout.connect(lambda: None)


class AnonConnectionWizard(QWizard):
    def __init__(self):
        super(AnonConnectionWizard, self).__init__()

        translation = _translations(Common.translations_path, 'anon-connection-wizard')
        self._ = translation.gettext

        self.args = torrc_gen.parse_torrc()

        Common.bridge_type = self.args[0]
        Common.proxy_type = self.args[1]
        Common.proxy_ip = self.args[2]
        Common.proxy_port = self.args[3]
        Common.proxy_username = self.args[4]
        Common.proxy_password = self.args[5]
        Common.use_default_bridges = self.args[6]
        Common.use_proxy = self.args[7]

        self.steps = Common.wizard_steps

        self.connection_main_page = ConnectionMainPage()
        self.addPage(self.connection_main_page)

        self.bridge_wizard_page = BridgesWizardPage()
        self.addPage(self.bridge_wizard_page)

        self.proxy_wizard_page = ProxyWizardPage()
        self.addPage(self.proxy_wizard_page)

        self.torrc_page = TorrcPage()
        self.addPage(self.torrc_page)

        self.tor_status_page = TorStatusPage()
        self.addPage(self.tor_status_page)

        self.bridges = []
        self.proxy_type = ''
        self.tor_status = ''
        self.bootstrap_done = False

        self.setup_ui()

    def setup_ui(self):
        self.setWindowIcon(QtGui.QIcon("/usr/share/anon-connection-wizard/advancedsettings.ico"))
        self.setWindowTitle('Anon Connection Wizard')
        self.setFixedSize(580, 450)  # This is important to control the fixed size of the window

        # signal-and-slot
        self.button(QWizard.BackButton).clicked.connect(self.back_button_clicked)
        self.button(QWizard.NextButton).clicked.connect(self.next_button_clicked)
        self.button(QWizard.CancelButton).clicked.connect(self.cancel_button_clicked)

        # Since this is the index page, no back_button is needed.
        self.button(QWizard.BackButton).hide()
        self.button(QWizard.BackButton).setEnabled(False)

        self.button(QWizard.FinishButton).clicked.connect(self.finish_button_clicked)

        self.button(QWizard.CancelButton).show()
        self.button(QWizard.CancelButton).setEnabled(True)
        self.button(QWizard.CancelButton).setText('Quit')
        self.exec_()

    def update_bootstrap(self, bootstrap_phase, bootstrap_percent):
        self.tor_status_page.bootstrap_progress.setValue(bootstrap_percent)
        if bootstrap_percent == 100:
            self.tor_status_page.text.setText('<p><b>Tor bootstrapping done</b></p>Bootstrap phase: {0}'
                                              .format(bootstrap_phase))
            self.bootstrap_done = True
            self.show_finish_button()
        else:
            self.tor_status_page.text.setText('<p><b>Bootstrapping Tor...</b></p>Bootstrap phase: {0}'
                                              .format(bootstrap_phase))

        if bootstrap_phase == 'no_controller':
            self.bootstrap_thread.terminate()
            buttonReply = QMessageBox.warning(self, 'Tor Controller Not Constructed', 'Tor controller \
                                              cannot be constructed.')
            if buttonReply == QMessageBox.Ok:
                sys.exit(1)

        elif bootstrap_phase == 'cookie_authentication_failed':
            self.bootstrap_thread.terminate()
            buttonReply = QMessageBox.Warning(self, 'Tor Controller Authentication Failed', 'Tor allows \ '
                                              'for authentication by reading it a cookie file, but we cannot read \ '
                                              'that file (probably due to permissions)', QMessageBox.Ok )
            if buttonReply == QMessageBox.Ok:
                sys.exit(1)

    def next_button_clicked(self):
        self.bridge_wizard_page.reformat_custom_bridge_input()
        if self.currentId() == self.steps.index('connection_main_page'):

            self.button(QWizard.CancelButton).show()
            self.button(QWizard.FinishButton).hide()
            # Common.from_bridge_page_1 = True
            # Common.from_proxy_page_1 = True

        if self.currentId() == self.steps.index('bridge_wizard_page'):
            # Common.from_bridge_page_1 serves as a flag to work around the bug that
            # message jump out when switching from bridge_wizard_page_1 to bridge_wizard_page
            # if not Common.from_bridge_page_1:
            # Remember previous settings
            self.bridge_wizard_page.bridges_frame.setVisible(self.bridge_wizard_page.bridges_checkbox.isChecked())
            if (self.bridge_wizard_page.bridges_checkbox.isChecked() and
                    self.bridge_wizard_page.custom_option.isChecked()):
                if not self.bridge_wizard_page.valid_custom_bridges():
                    self.reply = QMessageBox(QMessageBox.NoIcon, 'Warning',
                        '''<p><b>  Custom bridge list is blank or invalid</b></p>
                        <p> Please input valid custom bridges or use provided bridges instead.</p>''',
                        QMessageBox.Ok)
                    self.reply.exec_()

            # Common.from_bridge_page_1 = False
            # Common.from_proxy_page_1 = True

        if self.currentId() == self.steps.index('proxy_wizard_page'):
            # Common.from_proxy_page_1 serves as a flag to work around the bug that
            # message jump out when switching from proxy_wizard_page_1 to proxy_wizard_page
            # if not Common.from_proxy_page_1:
            if self.proxy_wizard_page.checkBox.isChecked():
                if not (
                self.proxy_wizard_page.valid_ip(self.proxy_wizard_page.lineEdit.text()) and
                self.proxy_wizard_page.valid_port(self.proxy_wizard_page.lineEdit_2.text())
                ):
                    self.reply = QMessageBox(QMessageBox.NoIcon, 'Warning',
                    '''<p><b>  Please input valid Address and Port number.</b></p>
                    <p> The Address should look like: 127.0.0.1 or localhost</p>
                    <p> The Port number should be an integer between 1 and 65535</p>''', QMessageBox.Ok)
                    self.reply.exec_()
            # Common.from_proxy_page_1 = False

        if self.currentId() == self.steps.index('torrc_page'):
            self.button(QWizard.BackButton).show()
            self.button(QWizard.CancelButton).show()
            self.button(QWizard.FinishButton).hide()
            #self.center()

            ''' io() will write lines to 40_tor_control_panel.conf
            basing on user's selection in anon_connection_wizard
            Here we call the io() so that we can show user the torrc file
            '''
            self.io()

            if not Common.disable_tor:
                self.torrc_page.label_3.setText('Tor will be enabled.')
                if not Common.use_default_bridges:
                    self.torrc_page.label_5.setText('None Selected')

                else:
                    if Common.use_default_bridges:
                        if Common.bridge_type == 'obfs4':
                            self.torrc_page.label_5.setText('Provided obfs4')
                        elif Common.bridge_type == 'meek-azure':
                            self.torrc_page.label_5.setText('Provided meek-azure')
                        elif Common.bridge_type == 'snowflake':
                            self.torrc_page.label_5.setText('Provided snowflake')
                    else:
                        if Common.bridge_custom.lower().startswith('obfs4'):
                            self.torrc_page.label_5.setText('Custom obfs4')
                        elif Common.bridge_custom.lower().startswith('meek_lite'):
                            self.torrc_page.label_5.setText('Custom meek_lite')
                        elif Common.bridge_custom.lower().startswith('snowflake'):
                            self.torrc_page.label_5.setText('Custom snowflake')
                        else:
                            self.torrc_page.label_5.setText('Custom vanilla')

                self.torrc_page.label_7.setText('Tor will be enabled.')
                torrc_text = open(Common.torrc_file_path).read()
                self.torrc_page.torrc.setPlainText(torrc_text)

            else:
                ''' Notice that this condition will not be used now, because
                anon_connection_wizard will skip torrc_page when disable_tor is selected to be true.
                However, we still leave the code here in case of any related changes in the future.
                '''
                #self.torrc_page.text.setText(self._('tor_disabled'))
                self.torrc_page.label_3.setText('Tor will be disabled.')
                self.torrc_page.label_4.hide()
                self.torrc_page.label_5.hide()
                self.torrc_page.label_6.hide()
                self.torrc_page.label_7.hide()
                self.torrc_page.pushButton.hide()
                torrc_text = open(Common.torrc_file_path).read()
                self.torrc_page.torrc.setPlainText(torrc_text)
                #self.torrc_page.icon.setPixmap(QtGui.QPixmap( \
                    #'/usr/share/icons/oxygen/48x48/status/task-attention.png'))

            if not Common.use_proxy:
                self.torrc_page.label_7.setText('None Selected')
            else:
                if Common.proxy_type == 'HTTP/HTTPS':
                    self.torrc_page.label_7.setText('HTTP(S)  {0} : {1}'.format(Common.proxy_ip, Common.proxy_port))
                elif Common.proxy_type == 'SOCKS4':
                    self.torrc_page.label_7.setText('Socks4  {0} : {1}'.format(Common.proxy_ip, Common.proxy_port))
                elif Common.proxy_type == 'SOCKS5':
                    self.torrc_page.label_7.setText('Socks5  {0} : {1}'.format(Common.proxy_ip, Common.proxy_port))

        if self.currentId() == self.steps.index('tor_status_page'):
            self.tor_status_page.text.setText('')  # This will clear the text left by different Tor status statement
            self.button(QWizard.BackButton).show()
            self.button(QWizard.CancelButton).show()
            self.button(QWizard.FinishButton).hide()

            '''Arranging different tor_status_page according to the value of disable_tor.'''
            if not Common.disable_tor:
                if os.path.exists(Common.torrc_file_path):
                    ## Move the tmp file to the real .conf only when user
                    ## clicks the connect button. This may overwrite the
                    ## previous .conf, but it does not matter.
                    cat(Common.acw_comm_file_path)
                    content = open(Common.torrc_file_path).read()
                    write_to_temp_then_move(content)

                self.tor_status_page.bootstrap_progress.show()

                self.tor_status_result = tor_status.set_enabled()
                self.tor_status = self.tor_status_result[0]
                self.tor_status_code = str(self.tor_status_result[1])

                if self.tor_status == 'tor_enabled' or self.tor_status == 'tor_already_enabled':
                    self.tor_status_page.bootstrap_progress.show()
                    self.bootstrap_thread = tor_bootstrap.TorBootstrap(self)
                    self.bootstrap_thread.signal.connect(self.update_bootstrap)
                    self.bootstrap_thread.start()

                elif self.tor_status == 'cannot_connect':
                    print('tor_status: ' + self.tor_status + self.tor_status_code, file=sys.stderr)
                    self.tor_status_page.bootstrap_progress.hide()
                    self.tor_status_page.text.setText('<p><b>Tor failed to (re)start.</b></p>\
                    <p>Job for tor@default.service failed because the control process \
                    exited with error code.</p>' +
                    'Error Code: ' + self.tor_status_code + '\n' +
                    '<p>Often, this is because of your torrc file(s) has corrupted settings.</p>' +
                    '<p>See "systemctl status tor@default.service" and \
                    "journalctl -xe" for details.</p>\
                    <p>You may not be able to use any network facing application for now.</p>')

                else:
                    print('Unexpected tor_status: ' + self.tor_status + '\n' +
                        "Error Code:" + self.tor_status_code, file=sys.stderr)
                    # display error message on GUI
                    self.tor_status_page.bootstrap_progress.hide()
                    self.tor_status_page.text.setText('<p><b>Unexpected Exception.</b></p>\
                    <p>You may not be able to use any network facing application for now.</p>\
                    Unexpected exception reported from tor_status module:' + self.tor_status\
                    + '\n' + "Error Code:" + self.tor_status_code)

            else:
                self.tor_status = tor_status.set_disabled()

                ## Related to meek and snowflake only.
                ## See edit_etc_resolv_conf_add above.
                edit_etc_resolv_conf_remove()

                self.tor_status_page.bootstrap_progress.hide()
                self.tor_status_page.text.show()
                self.tor_status_page.text.setText('<p><b>Tor is disabled.</b></p>\
                <p>You will not be able to use any network facing application.</p>\
                <p>You can enable Tor at any moment using <i>Anon Connection Wizard</i> \
                from your application launcher, or from a terminal:\
                <blockquote><code>anon-connection-wizard</code></blockquote> \
                or even simply press the <i>Back button</i> and select another option right now.')
                self.show_finish_button()

    def back_button_clicked(self):
        try:
            if self.bootstrap_thread:
                self.bootstrap_thread.terminate()
                ## since terminate() should be executed only once,
                ## we should set the flag as False after the execution.
                self.bootstrap_thread = False

                ''' recover Tor to the initial status before the starting of anon_connection_wizard
                '''
                if Common.init_tor_status == 'tor_enabled':
                    pass
                elif Common.init_tor_status == 'tor_disabled':
                    tor_status.set_disabled()
        except AttributeError:
            pass

        # if self.currentId() == self.steps.index('connection_main_page'):
        #     Common.from_bridge_page_1 = True
        #     Common.from_proxy_page_1 = True

        self.bootstrap_done = False
        self.button(QWizard.FinishButton).hide()
        self.button(QWizard.CancelButton).show()

        # if self.currentId() == self.steps.index('bridge_wizard_page'):
        #     Common.from_proxy_page_1 = True

    def cancel_button_clicked(self):
        try:
            if self.bootstrap_thread:
                self.bootstrap_thread.terminate()
                ## When user cancel Tor bootstrap,
                ## it is reasonable to assume user wants to disable Tor
                tor_status.set_disabled()

            # recover Tor to the initial status before the starting of anon_connection_wizard
            if Common.init_tor_status == 'tor_enabled':
                pass
            elif Common.init_tor_status == 'tor_disabled':
                tor_status.set_disabled()
        except AttributeError:
            pass

    def finish_button_clicked(self):
        # The True indicates the acw has finished successfully
        # TODO: this does not work as expected, even the cancel button is clicked,
        # the wizard still return True
        return True

    def show_finish_button(self):
        if self.bootstrap_done or Common.disable_tor:
            self.button(QWizard.CancelButton).hide()
            self.button(QWizard.FinishButton).show()
            self.button(QWizard.FinishButton).setFocus()

    def io(self):
        repair_torrc.repair_torrc()  # This guarantees a good set of torrc files

        args = []

        if Common.use_default_bridges:
            if Common.bridge_type == 'obfs4':
                args.append('obfs4')
            elif Common.bridge_type == 'meek-azure':
                args.append('meek_lite')
            elif Common.bridge_type == 'snowflake':
                args.append('snowflake')
            elif Common.bridge_type == '':
                pass

            bridges = json.loads(open(Common.bridges_default_path).read())
            for bridge in bridges['bridges'][Common.bridge_type]:
                args.append('{0}\n'.format(bridge))

        elif Common.use_custom_bridges:
            args.append('Custom bridges')
            print(f"[DEBUG] Custom : {Common.bridge_custom}")
            if not Common.bridge_custom == '':
                args.append(Common.bridge_custom)

        if Common.use_proxy:
            if Common.proxy_type == 'HTTP/HTTPS':
                args.append('HTTPSProxy {0}:{1}\n'.format(Common.proxy_ip, Common.proxy_port))
                if Common.proxy_username:
                    args.append('HTTPSProxyAuthenticator {0}:{1}\n'.format(Common.proxy_username,
                                                                        Common.proxy_password))
            elif Common.proxy_type == 'SOCKS4':
                # Notice that SOCKS4 does not support proxy username and password
                args.append('Socks4Proxy {0}:{1}\n'.format(Common.proxy_ip, Common.proxy_port))

            elif Common.proxy_type == 'SOCKS5':
                args.append('Socks5Proxy {0}:{1}\n'.format(Common.proxy_ip, Common.proxy_port))
                if Common.proxy_username:
                    args.append(f'Socks5ProxyUsername {Common.proxy_username}\n')
                    if Common.proxy_password:
                        args.append(f'Socks5ProxyPassword {Common.proxy_password}\n')

        print(f"[DEBUG] args = {args}")
        torrc_gen.gen_torrc(args)


def main():
    if os.geteuid() == 0:
        print('anon_connection_wizard.py: ERROR: Do not run with sudo / as root!')
        sys.exit(1)

    # Available styles: "windows", "motif", "cde", "sgi", "plastique" and "cleanlooks"
    # TODO: use customized css instead. Take Tor Launcher's css as a reference
    QApplication.setStyle('cleanlooks')

    wizard = AnonConnectionWizard()


if __name__ == "__main__":
    main()
