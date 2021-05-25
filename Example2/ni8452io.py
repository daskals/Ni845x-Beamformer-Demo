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



#-------------------------------------------------------------------------------
# SPI Class: Hardware notes
#
#-------------------------------------------------------------------------------
import ctypes as c
import sys

class SPI(object):
    def __init__(self):

        # Version info
        self.__version = '2.00.01'
        self.__versDate = '24-05-21'
        self.__versStatus = 'Released'

        # cType parameters

        #For whatever reason, when using python3, it uses 64 bit pointers
        # but for python2, these functions use 32 bit pointers. (on my comp at least)
        # adjust accordingly
        if sys.version_info[0] == 3:
            self._cHdl      = c.c_ulonglong()
            self._cHdlScr   = c.c_ulonglong()
        else:
            self._cHdl      = c.c_ulong()
            self._cHdlScr   = c.c_ulong()
        self._cDevStr   = c.create_string_buffer(255)
        self._cNdev     = c.c_uint32(0)
        self._cIOdataIn = c.c_uint8()

        # Config parameters
        self.spiClk      = 1000      # SPI clkRate in kHz
        self.Vio         = 12        # VIO voltage as Vio*10
        self.delayLDB    = 10        # LDB delay (-ve width) in us
        self.delayCS2LDB = 2         # Delay between CS HIGH and LDB
        self._gpioDir    = 31        # GPIO configuration

        # Status
        self.status   = 0
        self.errMsg   = ''
        self.cErrMsg  = c.create_string_buffer(1024)

        # VISA address (for external access)
        self.visaAddr = 'SIM'


        # CONSTANTS
        self.__IOPORT = c.c_uint8(0)    # Port# for GPIO on 8452

        # Load Ni8452x.dll
        self._lspi = None
        try:
            fSpec = 'c:/windows/system32/Ni845x.dll'
            self._lspi = c.windll.LoadLibrary(fSpec)
        except:
            self.status = -1
            self.errMsg = 'Unable to load Ni845x.dll'


    # --------------------------------------------------------------------------
    # HELPER FUNCTIONS
    # --------------------------------------------------------------------------
    def __word2bytes(self, wordVal):
        '''Returns bytes array [b1, b0] from input word (uint16)'''
        b0=wordVal & 255
        b1=(wordVal>>8)&255
        return [b1,b0]

    def __bytes2word(self, byteList):
        '''Returns decimal word (uint16) based on [MSB,LSB] byteList'''
        return ((byteList[0]<<8)+byteList[1])

    def __errStatus(self, statusCode):
        '''Return error message based on NI8452 error code. Updates
        .status=errCode and .errMsg= NI8452 error string'''
        if self._lspi is None:
            return self.errMsg
        self._lspi.ni845xStatusToString(statusCode, c.c_uint32(1024), c.byref(self.cErrMsg))
        self.errMsg = self.cErrMsg.value
        self.status = statusCode
        return self.errMsg

    def ioGetVersion(self):
        '''Returns (version, versionDate, versionStatus) of class driver'''
        return self.__version, self.__versDate, self.__versStatus


    # --------------------------------------------------------------------------
    # IO CORE FUNCTIONS
    # --------------------------------------------------------------------------

    # --------------------------- ioOpen() -------------------------------------
    def ioOpen(self):
        '''Opens a session to NI-SPI.
        Creates handles to hardware and spiScript
        Returns 0 for success else error number: .errMsg contains error detail'''
        if self._lspi is None:
            self.status = -1
            return self.status
        fRet = self._lspi.ni845xFindDevice(c.byref(self._cDevStr),
                                           c.byref(self._cHdl), c.byref(self._cNdev))

        if fRet !=0:
            return fRet
        if self._cNdev.value < 1:
            self.errMsg = 'No devices found'
            self.status = -1
            return self.status

        # If fRet==0 then capture visaAddr
        self.visaAddr = self._cDevStr.value
        # Open and get handle
        fRet = self._lspi.ni845xOpen(self._cDevStr, c.byref(self._cHdl))
        if fRet !=0:
            #print(self.__errStatus(fRet))
            return fRet

        fRet = self._lspi.ni845xSpiScriptOpen(c.byref(self._cHdlScr))
        if fRet !=0:
            #print(self.__errStatus(fRet))
            return fRet
            # Set CS0 HIGH


        return fRet

    # --------------------------- ioOpenByName() -------------------------------------
    def ioOpenByName(self, ResourceName):
        '''Opens a session to NI-SPI with a specific VISA resource
        Creates handles to hardware and spiScript
        Returns 0 for success else error number: .errMsg contains error detail'''

        if self._lspi is None:
            return -1
        cResourceName = c.create_string_buffer(ResourceName)

        fRet = self._lspi.ni845xOpen(cResourceName, c.byref(self._cHdl))

        if fRet !=0:
            #print(self.__errStatus(fRet))
            return fRet

        # If success then capture visaAddr
        self.visaAddr = ResourceName

        fRet = self._lspi.ni845xSpiScriptOpen(c.byref(self._cHdlScr))
        if fRet !=0:
            #print(self.__errStatus(fRet))
            return fRet

        return fRet


    # --------------------------- ioConfig() -----------------------------------
    def ioSetConfig(self, Vio=12, spiClk=1000, gpioDir=31):
        '''Configures SPI parameters Vio*10 voltage level (for SPI and DIO), SPI Clk
        rate (kHz) and GPIO direction (0-all inputs, 255=all outputs).  Sets internal
        variables used by other functions, does not communicate directly with hardware'''
        self.spiClk = spiClk
        self.Vio = Vio
        self._gpioDir = gpioDir
        return 0


    # --------------------------- ioInit() -------------------------------------
    def ioInit(self):
        '''Initialize IO: Set Vio levels, initialize DIO
        '''
        # TODO
        fRet = 0

        # VIO levels
        if self._lspi is None:
            return -1
        intVio = int(self.Vio)
        fRet = self._lspi.ni845xSetIoVoltageLevel(self._cHdl, intVio)
        if fRet !=0:
            #print(self.__errStatus(fRet))
            return fRet
        # Set DIO mapping
        # D7  D6  D5  D4  D3  D2  D1  D0
        # CA  C1  C0  A2  A1  A0  RX  TX
        #  0   0   0   1   1   1   1   1 = 31

        fRet = self._lspi.ni845xDioSetPortLineDirectionMap(self._cHdl,
                                        self.__IOPORT, c.c_uint8(self._gpioDir))
        if fRet !=0:
            pass
            #print(self.__errStatus(fRet))
        return fRet


    # ------------------------------ ioSafe() ----------------------------------
    def ioSafe(self):
        '''Sets IO to safe state (0 V): disables SPI and sets all GPIO=0V
        Returns 0 for success, error coode otherwise'''

        if self._lspi is None:
            return -1
        # Set GPIO to 0V
        fRet = self._lspi.ni845xDioWritePort(self._cHdl, self.__IOPORT, c.c_uint8(0))
        if fRet!=0:
            #print(self.__errStatus(fRet))
            return fRet

        # Shut down SPI CS using SpiScript
        fRet = self._lspi.ni845xSpiScriptReset(self._cHdlScr)
        if fRet != 0:
            #print(self.__errStatus(fRet))
            return fRet
        fRet = self._lspi.ni845xSpiScriptDisableSPI(self._cHdlScr)
        if fRet != 0:
            #print(self.__errStatus(fRet))
            return fRet
        fRet = self._lspi.ni845xSpiScriptRun(self._cHdlScr, self._cHdl, self.__IOPORT)
        if fRet != 0:
            #print(self.__errStatus(fRet))
            return fRet

        return fRet


    # --------------------------- ioClose() --------------------------------
    def ioClose(self, shutDown=1):
        '''Closes SPI. shutDown!=0 sets all IO=0V'''
        # Shut down DIO and SPI if shutDown!=0
        if self._lspi is None:
            return -1
        if shutDown!=0:
            fRet = self.ioSafe()
            if fRet !=0:
                return fRet

        # Close handles cHdlScr & cHdl
        fRet = self._lspi.ni845xSpiScriptClose(self._cHdlScr)
        if fRet !=0:
            #print(self.__errStatus(fRet))
            return fRet
        fRet = self._lspi.ni845xClose(self._cHdl)
        if fRet !=0:
            pass
            #print(self.__errStatus(fRet))

        return fRet


    # --------------------------------------------------------------------------
    # IO READ/WRITE FUNCTIONS
    # --------------------------------------------------------------------------

    # --------------------------- ioWriteDIO() ---------------------------------
    def ioWriteDIO(self, dioData=0):
        '''Writes dioData value out of GPIO port.  Assume necessary masking
        has already been applied to dioData. Returns 0/err code'''
        if self._lspi is None:
            return -1

        fRet = self._lspi.ni845xDioWritePort(self._cHdl, self.__IOPORT, c.c_uint8(dioData))
        if fRet != 0:
            pass
            #print(self.__errStatus(fRet))
        return fRet


    # --------------------------- ioReadDIO() ---------------------------------
    def ioReadDIO(self):
        '''Returns DIO data value (uint8) returned from GPIO lines'''
        if self._lspi is None:
            return 0
        fRet = self._lspi.ni845xDioReadPort(self._cHdl, self.__IOPORT, c.byref(self._cIOdataIn))
        if fRet != 0:
            pass
            #print(self.__errStatus(fRet))

        rData = self._cIOdataIn.value
        return rData


    # --------------------------- ioWriteSPI() ---------------------------------
    def ioWriteSPI(self, wData):
        '''Write wData array of bytes over SPI using SPIscript
           Returns data read back over spi'''
        if self._lspi is None:
            return 0
        fRet = 0
        # Num of bytes to be transmitted
        Nbytes=len(wData)
        # USB-SPI has max 8bytes/64clks per write buffer
        # Hence group writes into Nmain blocks of 8 and one last
        # transaction of Ntail bytes
        [Nmain, Ntail] = divmod(Nbytes, 8)

        # Reset script
        fRet += self._lspi.ni845xSpiScriptReset(self._cHdlScr)
        # Enable SPI
        fRet += self._lspi.ni845xSpiScriptEnableSPI(self._cHdlScr)

        # Configure polarity and phase
        fRet += self._lspi.ni845xSpiScriptClockPolarityPhase(self._cHdlScr, 0, 0)
        # Configure clock rate
        fRet += self._lspi.ni845xSpiScriptClockRate(self._cHdlScr, self.spiClk)
        # Set CS0 HIGH
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(0))

        # Set LDB HIGH (DIO-0): portNum, lineNum, dir(1=op)
        fRet += self._lspi.ni845xSpiScriptDioConfigureLine(self._cHdlScr, self.__IOPORT, c.c_uint8(0), c.c_int32(1))

        fRet += self._lspi.ni845xSpiScriptDioWriteLine(self._cHdlScr, self.__IOPORT, c.c_uint8(0), c.c_int32(1) )

        # SET CS0 LOW
        fRet += self._lspi.ni845xSpiScriptCSLow(self._cHdlScr, c.c_uint32(0))

        # *** START WRITE LOOP ***
        idxRead= []                 # Array for read pointers

        c_IdxRead = c.c_uint32()    # ctype for read pointer
        cWdata = (c.c_uint8*8)()    # ctype for write data array

        if Nmain>0:
            # Set numSamples=64 clks (8 bytes)
            fRet = self._lspi.ni845xSpiScriptNumBitsPerSample(self._cHdlScr, c.c_uint16(64))

            for idx in range(Nmain):
                cWdata[0:8] = wData[idx*8:idx*8+8]
                fRet += self._lspi.ni845xSpiScriptWriteRead(self._cHdlScr, c.c_uint32(8), c.byref(cWdata), c.byref(c_IdxRead))
                idxRead.append(c_IdxRead.value)

        if Ntail>0:
            fRet += self._lspi.ni845xSpiScriptNumBitsPerSample(self._cHdlScr, c.c_uint16(Ntail*8))
            cWdata = (c.c_uint8*Ntail)()
            cWdata[0:Ntail] = wData[8*Nmain:8*Nmain+1+Ntail]
            fRet += self._lspi.ni845xSpiScriptWriteRead(self._cHdlScr, c.c_uint32(Ntail), c.byref(cWdata), c.byref(c_IdxRead))
            idxRead.append(c_IdxRead.value)

        # Set CS0 HIGH
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(0))

        # Set delay: 2us
        fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(2))

        # Set DIO LOW
        fRet += self._lspi.ni845xSpiScriptDioWriteLine(self._cHdlScr,self.__IOPORT, c.c_uint8(0), c.c_int32(0) )
        # Delay LDB us
        fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(self.delayLDB))
        # Set DIO-0 HIGH
        fRet += self._lspi.ni845xSpiScriptDioWriteLine(self._cHdlScr,self.__IOPORT, c.c_uint8(0), c.c_int32(1) )

        fRet += self._lspi.ni845xSpiScriptRun(self._cHdlScr, self._cHdl, 0)

        nRead = c.c_uint32()

        rData = []
        for pIdx in idxRead:
            #print( pIdx)
            fRet = self._lspi.ni845xSpiScriptExtractReadDataSize(self._cHdlScr, c.c_uint32(pIdx), c.byref(nRead))

            cRdata = (c.c_uint8 * nRead.value)()
            fRet = self._lspi.ni845xSpiScriptExtractReadData(self._cHdlScr,c.c_uint32(pIdx), c.byref(cRdata))

            rData += cRdata[0:nRead.value]

        return rData


    # --------------------------- ioWriteRSPI() --------------------------------
    def ioWriteRSPI(self, byteList):
        '''Writes data from byte list over SPI and readback. Returns:
            status, dataIn, bitCount'''
        if self._lspi is None:
            return 0, 0, 0
        # TODO: quick test use ioWriteSPI() and wrap.  However could implement
        # faster 'standard SPI call' in this space
        rData = self.ioWriteSPI(byteList)
        Nclks = len(rData) * 8
        return 0, rData, Nclks


    # --------------------------- ioWriteSPI2() --------------------------------
    def ioWriteSPI2(self, wData, wordSize=8):
        '''Write wData array over SPI in wordSize chunks using SPIscript
           Returns data read back over spi'''
        if self._lspi is None:
            return [], 0
        fRet = 0

        # Num of words to be transmitted
        Nwords=len(wData)
        # Set wFlag: if wordSize=4-8 bits then no need to manage word conversion
        if wordSize<4 or wordSize>16:
            return -1
        elif wordSize<9:
            wFlag=0
        else:
            wFlag=1

        # Reset script
        fRet += self._lspi.ni845xSpiScriptReset(self._cHdlScr)
        # Enable SPI
        fRet += self._lspi.ni845xSpiScriptEnableSPI(self._cHdlScr)

        # Configure polarity and phase
        fRet += self._lspi.ni845xSpiScriptClockPolarityPhase(self._cHdlScr, 0, 0)
        # Configure clock rate
        fRet += self._lspi.ni845xSpiScriptClockRate(self._cHdlScr, self.spiClk)
        # Set CS0 HIGH
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(0))
        # Set CS1 HIGH
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(1))

        # SET CS0 LOW
        fRet += self._lspi.ni845xSpiScriptCSLow(self._cHdlScr, c.c_uint32(0))

        # *** START WRITE LOOP ***
        idxRead= []                 # Array for read pointers
        c_IdxRead = c.c_uint32()    # ctype for read pointer

        fRet += self._lspi.ni845xSpiScriptNumBitsPerSample(self._cHdlScr, c.c_uint16(wordSize))

        if wFlag==1:
            # Transmit data as WORDS (2 bytes per write)
            cWdata = (c.c_uint8*2)()   # ctype for write data array
            cNumBytes = c.c_uint32(2)  # 2 bytes
            for idx in range(Nwords):
                cWdata[0:2] = self.__word2bytes(wData[idx])
                fRet += self._lspi.ni845xSpiScriptWriteRead(self._cHdlScr, cNumBytes, c.byref(cWdata), c.byref(c_IdxRead))
                idxRead.append(c_IdxRead.value)

        else:
            cNumBytes=c.c_uint32(1)
            for idx in range(Nwords):
                cWdata = c.c_uint8(wData[idx])
                fRet += self._lspi.ni845xSpiScriptWriteRead(self._cHdlScr, cNumBytes, c.byref(cWdata), c.byref(c_IdxRead))
                idxRead.append(c_IdxRead.value)


        # Set CS0 HIGH
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(0))

        # Set delay: 2us
        fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(self.delayCS2LDB))

        # Set CS1 LOW
        fRet += self._lspi.ni845xSpiScriptCSLow(self._cHdlScr, c.c_uint32(1))
        # Delay LDB us
        fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(self.delayLDB))
        # Set CS1 HIGH
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(1))

        # Run script
        fRet += self._lspi.ni845xSpiScriptRun(self._cHdlScr, self._cHdl, 0)

        nRead = c.c_uint32()

        rData = []
        for pIdx in idxRead:

            fRet += self._lspi.ni845xSpiScriptExtractReadDataSize(self._cHdlScr, c.c_uint32(pIdx), c.byref(nRead))

            cRdata = (c.c_uint8 * nRead.value)()
            fRet = self._lspi.ni845xSpiScriptExtractReadData(self._cHdlScr,c.c_uint32(pIdx), c.byref(cRdata))

            rData += cRdata[0:nRead.value]

        # Handle word translation if wFlag True
        if wFlag==1:
            wordArr = []
            for idx in range(Nwords):
                wordArr.append(self.__bytes2word(rData[2*idx:2*idx+2]))
        else:
            wordArr=rData

        return wordArr, fRet

    # --------------------------- ioWriteSPI4() --------------------------------
    def ioWriteSPI4(self, wData, wordSize=10):
            '''Write wData array over SPI in wordSize chunks using SPIscript
               Returns data read back over spi'''
            if self._lspi is None:
                return [], 0
            fRet = 0

            # Num of words to be transmitted
            Nwords = len(wData)
            # Set wFlag: if wordSize=4-8 bits then no need to manage word conversion
            if wordSize < 4 or wordSize > 16:
                return -1
            elif wordSize < 9:
                wFlag = 0
            else:
                wFlag = 1

            # Reset script
            fRet += self._lspi.ni845xSpiScriptReset(self._cHdlScr)
            # Enable SPI
            fRet += self._lspi.ni845xSpiScriptEnableSPI(self._cHdlScr)

            # Configure polarity and phase
            fRet += self._lspi.ni845xSpiScriptClockPolarityPhase(self._cHdlScr, 0, 0)
            # Configure clock rate
            fRet += self._lspi.ni845xSpiScriptClockRate(self._cHdlScr, self.spiClk)
            # Set CS0 HIGH
            fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(0))


            # SET CS0 LOW
            fRet += self._lspi.ni845xSpiScriptCSLow(self._cHdlScr, c.c_uint32(0))
            # Set delay: 10us
            fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(1))
            # SET CS0 HIGH
            fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(0))
            # Set delay: 10us
            fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(1))
            # SET CS0 LOW
            fRet += self._lspi.ni845xSpiScriptCSLow(self._cHdlScr, c.c_uint32(0))

            # *** START WRITE LOOP ***
            idxRead = []  # Array for read pointers
            c_IdxRead = c.c_uint32()  # ctype for read pointer

            fRet += self._lspi.ni845xSpiScriptNumBitsPerSample(self._cHdlScr, c.c_uint16(wordSize))

            if wFlag == 1:
                # Transmit data as WORDS (2 bytes per write)
                cWdata = (c.c_uint8 * 2)()  # ctype for write data array
                cNumBytes = c.c_uint32(2)  # 2 bytes
                for idx in range(Nwords):
                    cWdata[0:2] = self.__word2bytes(wData[idx])
                    fRet += self._lspi.ni845xSpiScriptWriteRead(self._cHdlScr, cNumBytes, c.byref(cWdata),
                                                                c.byref(c_IdxRead))
                    idxRead.append(c_IdxRead.value)

            else:
                cNumBytes = c.c_uint32(1)
                for idx in range(Nwords):
                    cWdata = c.c_uint8(wData[idx])
                    fRet += self._lspi.ni845xSpiScriptWriteRead(self._cHdlScr, cNumBytes, c.byref(cWdata),
                                                                c.byref(c_IdxRead))
                    idxRead.append(c_IdxRead.value)

            # Set CS0 HIGH
            fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(0))

            # Set delay: 2us
            fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(self.delayCS2LDB))

            # # Set CS1 LOW
            # fRet += self._lspi.ni845xSpiScriptCSLow(self._cHdlScr, c.c_uint32(1))
            # # Delay LDB us
            # fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(self.delayLDB))
            # # Set CS1 HIGH
            # fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(1))

            # Run script
            fRet += self._lspi.ni845xSpiScriptRun(self._cHdlScr, self._cHdl, 0)

            nRead = c.c_uint32()

            rData = []

            for pIdx in idxRead:
                fRet += self._lspi.ni845xSpiScriptExtractReadDataSize(self._cHdlScr, c.c_uint32(pIdx), c.byref(nRead))

                cRdata = (c.c_uint8 * nRead.value)()
                fRet = self._lspi.ni845xSpiScriptExtractReadData(self._cHdlScr, c.c_uint32(pIdx), c.byref(cRdata))

                rData += cRdata[0:nRead.value]


            # Handle word translation if wFlag True
            if wFlag == 1:
                wordArr = []
                for idx in range(Nwords):
                    wordArr.append(self.__bytes2word(rData[2 * idx:2 * idx + 2]))
            else:
                wordArr = rData

            return wordArr, fRet





    # --------------------------- ioWriteSPI3() --------------------------------
    def ioWriteSPI3(self, wData, wordSize=8):
        '''Write wData array over SPI in wordSize chunks using SPIscript
           Returns data read back over spi
           Uses ODIN A0 SPI protocol workaround'''
        if self._lspi is None:
            return -1
        fRet = 0

        iCSB = 0    # IO address for CSB (CS0)
        iLDB = 1    # IO address for LDB (CS1)
        iTRG = 7    # IO address for trigger (CS7)

        # PROTOCOL
        # LDB ---|                |----------
        #        |________________|
        #
        # CSB -----|         |--------|   |--
        #          |_________|        |--|
        #
        #
        # CS7 ------------------------|  |---
        #                             |--|


        # Num of words to be transmitted
        Nwords=len(wData)
        # Set wFlag: if wordSize=4-8 bits then no need to manage word conversion
        if wordSize<4 or wordSize>16:
            return -1
        elif wordSize<9:
            wFlag=0
        else:
            wFlag=1

        # Reset script
        fRet += self._lspi.ni845xSpiScriptReset(self._cHdlScr)
        # Enable SPI
        fRet += self._lspi.ni845xSpiScriptEnableSPI(self._cHdlScr)

        # Configure polarity and phase
        fRet += self._lspi.ni845xSpiScriptClockPolarityPhase(self._cHdlScr, 0, 0)
        # Configure clock rate
        fRet += self._lspi.ni845xSpiScriptClockRate(self._cHdlScr, self.spiClk)
        # Set CSB/CS0 HIGH
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(iCSB))
        # Set LDB/CS1 HIGH
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(iLDB))
        # Set TRG/CS7 HIGH
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(iTRG))

        # SET LDB/CS1 LOW
        fRet += self._lspi.ni845xSpiScriptCSLow(self._cHdlScr, c.c_uint32(iLDB))
        fRet += self._lspi.ni845xSpiScriptCSLow(self._cHdlScr, c.c_uint32(iTRG))
        # Wait one click
        fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(1))
        # SET CSB/CS0 LOW
        fRet += self._lspi.ni845xSpiScriptCSLow(self._cHdlScr, c.c_uint32(iCSB))


        # *** START WRITE LOOP ***
        idxRead= []                 # Array for read pointers
        c_IdxRead = c.c_uint32()    # ctype for read pointer

        fRet += self._lspi.ni845xSpiScriptNumBitsPerSample(self._cHdlScr, c.c_uint16(wordSize))

        if wFlag==1:
            # Transmit data as WORDS (2 bytes per write)
            cWdata = (c.c_uint8*2)()   # ctype for write data array
            cNumBytes = c.c_uint32(2)  # 2 bytes
            for idx in range(Nwords):
                cWdata[0:2] = self.__word2bytes(wData[idx])
                fRet += self._lspi.ni845xSpiScriptWriteRead(self._cHdlScr, cNumBytes, c.byref(cWdata), c.byref(c_IdxRead))
                idxRead.append(c_IdxRead.value)

        else:
            cNumBytes=c.c_uint32(1)
            for idx in range(Nwords):
                cWdata = c.c_uint8(wData[idx])
                fRet += self._lspi.ni845xSpiScriptWriteRead(self._cHdlScr, cNumBytes, c.byref(cWdata), c.byref(c_IdxRead))
                idxRead.append(c_IdxRead.value)


        # Set CSB/CS0 HIGH
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(iCSB))
        # Wait 1us
        fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(1))
        # Set LDB/CS1 HIGH
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(iLDB))
        # Wait 1us
        fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(1))
        # Set CSB/CS0 LOW
        fRet += self._lspi.ni845xSpiScriptCSLow(self._cHdlScr, c.c_uint32(iCSB))
        # Wait 1us
        fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(1))
        # Set CSB/CS0 & TRG HIGH
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(iCSB))
        fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(iTRG))
        # Wait 1us
        fRet += self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(1))
##        # Set TRG/CS7 LOW
##        fRet += self._lspi.ni845xSpiScriptCSLow(self._cHdlScr, c.c_uint32(iTRG))

        # --- Run script ---
        fRet += self._lspi.ni845xSpiScriptRun(self._cHdlScr, self._cHdl, 0)

        nRead = c.c_uint32()

        rData = []
        for pIdx in idxRead:

            fRet += self._lspi.ni845xSpiScriptExtractReadDataSize(self._cHdlScr, c.c_uint32(pIdx), c.byref(nRead))

            cRdata = (c.c_uint8 * nRead.value)()
            fRet = self._lspi.ni845xSpiScriptExtractReadData(self._cHdlScr,c.c_uint32(pIdx), c.byref(cRdata))

            rData += cRdata[0:nRead.value]

        # Handle word translation if wFlag True
        if wFlag==1:
            wordArr = []
            for idx in range(Nwords):
                wordArr.append(self.__bytes2word(rData[2*idx:2*idx+2]))
        else:
            wordArr=rData

        return wordArr

    # --------------------------- ioReadSPI2() ---------------------------------
    def ioReadSPI2(self, nWords=18, wordSize=12):
            '''Readback SPI data using AKW protocol.  Sets up necessary parameters using
            nWords (no. of registers) and the wordSize.  Clocks out nWordsxwordSize 0's
            and readback data into nWords registers of wordSize. Note LDB is not strobed
            so no data written to device
            Returns list of register values'''
            if self._lspi is None:
                return []
            fRet = 0

            # Generate wData: [ 0,0,0,...0  ]: just clock through 0's
            wData   = [(0) for idx in range(nWords)]

            # Num of words to be transmitted
            Nwords = nWords
            # Set wFlag: if wordSize=4-8 bits then no need to manage word conversion
            if wordSize<4 or wordSize>16:
                return -1
            elif wordSize<9:
                wFlag=0
            else:
                wFlag=1

            # Reset script
            fRet += self._lspi.ni845xSpiScriptReset(self._cHdlScr)
            # Enable SPI
            fRet += self._lspi.ni845xSpiScriptEnableSPI(self._cHdlScr)

            # Configure polarity and phase
            fRet += self._lspi.ni845xSpiScriptClockPolarityPhase(self._cHdlScr, 0, 0)
            # Configure clock rate
            fRet += self._lspi.ni845xSpiScriptClockRate(self._cHdlScr, self.spiClk)
            # Set CS0 HIGH
            fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(0))
            # Set CS1 HIGH
            fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(1))

            # SET CS0 LOW
            fRet += self._lspi.ni845xSpiScriptCSLow(self._cHdlScr, c.c_uint32(0))

            # *** START WRITE LOOP ***
            idxRead= []                 # Array for read pointers
            c_IdxRead = c.c_uint32()    # ctype for read pointer

            fRet += self._lspi.ni845xSpiScriptNumBitsPerSample(self._cHdlScr, c.c_uint16(wordSize))

            if wFlag==1:
                # Transmit data as WORDS (2 bytes per write)
                cWdata = (c.c_uint8*2)()   # ctype for write data array
                cNumBytes = c.c_uint32(2)  # 2 bytes
                for idx in range(Nwords):
                    cWdata[0:2] = self.__word2bytes(wData[idx])
                    fRet += self._lspi.ni845xSpiScriptWriteRead(self._cHdlScr, cNumBytes, c.byref(cWdata), c.byref(c_IdxRead))
                    idxRead.append(c_IdxRead.value)

            else:
                cNumBytes=c.c_uint32(1)
                for idx in range(Nwords):
                    cWdata = c.c_uint8(wData[idx])
                    fRet += self._lspi.ni845xSpiScriptWriteRead(self._cHdlScr, cNumBytes, c.byref(cWdata), c.byref(c_IdxRead))
                    idxRead.append(c_IdxRead.value)


            # Set CS0 HIGH
            fRet += self._lspi.ni845xSpiScriptCSHigh(self._cHdlScr, c.c_uint32(0))


            # Run script
            fRet += self._lspi.ni845xSpiScriptRun(self._cHdlScr, self._cHdl, 0)

            nRead = c.c_uint32()

            rData = []
            for pIdx in idxRead:

                fRet += self._lspi.ni845xSpiScriptExtractReadDataSize(self._cHdlScr, c.c_uint32(pIdx), c.byref(nRead))

                cRdata = (c.c_uint8 * nRead.value)()
                fRet = self._lspi.ni845xSpiScriptExtractReadData(self._cHdlScr,c.c_uint32(pIdx), c.byref(cRdata))

                rData += cRdata[0:nRead.value]

            # Handle word translation if wFlag True
            if wFlag==1:
                wordArr = []
                for idx in range(Nwords):
                    wordArr.append(self.__bytes2word(rData[2*idx:2*idx+2]))
            else:
                wordArr=rData

            return wordArr



    # --------------------------------------------------------------------------
    def ioWriteFBSmerc(self, addr=0, fbsLine=4):
        '''FBS selection on Mercury awmf-0123/0125
        addr:     FBS addres (3 clocks) 0-7
        fbsLine:  DIO line for FBS address (DIO=0-7)
        '''
        if self._lspi is None:
            return []
        f = []

        # Number of clks
        if addr<4:
            Nclks = addr+8
        else:
            Nclks = addr

        print( Nclks)

        # Reset script
        f.append(self._lspi.ni845xSpiScriptReset(self._cHdlScr))
        # Enable SPI
        f.append(self._lspi.ni845xSpiScriptEnableSPI(self._cHdlScr))

        # Configure polarity and phase
        f.append(self._lspi.ni845xSpiScriptClockPolarityPhase(self._cHdlScr, 0, 0))
        # Configure clock rate
        f.append(self._lspi.ni845xSpiScriptClockRate(self._cHdlScr, self.spiClk))
        # Set DIO Dx FBSen line HIGH
        f.append(self._lspi.ni845xSpiScriptDioWriteLine(self._cHdlScr, c.c_uint8(0), c.c_uint8(fbsLine), c.c_int32(1)))
        # Wait
        f.append(self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(1)))
        # Set chunk size
        f.append(self._lspi.ni845xSpiScriptNumBitsPerSample(self._cHdlScr, c.c_uint16(Nclks)))
        c_IdxRead = c.c_uint32()
        if Nclks>8:
            cWdata = (c.c_uint8*2)()
            cWdata[0:2] = self.__word2bytes(0)
            cNumBytes = c.c_uint32(2)
        else:
            cWdata = c.c_uint8(0)
            cNumBytes = c.c_uint32(1)

        # Clock out data
        f.append(self._lspi.ni845xSpiScriptWriteRead(self._cHdlScr, cNumBytes, c.byref(cWdata), c.byref(c_IdxRead)))


        # Wait
        f.append(self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(1)))
        # Set DIO Dx FBSen line LOW
        f.append(self._lspi.ni845xSpiScriptDioWriteLine(self._cHdlScr, c.c_uint8(0), c.c_uint8(fbsLine), c.c_int32(0)))


        # Run script
        f.append(self._lspi.ni845xSpiScriptRun(self._cHdlScr, self._cHdl, 0))

        return f


    # --------------------------------------------------------------------------
    def ioWritePulse(self, nPulses=1, pWidth=1, dioLine=0):
        '''Pulses a dioLine using the spiScript engine
        Pulsewidth is min 15 us. pWidth is excess width
        Fixed ~15us between pulses
        nPulses:    # pulses 1-
        pWidth:     excess pulsewidth in us (int)
        dioLine:    dioLine to pulse 0-7
        Return:
            0=success'''
        if self._lspi is None:
            return []

        f = []

        # Reset script
        f.append(self._lspi.ni845xSpiScriptReset(self._cHdlScr))
        # Enable SPI
        f.append(self._lspi.ni845xSpiScriptEnableSPI(self._cHdlScr))

        # Configure polarity and phase
        f.append(self._lspi.ni845xSpiScriptClockPolarityPhase(self._cHdlScr, 0, 0))
        # Configure clock rate
        f.append(self._lspi.ni845xSpiScriptClockRate(self._cHdlScr, self.spiClk))
        for nP in range(nPulses):
            # Set DIO Dx FBSen line HIGH
            f.append(self._lspi.ni845xSpiScriptDioWriteLine(self._cHdlScr, c.c_uint8(0), c.c_uint8(dioLine), c.c_int32(1)))
            # Wait
            f.append(self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(pWidth)))
            # Set DIO Dx FBSen line LOW
            f.append(self._lspi.ni845xSpiScriptDioWriteLine(self._cHdlScr, c.c_uint8(0), c.c_uint8(dioLine), c.c_int32(0)))
            # Wait
            f.append(self._lspi.ni845xSpiScriptUsDelay(self._cHdlScr, c.c_uint8(1)))

        # Run script
        f.append(self._lspi.ni845xSpiScriptRun(self._cHdlScr, self._cHdl, 0))

        return sum(f)


# ------------------------------------------------------------------------------
# MAIN PROGRAM - TEST HARNESS
# ------------------------------------------------------------------------------
def main():

    print( '**********************************************')
    print( '***   Test Harness for NI8452io Class      ***')
    print( '**********************************************')

    spiLoopTest  = False
    gpioLoopTest = False
    spiLoopTest_10_bit=True

    # ==========================================================================
    # --- Initialization ---
    spi = SPI()
    print( 'Class version:\t', spi.ioGetVersion())

    fRet = spi.ioOpen()
    print( 'ioOpen():   \t{0}'.format(fRet))
    if fRet!=0:
        exit(0)

    fRet = spi.ioSetConfig(spiClk=1000)
    print( 'ioSetConfig():\t{0}'.format(fRet))
    if fRet!=0:
        exit(0)

    fRet= spi.ioInit()
    print( 'ioInit():     \t{0}\n'.format(fRet))
    if fRet!=0:
        exit(0)


    # ==========================================================================
    # --- Standard SPI write LOOP TEST ----
    if spiLoopTest:
        print( '*** SPI LOOP TEST ***')
        for p in range(230):
            wArr=range(p,p+27)
            rData = spi.ioWriteSPI(wArr)
            if wArr != rData:
                print( 'MOSI/MISO Error @ {0}'.format(p))
                print( rData)
        print( '***    COMPLETE   ***\n')

    # ==========================================================================
    # --- 5-WIRE SPI LOOP TEST: 4 BIT WORD ----
    if spiLoopTest:
        print( '*** SPI2 LOOP TEST: 4bit word ***')
        for p in range(10):
            wArr=range(p,p+7)
            rData = spi.ioWriteSPI2(wArr, 4)
            if wArr != rData:
                print( 'MOSI/MISO Error @ {0}'.format(p))
                print( rData)
        print( 'Last iter:\t', rData)
        print( '***         COMPLETE            ***\n')

    # ==========================================================================
    # --- 5-WIRE SPI LOOP TEST: 8 BIT WORD ----
    if spiLoopTest:
        print( '*** SPI2 LOOP TEST: 8bit word ***')
        for p in range(247):
            wArr=range(p,p+10)
            rData = spi.ioWriteSPI2(wArr, 8)
            if wArr != rData:
                print( 'MOSI/MISO Error @ {0}'.format(p))
                print( rData)
        print( 'Last iter:\t', rData)
        print( '***         COMPLETE            ***\n')

    # ==========================================================================
    # --- 5-WIRE SPI LOOP TEST: 10 BIT WORD ----
    if spiLoopTest_10_bit:
        print( '*** SPI2 LOOP TEST: 10bit word ***')
        for p in range(1015):
            wArr=range(p,p+10)
            rData = spi.ioWriteSPI2(wArr, 10)
            if wArr != rData:
                print( 'MOSI/MISO Error @ {0}'.format(p))
                print( rData)
        print( 'Last iter:\t', rData)
        print( '***         COMPLETE            ***\n')

    # ==========================================================================
    # --- 5-WIRE SPI LOOP TEST: 12 BIT WORD ----
    if spiLoopTest:
        print( '*** SPI2 LOOP TEST: 12bit word ***')
        for p in range(4079):
            wArr=range(p,p+18)
            rData = spi.ioWriteSPI2(wArr, 12)
            if wArr != rData:
                print( 'MOSI/MISO Error @ {0}'.format(p))
                print( rData)
        print( 'Last iter:\t', rData)
        print( '***         COMPLETE            ***\n')

    # ==========================================================================
    # --- DIO TEST: ATLAS EMULATION ----
    if gpioLoopTest:
        for idx in range(32):
            dVal=idx
            fRet = spi.ioWriteDIO(dVal)
            print( 'writeDIO\t{0}\t{1}'.format(fRet, hex(idx)))
            time.sleep(1)

    #fRet = spi.readDIO()
    #print( 'readDIO\t{0}'.format(fRet))


    # ==========================================================================
    # --- ioReadSPI2() Test ---
    if False:
        print( 'ioReadSPI2() Test')
        fRet = spi.ioReadSPI2(18,12)
        print( fRet)

    # ==========================================================================
    if False:
        print( '*** ioWriteRSPI() Testing ***')
        fRet, rDataIn, Nclks = spi.ioWriteRSPI([0x55,0xaa,0x55])
        print( rDataIn)


    # ==========================================================================
    if False:
        print( '*** Test Mercury FBS Pulsing ***')
        spi.ioSetConfig(Vio=12, spiClk=1000)
        spi.ioInit()
        f = spi.ioWriteFBSmerc(7,4)
        print( f)




    # ==========================================================================
    # --- Set IO safe state ---
    fRet = spi.ioSafe()
    print( 'ioSafe():     \t{0}'.format(fRet))

    # --- Close IO ---
    fRet = spi.ioClose(0)
    print( 'ioClose():    \t{0}'.format(fRet))


if __name__ == '__main__':
    import time
    main()
