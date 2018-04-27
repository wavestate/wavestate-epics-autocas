"""
"""
from __future__ import division, print_function, unicode_literals

import sys
from .. import cas9core
from ..serial import SerialError
import re
from . import IFRSigGenCommon


class IFR2026(
    cas9core.CASUser,
):
    @cas9core.dproperty
    def serial(self, val):
        return val

    @cas9core.dproperty
    def SBlist_readbacks(self):
        return []

    @cas9core.dproperty
    def SBlist_setters(self):
        return []

    @cas9core.dproperty
    def rb_autoset(self):
        rb = cas9core.RelayBool(False)
        self.cas_host(
            rb,
            'AUTOSET',
            writable = True,
            urgentsave = 10,
        )
        return rb

    @cas9core.dproperty
    def _onconnect_setup(self):
        def connect_cb(value):
            if value:
                if self.rb_autoset:
                    for RB in self.SBlist_setters:
                        RB()
                for RB in self.SBlist_readbacks:
                    RB()
                self.reactor.send_task(self.serial.run)
                return
        self.serial.rb_connected.register(
            callback = connect_cb,
        )
        return

    @cas9core.dproperty_ctree(default = None)
    def device_SN(self, val):
        """
        Serial number of the device to check via *IDN? call.
        ID command Must succeed to attempt future commands and SN must match if specified
        """
        if val == '':
            val = None
        return val

    @cas9core.dproperty
    def block_root(self):
        def action_sequence(cmd):
            with self.serial.error.clear_pending():
                try:
                    cmd.block_remainder()
                except SerialError as E:
                    self.serial.error(1, E.message)
                else:
                    self.serial.rb_communicating.put(True)

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            name = 'root',
            prefix = self.prefix_full,
        )
        return block

    @cas9core.dproperty
    def SB_SN_id_check(self):
        def action_sequence(cmd):
            cmd.writeline('*IDN?')
            val = cmd.readline()
            SN_found = val.strip()
            if self.device_SN is not None:
                if SN_found != self.device_SN:
                    print("Warning, device expected {0} but device found: {1}".format(self.device_SN, SN_found), file = sys.stderr)
                    raise SerialError("Wrong Device")

            try:
                with self.serial.error.clear_pending():
                    cmd.block_remainder()
            finally:
                pass

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            parent = self.block_root,
            name = 'id_check',
            prefix = self.prefix_full,
        )
        return block

    #@cas9core.dproperty
    #def lockout_soft(self):
    #    """
    #    Sends soft (front panel) lockout signal when using rs232.
    #    """
    #    def action_sequence(cmd):
    #        #special character to activate local lockout
    #        cmd.writeline(chr(01))
    #        for i in range(30):
    #            cmd.writeline('*TST?')
    #            resp = cmd.readline(timeout_s = 0.02)
    #            if resp:
    #                break

    #    block = self.serial.block_add(
    #        action_sequence,
    #        ordering = -1,
    #        parent = self.SB_SN_id_check,
    #        name = 'lockout_soft',
    #        prefix = self.prefix_full,
    #    )
    #    return block

    @cas9core.dproperty
    def chnA(self):
        chn = IFR2026Channel(
            parent = self,
            name = 'chnA',
            device_channel_name = 'A',
            SB_parent = self.SB_SN_id_check,
        )
        self.SBlist_setters.extend(chn.SBlist_setters)
        self.SBlist_readbacks.extend(chn.SBlist_readbacks)
        return chn

    @cas9core.dproperty
    def chnB(self):
        chn = IFR2026Channel(
            parent = self,
            name = 'chnB',
            device_channel_name = 'B',
            SB_parent = self.SB_SN_id_check,
        )
        self.SBlist_setters.extend(chn.SBlist_setters)
        self.SBlist_readbacks.extend(chn.SBlist_readbacks)
        return chn


class IFR2026Channel(
    cas9core.CASUser,
):
    """
    Must be hosted by a IFR2026
    """

    @cas9core.dproperty
    def serial(self):
        return self.parent.serial

    @cas9core.dproperty
    def device_channel_name(self, val):
        return val

    @cas9core.dproperty
    def SB_parent(self, val):
        """
        Parent serial-block
        """
        return val

    @cas9core.dproperty
    def SB_set_chn(self):
        #one group, the channel name
        re_SOURCE = re.compile('^:SOURCE (.)$')

        def action_sequence(cmd):
            cmd.writeline(':SOURCE {0};:SOURCE?'.format(self.device_channel_name))
            response = cmd.readline()
            match = re_SOURCE.match(response)
            if not match:
                raise SerialError("Channel Set Response: {0}".format(response))
            response_chn = match.group(1)
            if response_chn != self.device_channel_name:
                raise SerialError("Channel Not Set by request")

        block = self.serial.block_add(
            action_sequence,
            ordering = 0,
            parent = self.SB_parent,
            name = 'set_chn',
            prefix = self.prefix_full,
        )
        return block

    @cas9core.dproperty
    def channel(self):
        return IFRSigGenCommon.IFRSigGenChannel(
            parent = self,
            SB_parent = self.SB_set_chn,
            name = 'channel',
            prefix = None,
        )

    @cas9core.dproperty
    def SBlist_readbacks(self):
        return self.channel.SBlist_readbacks

    @cas9core.dproperty
    def SBlist_setters(self):
        return self.channel.SBlist_setters
