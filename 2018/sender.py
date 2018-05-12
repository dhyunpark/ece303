# Written by S. Mevawala, modified by D. Gitzel

import logging
import socket
import channelsimulator
import utils
import sys
import zlib

class Sender(object):

    def __init__(self, inbound_port=50006, outbound_port=50005, timeout=10, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port, debug_level=debug_level)
        self.simulator.sndr_setup(timeout)
        self.simulator.rcvr_setup(timeout)

class BogoSender(Sender):

    def __init__(self):
        super(BogoSender, self).__init__(timeout=.01)

    def int2bi(self, number):
        #converts number to a 4 byte bytearray
        bytArr = bytearray([(a & 0xFF000000) >> 24, (a & 0xFF0000) >> 16, (a & 0xFF00) >> 8, (a & 0xFF)])
        return bytArr

    def bi2int(self, bytArr):
        #converts a 4 byte bytearray to an integer
        number = int(''.join([string.zfill(s,8) for s in map(lambda n : n[2:], map(bin, bytArr))]), 2)
        return number

    def checksum(data):
        sum1 = 0
        sum2 = 0
        i = 0
        while i < len(data):
            sum1 = (sum1 + ord(data[i]))%65535
            sum2 = (sum2 + sum1)%65535
            i+=1
        x = sum1*65536 + sum2
        checksum = bytearray.fromhex('{:08x}'.format(x))
        pad = bytearray(32-len(checksum))
        return pad + checksum

    def send(self, data):
        pDataSize = 1016 # + 4 bytes for seq number + 4 bytes for checksum
        pList = []
        windSize = 10

        # create list of packets
        for i in xrange(0, len(data), pDataSize):
            upper = i + pDataSize

            if upper > len(data):
                upper = len(data)

            # create components
            seqNum = int2bi(i)         #create unique packet seqNum 4 byte bytearray
            datachunk = data[i:upper]
            chksum = checksum(datachunk)

            # combine components
            packet = seqNum + datachunk + chksum

            # add packet to packet list
            plist.append({
                "packet": bytearray(packet),
                "ack": False,
                "sent": False
            })

        lower = 0
        upper = 0

        # check window size at end of data
        numPackets = len(plist)
        if numPackets < windSize:
            windSize = numPackets

        while True:
            try:
                    upper = lower + windSize

                    if upper > numPackets:
                        upper = numPackets

                    for i in xrange(lower, upper):
                        if not plist[i]['sent']:
                            self.simulator.u_send(plist[i]['packet'])
                            plist[i]['sent'] = True

                    while True:

                        ack = self.simulator.u_receive()
                        chksum = checksum(ack[:4])
                        ack_chksum = bi2int(ack[-4:])

                        if chksum == ack_chksum:

                            seqNum = ack[:4]
                            plist[seqNum]['ack'] = True

                            if seqNum == plist[upper - 1]['packet'][0]:
                                break

                    for i in xrange(lower, upper):
                        if not plist[i]['ack']:
                            break
                        else:
                            lower += windSize

            except socket.timeout:

                for i in xrange(lower, upper):
                    if not plist[i]['ack']:
                        self.simulator.u_send(plist[i]['packet'])


if __name__ == "__main__":
    # test out BogoSender
    DATA = bytearray(sys.stdin.read())
    sndr = BogoSender()
    sndr.send(DATA)
