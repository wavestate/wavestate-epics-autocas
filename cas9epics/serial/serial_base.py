"""
TODO, make a burt.req generator and a monitor.req generator, as well as a utility for merging monitor.reqs into a single SDF monitor.req file (and possibly restarting a soft SDF system)
"""
from __future__ import division, print_function, unicode_literals

import declarative

from .. import cas9core
from ..subservices import error

#from . import utilities


class SerialError(IOError):
    pass

class SerialTimeout(SerialError):
    pass

class SerialConnection(
    cas9core.CASUser,
):
    @declarative.dproperty
    def rb_connected(self):
        rb = cas9core.RelayBool(False)
        self.cas_host(
            rb,
            name = 'CONNECT',
            writable = False,
        )
        return rb

    @declarative.dproperty
    def rb_running(self):
        rb = cas9core.RelayBool(False)
        self.cas_host(
            rb,
            name = 'RUNNING',
            writable = False,
        )
        return rb

    @declarative.dproperty
    def error(self):
        return error.RVError(
            parent = self,
        )

    @declarative.dproperty
    def _block_data(self):
        return dict()

    @declarative.dproperty
    def _blocks_queued(self):
        return []

    def cmd_object(self):
        b = declarative.Bunch()

        def writeline(line):
            print("SERIAL: ", line)

        b.writeline = writeline

        def readline():
            return '100'
        b.readline = readline
        return b

    def block_enqueue(self, blockfunc):
        self._block_data[blockfunc]
        self._blocks_queued.append(blockfunc)

        self.reactor.enqueue(self.run, future_s = .1, limit_s = 1)
        return

    def queue_clear(self):
        self._blocks_queued[:] = []
        return

    def block_add(
            self,
            func,
            ordering = None,
            parent = None,
            chain = [],
            name = None,
            prefix = None,
    ):
        """
        if ordering is None then it may LAST or FIRST - NO GUARANTEE, otherwise they are sorted by ordering

        returns a key-function that can be enqueued to indicate to run the serial block in its correct context. If called it enqueues itself
        """
        def block_func():
            self.block_enqueue(block_func)
        if name is not None:
            if prefix is not None:
                name = '_'.join(list(prefix) + [name])
            block_func.__name__ = str(name)

        self._block_data[block_func] = dict(
            func = func,
            ordering = ordering,
            parent = parent,
            chain = list(chain),
        )
        #can add to chain later
        return block_func

    def block_chain(self, bfunc, *chains):
        #TODO check that the chains are also block-functions
        self._block_data[bfunc]['chain'].extend(chains)

    def run(self):
        """
        generates the block-chain run tree and serial command object through the block-parents and chains. Doesn't need to check for parent loop because that is prevented currently
        through the block creation convention that parents are specified.
        """
        self.rb_running.assign(True)

        #first to bfunc completion
        checked = set()
        stack = list(self._blocks_queued)
        #clear the previous list
        self._blocks_queued[:] = []

        plists = {
            None : []
        }
        while stack:
            bfunc = stack.pop()
            if bfunc in checked:
                continue
            #plists[bfunc] = []
            checked.add(bfunc)
            bdata = self._block_data[bfunc]
            stack.extend(bdata['chain'])

            bparent = bdata['parent']
            plist = plists.setdefault(bparent, [])
            plist.append(bfunc)
            if bparent is not None:
                stack.append(bparent)

        cmd = self.cmd_object()
        #utilities.pprint(plists)

        #get first list
        def block_call(bfunc):
            plist = plists.get(bfunc, [])
            plist.sort(key = lambda bfunc: self._block_data[bfunc]["ordering"])
            for bfunc in plist:
                was_called = [False]

                def remainder_call():
                    was_called[0] = True
                    return block_call(bfunc)

                cmd.block_remainder = remainder_call
                self._block_data[bfunc]["func"](cmd)
                cmd.block_remainder = None
                if not was_called[0]:
                    remainder_call()

        #call on the root parent
        block_call(None)
        #the block list is a sequence of bfunc, list pairs. The bfunc serial functions are called and any associated inner blocks are in the following sequence
        self.rb_running.assign(False)


class SerialSubBlock(
    cas9core.CASUser,
):
    """
    Takes a serial device and defines a new serial device with its own parent block
    """

    @declarative.dproperty
    def serial(self, val):
        return

    @declarative.dproperty
    def rb_connected(self):
        rb = self.serial.rb_connected
        self.cas_host(
            rb,
            name = 'CONNECT',
            writable = False,
        )
        return rb

    @declarative.dproperty
    def rb_running(self):
        rb = self.serial.rb_running
        self.cas_host(
            rb,
            name = 'RUNNING',
            writable = False,
        )
        return rb

    @declarative.dproperty
    def error(self, val = None):
        if val is None:
            val = error.RVError(
                parent = self,
            )
        return val

    @declarative.dproperty
    def SB_parent(self):
        raise NotImplementedError("Subclasses must override!")

    def cmd_object(self):
        self.serial.cmd_object()

    def block_enqueue(self, blockfunc):
        self.serial.block_enqueue(blockfunc)

    def queue_clear(self):
        self.serial.queue_clear()

    def block_add(
            self,
            func,
            ordering = None,
            parent   = None,
            chain    = [],
            name     = None,
            prefix   = None,
    ):
        """
        Uses the parent serial object, but injects its own parent block by default.
        This allows address/settings injection for certain devices
        """
        if parent is None:
            parent = self.SB_parent

        self.serial.block_add(
            ordering = ordering,
            parent   = parent,
            chain    = chain,
            name     = name,
            prefix   = prefix,
        )

    def block_chain(self, bfunc, *chains):
        self.serial.block_chain(bfunc, *chains)

    def run(self):
        """
        """
        #TODO could make a queue separator and do runs that way...
        self.serial.run()


