# Written by S. Mevawala, modified by D. Gitzel

import logging
import string
import channelsimulator
import utils
import sys
import socket

class Receiver(object):

    def __init__(self, inbound_port=50005, outbound_port=50006, timeout=0.01, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.rcvr_setup(timeout)
        self.simulator.sndr_setup(timeout)

    def receive(self):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


class BogoReceiver(Receiver):
    PACKET_SIZE = 1016
    WINDOW =
    ACK_DATA = bytes(123)

    def __init__(self):
        super(BogoReceiver, self).__init__()

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

    def receive(self):
        end = False
        self.logger.info("Receiving on port: {} and replying with ACK on port: {}".format(self.inbound_port, self.outbound_port))
        rList = dict()

        while True:
            try:
                packet = self.simulator.u_receive()  # receive data

                if len(packet) < 1024:
                    end = True  #denote the end of transmission
                else:
                    self.logger.info("Got data from socket: {}".format(
                        data.decode('ascii')))  # note that ASCII will only decode bytes in the range 0-127

                    #extract seqNum checksum and calculate data's checksum
                    seqNum = bi2int(packet[:3])
                    chkSum = bi2int(packet[-3:])
                    dataSum = checksum(packet[4:-4])

                    #if the data checksum is equal to calculated checksum, add to list of received packets and create an ACK packet
                    if dataSum == chkSum:
                        rList[seqNum] = {
                            'packet': bytearray(packet),
                            'acked': False,
                        }
                        #create a checksum for the sequence number of the ACK corresponding to the received packet being sent back
                        ack = bytearray(seqNum + checksum(seqNum))
                        #send ACK packet
                        self.simulator.u_send(ack)
                        rList[seqNum]['acked'] = True
                    else:
                        pass

            except socket.timeout:
                if end:
                    break
                else:
                    pass

        for entry in rList:
            if entry != None:
                sys.stdout.write(entry['packet'][4:-4])

        sys.exit()

if __name__ == "__main__":
    # test out BogoReceiver
    rcvr = BogoReceiver()
    rcvr.receive()
