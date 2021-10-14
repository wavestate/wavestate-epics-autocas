"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals

from .. import cas9core
from .serial_base import (
    SerialError,
    SerialTimeout,
)


class SerialCommandResponse(cas9core.CASUser):
    autocount_str = '?'

    @cas9core.dproperty
    def serial(self, val):
        return val

    @cas9core.dproperty
    def rv_cmd1(self):
        rv = cas9core.RelayValueLongString('')
        self.cas_host(
            rv, 'CMD1',
            unit  = 'message',
            interaction = "setting",
        )
        return rv

    @cas9core.dproperty
    def rv_cmd2(self):
        rv = cas9core.RelayValueLongString('')
        self.cas_host(
            rv, 'CMD2',
            unit  = 'message',
            interaction = "setting",
        )
        return rv

    @cas9core.dproperty
    def rv_cmd3(self):
        rv = cas9core.RelayValueLongString('')
        self.cas_host(
            rv, 'CMD3',
            unit  = 'message',
            interaction = "setting",
        )
        return rv

    @cas9core.dproperty
    def rv_response_lines(self):
        rv = cas9core.RelayValueInt(-1)
        self.cas_host(
            rv, 'RESLINES',
            unit  = 'responses',
            interaction = "setting",
        )
        return rv

    @cas9core.dproperty
    def rv_response1(self):
        rv = cas9core.RelayValueLongString('')
        self.cas_host(
            rv, 'RESP1',
            unit  = 'message',
            interaction = "report",
        )
        return rv

    @cas9core.dproperty
    def rv_response2(self):
        rv = cas9core.RelayValueLongString('')
        self.cas_host(
            rv, 'RESP2',
            unit  = 'message',
            interaction = "report",
        )
        return rv

    @cas9core.dproperty
    def rv_response3(self):
        rv = cas9core.RelayValueLongString('')
        self.cas_host(
            rv, 'RESP3',
            unit  = 'message',
            interaction = "report",
        )
        return rv

    @cas9core.dproperty
    def rb_send(self):
        rb = cas9core.RelayBool(False)
        self.cas_host(
            rb, 'SEND',
            interaction = "setting",
            burt = False,
        )

        def _rb_clear():
            rb.value = False

        def _serial_action(value):
            if value:
                self.SB_cmd_response()
                self.serial.run()
                self.reactor.send_task(_rb_clear)

        rb.register(
            callback = _serial_action
        )
        return rb

    @cas9core.dproperty
    def SB_cmd_response(self):
        def action_sequence(cmd):
            try:
                responses = []
                for line in [
                        self.rv_cmd1.value,
                        self.rv_cmd2.value,
                        self.rv_cmd3.value,
                ]:
                    line = line.strip()
                    if not line:
                        continue
                    response_autocount = line.count(self.autocount_str)
                    print("DIRECT SEND: ", line)
                    cmd.writeline(line)
                    try:
                        for idx in range(response_autocount):
                            resp = cmd.readline(timeout_s = .25)
                            responses.append(resp)
                    except SerialTimeout as E:
                        pass

                if self.rv_response_lines.value >= 0:
                    remaining = self.rv_response_lines.value - len(responses)
                    try:
                        for idx in range(remaining):
                            resp = cmd.readline(timeout_s = .25)
                            responses.append(resp)
                    except SerialTimeout as E:
                        pass

                if len(responses) >= 1:
                    self.rv_response1.put_coerce(responses[0])
                else:
                    self.rv_response1.value = ''

                if len(responses) >= 2:
                    self.rv_response2.put_coerce(responses[1])
                else:
                    self.rv_response2.value = ''

                if len(responses) > 3:
                    self.rv_response2.put_coerce('<response >3 lines, check log>')
                elif len(responses) == 3:
                    self.rv_response3.put_coerce(responses[2])
                else:
                    self.rv_response3.value = ''

                for resp in responses:
                    print("DIRECT RESPONSE: ", resp)

            except SerialError as E:
                self.serial.error(2, E.message)
            finally:
                pass

        block = self.serial.block_add(
            action_sequence,
            ordering = 10,
            name = 'command_response',
            prefix = self.prefix,
        )
        return block
