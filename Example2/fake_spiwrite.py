#-------------------------------------------------------------------------------
# Name:        ni8452 USB-SPI Class interface
# Purpose:     Class driver for NI8452 and AWMF-0132/0133 K/Ka-Band Rx/Tx Quad ASICs
#
# Authors:      astreet and  Daskalakispiros
#
# Created:     25/04/2020
# Copyright:   (c) astreet 2020
# Licence:     <your licence>
# The code is based on project: https://github.com/30Wedge/AnokiwaveChipDemo
#-------------------------------------------------------------------------------


from Example2.ni8452io import SPI

# dll name is Ni845x.dll

# enumerate TXMODE, RXMODE, RX_11, SB
TX_MODE = 1
RX_MODE = 2
INIT_MODE = 4

ELEMENT_1_a = 0b000
ELEMENT_1_b = 0b001
ELEMENT_2_a = 0b010
ELEMENT_2_b = 0b011
ELEMENT_3_a = 0b100
ELEMENT_3_b = 0b101
ELEMENT_4_a = 0b110
ELEMENT_4_b = 0b111

COMM_ATT_0dB = 0b00
COMM_ATT_8dB = 0b01


class SpiInitException(Exception):
    """Error from initializing SPI bus"""

    def __init__(self, fret, msg=""):
        self.fret = fret
        self.msg = msg


class AwmfCommander:
    """
    Sends commands to the awmf through the SPI interposer
    usage:

    AwmfCommander.initSpi()
    AwmfCommander.setBeam(....)
    """

    # SPi interface handle placeholder
    testSPI = 0

    @classmethod
    def initSpi(cls):
        """
        opens the connection to the SPI bus and sets the clock
        """
        # open spi
        print("Searching for SPI Interface")

        cls.testSPI = SPI()
        fRet = cls.testSPI.ioOpen()
        # print('ioOpen():  \t{0}'.format(fRet))
        if fRet != 0:
            cls.testSPI.ioClose()
            raise SpiInitException(fRet, "ioOpen()")
        # set clock rate
        fRet = cls.testSPI.ioSetConfig(spiClk=1000)
        # print('ioSetConfig():\t{0}'.format(fRet))
        if fRet != 0:
            cls.testSPI.ioClose()
            raise SpiInitException(fRet, "ioSetConfig()")

        fRet = cls.testSPI.ioInit()
        # print('ioInit():  \t{0}'.format(fRet))
        if fRet != 0:
            cls.testSPI.ioClose()
            raise SpiInitException(fRet, "ioInit()")

        print("SPI initialized successfully")

    @classmethod
    def closeSPI(cls):
        """
        Close the SPI port and reset all ports to 0V
        """
        r = cls.testSPI.ioSafe()
        r1 = cls.testSPI.ioClose()
        if (r == 0 and r1 == 0):
            print("SPI closed successfully")
        else:
            raise SpiInitException(r1, "ioClose()")

    @classmethod
    def RF_EN(cls, mode ):
        if mode == RX_MODE:
            print("Writing in RX_EN")
            fRet = cls.testSPI.ioWriteDIO(1)  # Set DIO RX_EN pin
        elif mode == TX_MODE:
            print("Writing in TX_EN")
            fRet = cls.testSPI.ioWriteDIO(2)  # Set DIO TX_EN pin
        print("Writing in RF_EN")

    @classmethod
    def Anokiewave_write(cls, mode, input):
        """
         Writes  init register  signals on to the the spi bus.
        """

        # determine message and pack it
        unpackedData = []
        fRet = 0
        if mode == INIT_MODE:
            print("Writing in INIT_MODE")
            fRet = cls.testSPI.ioWriteDIO(0)  # Set DIO RX_EN pin
            unpackedData = input
        elif mode == RX_MODE:
            print("Writing in RX_MODE")
            fRet = cls.testSPI.ioWriteDIO(1)  # Set DIO RX_EN pin
            unpackedData = input
        elif mode == TX_MODE:
            print("Writing in TX_MODE")
            fRet = cls.testSPI.ioWriteDIO(2)
            unpackedData = input

        if fRet != 0:
            try:
                cls.closeSPI()
            except:
                pass
            raise SpiInitException(fRet, "ioWriteDIO()")

        wArr = cls.__packValues(unpackedData, in_width=60, packed_size=10)

        counter = 0
        for i in wArr:
            counter = counter + 1
            print('Packet N:', counter, 'Packed data:', bin(i))

        # ioWriteSPI hits LDB pin automatically
        rData, fRet = cls.testSPI.ioWriteSPI4(wArr, 10)  # send bits 8

        if fRet != 0:
            try:
                cls.closeSPI()
            except:
                pass
            raise SpiInitException(fRet, "ioWriteSPI4")

        return rData  # return data from device

    @staticmethod
    def decode_telemetry(message):

        """
                This function caltulates the telemetry data from the bytes stream
                :param message: the imput message
                :type message: bytes
        """

        out = 0
        for bit in message:
            out = (out << 10) | bit
        print(bin(out))
        message=out

        mask_tempe_ic = 0b_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0011_1111
        mask_power_1b = 0b_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0111_1100_0000
        mask_power_1a = 0b_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_1111_1000_0000_0000
        mask_power_2b = 0b_0000_0000_0000_0000_0000_0000_0000_0000_0000_0001_1111_0000_0000_0000_0000
        mask_power_2a = 0b_0000_0000_0000_0000_0000_0000_0000_0000_0011_1110_0000_0000_0000_0000_0000
        mask_power_3b = 0b_0000_0000_0000_0000_0000_0000_0000_0111_1100_0000_0000_0000_0000_0000_0000
        mask_power_3a = 0b_0000_0000_0000_0000_0000_0000_1111_1000_0000_0000_0000_0000_0000_0000_0000
        mask_power_4b = 0b_0000_0000_0000_0000_0001_1111_0000_0000_0000_0000_0000_0000_0000_0000_0000
        mask_power_4a = 0b_0000_0000_0000_0011_1110_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000

        # message=int(message)
        #message = int.from_bytes(message, "big")
        tempe_ic = (message & mask_tempe_ic)
        power_1b = (message & mask_power_1b) >> 6
        power_1a = (message & mask_power_1a) >> (6 + 5)
        power_2b = (message & mask_power_2b) >> (6 + 5 + 5)
        power_2a = (message & mask_power_2a) >> (6 + 5 + 5 + 5)
        power_3b = (message & mask_power_3b) >> (6 + 5 + 5 + 5 + 5)
        power_3a = (message & mask_power_3a) >> (6 + 5 + 5 + 5 + 5 + 5)
        power_4b = (message & mask_power_4b) >> (6 + 5 + 5 + 5 + 5 + 5 + 5)
        power_4a = (message & mask_power_4a) >> (6 + 5 + 5 + 5 + 5 + 5 + 5 + 5)
        # y=ax+b =>>>> x=(b-y)/a
        # a=0.31 b=47.37
        #tempe_ic = (47.37 - tempe_ic) / 0.31
        print('TX Telemetry Data:')
        print('Temp IC:', tempe_ic)
        print('Power 1A:', power_1a)
        print('Power 1B:', power_1b)
        print('Power 2A:', power_2a)
        print('Power 2B:', power_2b)
        print('Power 3A:', power_3a)
        print('Power 3B:', power_3b)
        print('Power 4A:', power_4a)
        print('Power 4B:', power_4b)
        return tempe_ic, power_1a, power_1b, power_2a, power_2b, power_3a, power_3b, power_4a, power_4b

    @staticmethod
    def set_channel_on_off(RE1a_en=0, RE1b_en=0, RE2a_en=0, RE2b_en=0, RE3a_en=0, RE3b_en=0, RE4a_en=0,
                           RE4b_en=0):
        """
                        Set the channels of the beam former OFF or ON
                         Write at register BW0 (0b_0000_0000_0000_0001) at positions 34-41 (8 bits)
                        :param channel: Select any of the defined common channel values (ELEMENT_*)
                        :param on_off_ind: 0 for OFF, 1 for ON
        """
        # Register BW0
        BW0b = 0b_0000_0000_0001_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000
        # Activation Mask
        on_off_bin = 0b11111111
        # amp_number: 0 to 1
        on_off_bin = on_off_bin ^ RE1a_en
        on_off_bin = on_off_bin ^ RE1b_en << 1
        on_off_bin = on_off_bin ^ RE2a_en << 2  # RE1 is connected with RF_2A
        on_off_bin = on_off_bin ^ RE2b_en << 3
        on_off_bin = on_off_bin ^ RE3a_en << 4  # RE1 is connected with RF_2A
        on_off_bin = on_off_bin ^ RE3b_en << 5
        on_off_bin = on_off_bin ^ RE4a_en << 6
        on_off_bin = on_off_bin ^ RE4b_en << 7

        # Shift the Mask 34 bits
        packet = BW0b | on_off_bin << 34
        print('**************************')
        print('BB Activate Elements')
        print('Bin Packet send:', bin(packet))
        print('Hex Packet send:', hex(packet))
        telemetry = AwmfCommander.Anokiewave_write(RX_MODE, [packet])
        print('Return:', telemetry)
        print('**************************')
        return telemetry

    @staticmethod
    def set_channel_attenuation(channel, amp_number):
        """
                        Set Arm Attenuation attenuation  of the BF = 0.5dB * rf_gain
                        :param amp_number: int from 0 to 15
                         Write at register BW0 (0b_0000_0000_0000_0001) at positions 0-31 (4 bits)
                        :param channel: Select any of the defined common channel values (ELEMENT_*)
        """
        # Register BW0
        BW0b = 0b_0000_0000_0001_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000
        # amp_number: 0 to 15
        if 15 >= amp_number >= 0:
            if channel == ELEMENT_1_a:
                packet = amp_number | BW0b
            elif channel == ELEMENT_1_b:
                packet = (amp_number << 4) | BW0b
            elif channel == ELEMENT_2_a:
                packet = (amp_number << 8) | BW0b
            elif channel == ELEMENT_2_b:
                packet = (amp_number << 12) | BW0b
            elif channel == ELEMENT_3_a:
                packet = (amp_number << 16) | BW0b
            elif channel == ELEMENT_3_b:
                packet = (amp_number << 20) | BW0b
            elif channel == ELEMENT_4_a:
                packet = (amp_number << 24) | BW0b
            elif channel == ELEMENT_4_b:
                packet = (amp_number << 28) | BW0b
            print('**************************')
            print('Set Channel Attenuation')
            print('Bin Packet send:', bin(packet))
            print('Hex Packet send:', hex(packet))
            telemetry = AwmfCommander.Anokiewave_write(RX_MODE, [packet])
            print('Return:', telemetry)
            print('**************************')
            return telemetry
        else:
            raise ValueError("Incorrect Amp Number value")

    @staticmethod
    def __packValues(vals, in_width=8, packed_size=10, big_endian=True):
        """
        takes a list of values (integers) and packs them as densely
        as possible into a  array of bits where each element is
        packed_size bits long

        assumes each element in vals is *in_width* bits wide
        """
        byteArray = []
        cB = 0
        cBi = 0

        for val in vals:
            # for each meaningful bit in the current value
            for i in range(in_width):
                # set the next bit in the current working byte
                # whether or not the next bit in val is set
                #      |                   index of cB to set
                cB |= ((val & (1 << i)) >> i) << cBi
                cBi += 1

                if (cBi >= packed_size):
                    byteArray.append(cB)
                    cBi = 0
                    cB = 0

        # append the remaining bits if there are any
        if (cBi != 0):
            byteArray.append(cB)

        if big_endian:
            byteArray.reverse()

        return byteArray

    @staticmethod
    def set_comm_attenuation(att_value):
        """
                        Set Common Arm Attenuation attenuation  of the BF = 8dB * com_att
                        00 = 0dB
                        01 = 8dB
                        Write at register BW0 (0b_0000_0000_0000_0001) at positions 32-33 (2 bits)
                        :param bb_id: Select any of the defined common beamformer ID values (BEAMFORMER_*)
                        :param att_value: Select any of the defined common att values (COMM_ATT_*)
        """

        if not (att_value == 0b00 or att_value == 0b01):
            raise ValueError("Incorrect common attenuation value")
        BW0b = 0b_0000_0000_0000_0001_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000
        # Register Name: BW0
        packet = BW0b | att_value << 32
        print('**************************')
        print('Sett Common Attenuation')
        print('Bin Packet send:', bin(packet))
        print('Hex Packet send:', hex(packet))
        telemetry = AwmfCommander.Anokiewave_write(RX_MODE, [packet])
        print('Return:', telemetry)
        print('**************************')
        return telemetry

    @staticmethod
    def set_channel_phase(channel, phase_number):
        """
                Set Arm Phase of the PH = 5.625 deg * phase
                :param phase_number: int from 0 to 63
                Write at register BW1 (0b_0000_0000_0000_0010) at positions 0-47 (6 bits)
                :param channel: Select any of the defined common channel values (ELEMENT_*)
        """
        # Register BW1
        BW1b = 0b_0000_0000_0000_0010_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000
        # amp_number: 0 to 15
        if 63 >= phase_number >= 0:
            if channel == ELEMENT_1_a:
                packet = phase_number | BW1b
            elif channel == ELEMENT_1_b:
                packet = (phase_number << 6) | BW1b
            elif channel == ELEMENT_2_a:
                packet = (phase_number << 12) | BW1b
            elif channel == ELEMENT_2_b:
                packet = (phase_number << 18) | BW1b
            elif channel == ELEMENT_3_a:
                packet = (phase_number << 24) | BW1b
            elif channel == ELEMENT_3_b:
                packet = (phase_number << 30) | BW1b
            elif channel == ELEMENT_4_a:
                packet = (phase_number << 36) | BW1b
            elif channel == ELEMENT_4_b:
                packet = (phase_number << 42) | BW1b
            print('**************************')
            print('Set Channel Phase')
            print('Bin Packet send:', bin(packet))
            print('Hex Packet send:', hex(packet))
            telemetry = AwmfCommander.Anokiewave_write(RX_MODE, [packet])
            print('Return:', telemetry)
            print('**************************')
            return telemetry

    @staticmethod
    def init_BF(MODE):
        print('**************************')
        print('Set Channel Phase')
        print('**************************')
        if MODE == RX_MODE:
            AWMF_0132_INIT0 = 0x_0_00_00_00_01_02_04_00
            AWMF_0132_INIT1 = 0x_0_00_00_00_00_02_04_00
            AWMF_0132_INIT2 = 0x_0_01_00_00_00_00_00_00
            AWMF_0132_INIT3 = 0x_0_02_00_00_00_00_00_00
            AWMF_0132_INIT4 = 0x_0_03_00_00_00_00_00_00
            AWMF_0132_INIT5 = 0x_0_04_00_00_00_00_00_00
            AWMF_0132_INIT6 = 0x_0_05_00_29_4a_52_94_a5
            AWMF_0132_INIT7 = 0x_0_06_00_00_00_00_01_e7
            AWMF_0132_INIT8 = 0x_0_07_00_00_00_00_00_00
            AWMF_0132_INIT9 = 0x_0_08_00_03_9b_ce_01_fe
            AWMF_0132_INIT10 = 0x_0_09_00_00_06_01_b6_f6
            AWMF_0132_INIT11 = 0x_0_0a_00_00_6d_b6_db_41
            AWMF_0132_INIT12 = 0x_0_0b_00_00_01_20_01_0a
            AWMF_0132_INIT13 = 0x_0_0c_00_00_00_09_00_01
            AWMF_0132_INIT14 = 0x_0_0d_00_00_00_00_08_00
            AWMF_0132_INIT15 = 0x_0_0e_00_00_00_00_00_00
            AWMF_0132_INIT16 = 0x_0_0f_00_00_00_00_00_00
            AWMF_0132_INIT17 = 0x_0_10_00_00_00_00_00_00
            AWMF_0132_INIT18 = 0x_0_11_00_00_00_00_00_00

            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT0])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT1])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT2])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT3])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT4])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT5])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT6])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT7])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT8])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT9])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT10])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT11])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT12])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT13])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT14])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT15])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT16])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT17])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0132_INIT18])

        if MODE == TX_MODE:
            # TX
            AWMF_0133_INIT0 = 0x_0_00_00_00_01_02_04_00
            AWMF_0133_INIT1 = 0x_0_00_00_00_00_02_04_00
            AWMF_0133_INIT2 = 0x_0_01_00_00_00_00_00_00
            AWMF_0133_INIT3 = 0x_0_02_00_00_00_00_00_00
            AWMF_0133_INIT4 = 0x_0_03_00_00_00_00_00_00
            AWMF_0133_INIT5 = 0x_0_04_00_00_00_00_00_00
            AWMF_0133_INIT6 = 0x_0_05_04_31_8c_63_18_c6
            AWMF_0133_INIT7 = 0x_0_06_00_00_00_00_01_60
            AWMF_0133_INIT8 = 0x_0_07_00_00_00_00_00_00
            AWMF_0133_INIT9 = 0x_0_08_00_03_bb_ff_ff_fe
            AWMF_0133_INIT10 = 0x_0_09_00_00_06_01_b6_f6
            AWMF_0133_INIT11 = 0x_0_0a_00_00_6d_b6_db_44
            AWMF_0133_INIT12 = 0x_0_0b_00_00_00_00_00_02
            AWMF_0133_INIT13 = 0x_0_0c_00_00_03_69_14_01
            AWMF_0133_INIT14 = 0x_0_0d_00_00_00_00_08_00
            AWMF_0133_INIT15 = 0x_0_0e_00_00_00_00_00_00
            AWMF_0133_INIT16 = 0x_0_0f_00_00_00_00_00_00
            AWMF_0133_INIT17 = 0x_0_10_00_00_00_00_00_00
            AWMF_0133_INIT18 = 0x_0_11_00_00_00_00_00_00

            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT0])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT1])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT2])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT3])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT4])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT5])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT6])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT7])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT8])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT9])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT10])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT11])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT12])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT13])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT14])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT15])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT16])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT17])
            AwmfCommander.Anokiewave_write(INIT_MODE, [AWMF_0133_INIT18])

    @staticmethod
    def version_test():
        """
                        Set the two channels of the beam former OFF or ON
                        :param RE2_on_off: Radiated Element 1 1=ON, 0=OFF
                        :param RE1_on_off: Radiated Element 2 1=ON, 0=OFF
        """

        # change the mode to read the version of the IC
        packet = 0x_0_00_00_00_00_03_c4_00
        telemetry = AwmfCommander.Anokiewave_write(RX_MODE, [packet])

        packet = 0x_0_3D_00_00_00_00_00_3E
        print('**************************')
        print('Bin Packet send:', bin(packet))
        print('Hex Packet send:', hex(packet))
        version = AwmfCommander.Anokiewave_write(RX_MODE, [packet])
        version = AwmfCommander.Anokiewave_write(RX_MODE, [packet])
        print('Return:', version)
        return version

    @staticmethod
    def set_channel_all_on():
        """
                        Set all the channels of the beamformer OFF
                        Write at register BW0 (0b_0000_0000_0000_0001) at position 34-41 (8 bits)
        """
        # Register BW0
        BW0b = 0b_0000_0000_0000_0001_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000
        on_off_bin = 0b00000000
        packet = BW0b | on_off_bin << 34
        print('Activate All Elements')
        print('Bin Packet send:', bin(packet))
        print('Hex Packet send:', hex(packet))
        telemetry = AwmfCommander.Anokiewave_write(RX_MODE, [packet])
        print('Return:', telemetry)
        return telemetry

    @staticmethod
    def reset_beamformer():
        # Register BW0
        MODEb = 0b_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000
        reset_bin = 0b1
        packet = MODEb | reset_bin << 24
        print('Reset_Beamformer')
        print('Bin Packet send:', bin(packet))
        print('Hex Packet send:', hex(packet))
        AwmfCommander.Anokiewave_write(RX_MODE, [packet])
        reset_bin = 0b0
        packet = MODEb | reset_bin << 24
        telemetry = AwmfCommander.Anokiewave_write(RX_MODE, [packet])


    @staticmethod
    def rf_en_beamformer():
        # Register BW0
        MODEb = 0b_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000
        rf_en_bin = 0b1
        packet = MODEb | rf_en_bin << 23
        print('**************************')
        print('RF enable_Beamformer')
        print('Bin Packet send:', bin(packet))
        print('Hex Packet send:', hex(packet))
        telemetry = AwmfCommander.Anokiewave_write(RX_MODE, [packet])

    @staticmethod
    def set_channel_all_off():
        """
                        Set all the channels of the beamformer OFF
                        Write at register BW0 (0b_0000_0000_0000_0001) at positions 34-41 (8 bits)
        """
        # Register BW0
        BW0b = 0b_0000_0000_0000_0001_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000_0000
        on_off_bin = 0b11111111
        packet = BW0b | on_off_bin << 34
        print('**************************')
        print('Deactivate All Elements')
        print('Bin Packet send:', bin(packet))
        print('Hex Packet send:', hex(packet))
        telemetry = AwmfCommander.Anokiewave_write(RX_MODE, [packet])
        print('Return:', telemetry)
        return telemetry


def main():

        print("**Interactive setBeam test. Get out an o'scope")
        AwmfCommander.initSpi()
        print("Init BW")
        AwmfCommander.init_BF(RX_MODE)

        #telemetry = AwmfCommander.version_test()
        telemetry = AwmfCommander.set_channel_on_off(RE1a_en=1, RE1b_en=1, RE2a_en=1, RE2b_en=1, RE3a_en=1, RE3b_en=1,
                                                     RE4a_en=1, RE4b_en=1)

        AwmfCommander.set_comm_attenuation(COMM_ATT_8dB)

        bit_steam = [0, 0, 0, 0, 0, 23]
        AwmfCommander.decode_telemetry(bit_steam)

        channel = ELEMENT_1_a
        amp_number = 2  # from 0 to 15
        phase_number = 23  # from 0 to 63
        #AwmfCommander.set_channel_attenuation(channel, amp_number)
        #AwmfCommander.set_channel_phase(channel, phase_number)

        # AwmfCommander.closeSPI()


if __name__ == '__main__':
    main()
