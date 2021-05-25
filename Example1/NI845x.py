#!/usr/bin/env python -*- coding: utf-8 -*-
import ctypes as c
import time
import numpy as np

DEV_SIZE = 256
MAX_SIZE = 1024
'''
SPI lib used 
'''


class NI8452Interface():
    """
    This class makes Python calls to the C DLL of NI USB 8452 (ni845x.dll)
    """

    def __init__(self):
        self.first_device = None
        self.find_device_handle = None
        self.number_found = None
        self.status_code = c.c_long()
        self.device_handle = c.c_ulonglong()
        self.script_handle= c.c_ulonglong()
        self.configuration_handle = c.c_ulonglong()

        # CONSTANTS
        self.__IOPORT = c.c_uint8(0)  # Port# for GPIO on 8452

        self._cIOdataIn = c.c_uint8()

        self.dll_location = "C:\\Windows\\System32\\Ni845x.dll"
        try:
            self.spi = c.cdll.LoadLibrary(self.dll_location)
        except Exception as e:
            print(e)

    def ni845xFindDevice(self):
        """
        Calls NI USB-8452 C API function ni845xFindDevice whose prototype is:
        int32 ni845xFindDevice (char * pFirstDevice, NiHandle * pFindDeviceHandle, uInt32 * pNumberFound);
        :return: name of first device
        """
        self.first_device = c.create_string_buffer(DEV_SIZE)
        self.find_device_handle = (c.c_ulong * 5)()
        c.cast(self.find_device_handle, c.POINTER(c.c_ulong))
        number_found = (c.c_ulong * 5)()
        c.cast(number_found, c.POINTER(c.c_ulong))

        self.status_code = self.spi.ni845xFindDevice(self.first_device, self.find_device_handle, number_found)
        print("returnValue ni845xFindDevice", self.status_code)
        # print("First Device Name:\n", repr(self.first_device.raw))
        print("First DeviceName:\n", str(self.first_device.value))
        # print("Number Found: ", number_found[0])
        self.number_found = number_found[0]
        return self.first_device

    def ni845xCloseFindDeviceHandle(self):
        """
        Calls NI USB-8452 C API function ni845xCloseFindDeviceHandle whose prototype is:
        int32 ni845xCloseFindDeviceHandle (NiHandle FindDeviceHandle);
        :return: None
        """

        self.status_code = self.spi.ni845xCloseFindDeviceHandle(self.find_device_handle)
        # print("returnValue", self.status_code)
        # print("Running StatusToString")
        returnValue = self.ni845xStatusToString(self.status_code)
        print("Return value of ni845xCloseFindDeviceHandle:", returnValue)

    def ni845xStatusToString(self, status_code):
        """
        Calls NI USB-8452 C API function ni845xStatusToString whose prototype is:
        void ni845xStatusToString (int32 StatusCode, uInt32 MaxSize, int8 * pStatusString);
        :return:None
        """
        if not status_code == 0:
            status_string = c.create_string_buffer(b'', MAX_SIZE)
            returnValue = self.spi.ni845xStatusToString(status_code, MAX_SIZE, status_string)
            # print("Status String:\n", repr(status_string.raw))
            str(status_string)
            print("state2string:", status_string.value)

    def ni845xOpen(self, resource_name):
        """
        Calls the NI USB-8452 C API function ni845xOpen whose prototype is:
        int32 ni845xOpen (char * pResourceName, NiHandle * pDeviceHandle);
        :param resource_name: name of the resource
        :return: device handle
        """
        # c.cast(self.device_handle, c.POINTER(c.c_ulong))

        returnValue = self.spi.ni845xOpen(resource_name, c.byref(self.device_handle))
        print("self.device_handle", self.device_handle)
        print("Return values of ni845xOpen: ", returnValue)
        # return self.device_handle

    def ni845xClose(self):
        """
        Calls the NI USB-8452 C API function ni845xClose whose prototype is
        int32 ni845xClose (NiHandle pDeviceHandle);
        :param: pDeviceHandle: Device handle to be closed.
        :return: None
        """
        print("self.device_handle.value", self.device_handle.value)
        returnValue = self.spi.ni845xClose(self.device_handle)
        print("Return values of ni845xClose: ", returnValue)
        self.ni845xStatusToString(returnValue)

    def ni845xSetIoVoltageLevel(self, VoltageLevel):
        """
        Calls the NI USB-8452 C API function ni845xSetIoVoltageLevel whose prototype is
        int32 ni845xSetIoVoltageLevel (NiHandle DeviceHandle,uInt8 VoltageLevel);
        :param: NiHandle DeviceHandle: Device handle returned from ni845xOpen.
                uInt8 VoltageLevel: The desired voltage level. VoltageLevel uses the following values:
                                    • kNi845x33Volts (33): The output I/O high level is 3.3 V.
                                    • kNi845x25Volts (25): The output I/O high level is 2.5 V.
                                    • kNi845x18Volts (18): The output I/O high level is 1.8 V.
                                    • kNi845x15Volts (15): The output I/O high level is 1.5 V.
                                    • kNi845x12Volts (12): The output I/O high level is 1.2 V.
                                    The default value of this property is 3.3 V.
        :return: None
        """
        cVoltageLevel = c.c_uint8(VoltageLevel)
        print("Setting Voltage Level to: ", cVoltageLevel)
        returnValue = self.spi.ni845xSetIoVoltageLevel(self.device_handle, cVoltageLevel)
        print("Return value of ni845xSetIoVoltageLevel: ", returnValue)
        self.ni845xStatusToString(returnValue)

    def ni845xSetTimeout(self, Timeout):
        """
        Calls the NI USB-8452 C API function ni845xSetTimeout whose prototype is
        int32 ni845xSetTimeout (NiHandle DeviceHandle, uInt32 Timeout);
        :param: NiHandle DeviceHandle: Device handle returned from ni845xOpen.
                uInt32 Timeout: The timeout value in milliseconds. The minimum timeout is 1000 ms (1 second).
                                • The default of this property is 30000 (30 seconds).
        :return: None
        """
        cTimeout = c.c_uint32(Timeout)
        print("Setting timeout to: ", cTimeout)
        returnValue = self.spi.ni845xSetTimeout(self.device_handle, cTimeout)
        print("Return value of ni845xSetTimeout: ", returnValue)
        self.ni845xStatusToString(returnValue)

    def ni845xSpiConfigurationClose(self):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationClose whose prototype is
        int32 ni845xSpiConfigurationClose (NiHandle ConfigurationHandle);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
        :return: None
        """
        print("Closing a configuration handle.")
        returnValue = self.spi.ni845xSpiConfigurationClose(self.configuration_handle)
        self.ni845xStatusToString(returnValue)

    def ni845xSpiConfigurationOpen(self):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationOpen whose prototype is
        int32 ni845xSpiConfigurationOpen (NiHandle * pConfigurationHandle);
        :param: None
        :return: configuration handle
        """
        print("Opening a configuration handle.")
        returnValue = self.spi.ni845xSpiConfigurationOpen(c.byref(self.configuration_handle))
        print("self.configuration_handle", self.configuration_handle)
        self.ni845xStatusToString(returnValue)

    def ni845xSpiConfigurationGetChipSelect(self):
        """
        Calls the NI USB-8452 C API function  whose prototype is
        int32 ni845xSpiConfigurationGetChipSelect (NiHandle ConfigurationHandle,uInt32 * pChipSelect);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
        :return: None
        """
        cChipSelect = c.c_uint32()
        returnValue = self.spi.ni845xSpiConfigurationGetChipSelect(self.configuration_handle, c.byref(cChipSelect))
        print("chip_select: ", cChipSelect)
        print("Return values of ni845xSpiConfigurationGetChipSelect: ", returnValue)
        self.ni845xStatusToString(returnValue)
        return cChipSelect

    def ni845xSpiConfigurationGetClockPhase(self):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationGetClockPhase whose prototype is
        int32 ni845xSpiConfigurationGetClockPhase (NiHandle ConfigurationHandle,int32 * pClockPhase);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
        :return: int32 * pClockPhase: A pointer to an integer to store the clock phase in. pClockPhase uses the followingvalues:
                                    • kNi845xSpiClockPhaseFirstEdge (0): Data is centered on the first edge of theclock period.
                                    • kNi845xSpiClockPhaseSecondEdge (1): Data is centered on the second edge ofthe clock period.
        """
        cClockPhase = c.c_uint32()
        returnValue = self.spi.ni845xSpiConfigurationGetClockPhase(self.configuration_handle, c.byref(cClockPhase))
        print("cClockPhase: ", cClockPhase)
        print("Return values of ni845xSpiConfigurationGetClockPhase: ", returnValue)
        self.ni845xStatusToString(returnValue)
        return cClockPhase

    def ni845xSpiConfigurationGetClockPolarity(self):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationGetClockPolarity whose prototype is
        int32 ni845xSpiConfigurationGetClockPolarity (NiHandle ConfigurationHandle,int32 * pClockPolarity);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
        :return: int32 * pClockPolarity: A pointer to an integer to store the clock polarity in. pClockPolarity uses thefollowing values:
                                        • kNi845xSpiClockPolarityIdleLow (0): Clock is low in the idle state.
                                        • kNi845xSpiClockPolarityIdleHigh (1): Clock is high in the idle state.
        """
        cClockPolarity = c.c_uint32()
        returnValue = self.spi.ni845xSpiConfigurationGetClockPolarity(self.configuration_handle,
                                                                      c.byref(cClockPolarity))
        print("cClockPolarity: ", cClockPolarity)
        print("Return values of ni845xSpiConfigurationGetClockPolarity: ", returnValue)
        self.ni845xStatusToString(returnValue)
        return cClockPolarity

    def ni845xSpiConfigurationGetClockRate(self):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationGetClockRate whose prototype is
        int32 ni845xSpiConfigurationGetClockRate (NiHandle ConfigurationHandle,uInt16 * pClockRate);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
        :return: uInt16 * pClockRate: A pointer to an unsigned 16-bit integer to store the clock rate in.
        """
        cClockRate = c.c_uint16()
        returnValue = self.spi.ni845xSpiConfigurationGetClockRate(self.configuration_handle, c.byref(cClockRate))
        print("cClockRate: ", cClockRate)
        print("Return values of ni845xSpiConfigurationGetClockRate: ", returnValue)
        self.ni845xStatusToString(returnValue)
        return cClockRate

    def ni845xSpiConfigurationGetNumBitsPerSample(self):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationGetNumBitsPerSample whose prototype is
        int32 ni845xSpiConfigurationGetNumBitsPerSample (NiHandle ConfigurationHandle,uInt16 * pNumBitsPerSample);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
        :return: uInt16 * pNumBitsPerSample: A pointer to an unsigned 16-bit integer to store the number of bits per sample in.
        """
        cNumBitsPerSample = c.c_uint16()
        returnValue = self.spi.ni845xSpiConfigurationGetNumBitsPerSample(self.configuration_handle,
                                                                         c.byref(cNumBitsPerSample))
        print("cNumBitsPerSample: ", cNumBitsPerSample)
        print("Return values of ni845xSpiConfigurationGetNumBitsPerSample: ", returnValue)
        self.ni845xStatusToString(returnValue)
        return cNumBitsPerSample

    def ni845xSpiConfigurationGetPort(self):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationGetPort whose prototype is
        int32 ni845xSpiConfigurationGetPort (NiHandle ConfigurationHandle,uInt8 * pPort);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
        :return: uInt8 * pPort: A pointer to an unsigned byte to store the port value in.
        """
        cPort = c.c_uint8()
        returnValue = self.spi.ni845xSpiConfigurationGetPort(self.configuration_handle, c.byref(cPort))
        print("cPort: ", cPort)
        print("Return values of ni845xSpiConfigurationGetPort: ", returnValue)
        self.ni845xStatusToString(returnValue)
        return cPort

    def ni845xSpiConfigurationSetChipSelect(self, ChipSelect):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationSetChipSelect whose prototype is
        int32 ni845xSpiConfigurationSetChipSelect (NiHandle ConfigurationHandle,uInt32 ChipSelect);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
                uInt32 ChipSelect: Selects the chip select line for this configuration.
                The default value for the chip select is 0.
        :return: None
        """
        cCipselect = c.c_uint32(ChipSelect)
        returnValue = self.spi.ni845xSpiConfigurationSetChipSelect(self.configuration_handle, cCipselect)
        print("cCipselect set to: ", cCipselect)
        print("Return values of ni845xSpiConfigurationSetChipSelect: ", returnValue)
        self.ni845xStatusToString(returnValue)

    def ni845xSpiConfigurationSetClockPhase(self, ClockPhase):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationSetClockPhase whose prototype is
        int32 ni845xSpiConfigurationSetClockPhase (NiHandle ConfigurationHandle,int32 ClockPhase);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
                int32 ClockPhase:Sets the positioning of the data bits relative to the clock edges for the SPI Port.
                    ClockPhase uses the following values:
                        • kNi845xSpiClockPhaseFirstEdge (0): Data is centered on the first edge of the clock period.
                        • kNi845xSpiClockPhaseSecondEdge (1): Data is centered on the second edge of the clock period.
                    The default value for this property is kNi845xSpiClockPhaseFirstEdge.
        :return: None
        """
        cClockPhase = c.c_uint32(ClockPhase)
        returnValue = self.spi.ni845xSpiConfigurationSetClockPhase(self.configuration_handle, cClockPhase)
        print("cClockPhase set to: ", cClockPhase)
        print("Return values of ni845xSpiConfigurationSetClockPhase: ", returnValue)
        self.ni845xStatusToString(returnValue)

    def ni845xSpiScriptDioConfigureLine(self, PortNumber, LineNumber, ConfigurationValue):
        """
        Adds an SPI Script DIO Configure Line command to an SPI script referenced by ScriptHandle. This command configures a DIO line on an NI 845x device
        int32 ni845xSpiScriptDioConfigureLine (NiHandle ScriptHandle,uInt8 PortNumber,uInt8 LineNumber,int32 ConfigurationValue);

        :param: NiHandle ScriptHandle, NiHandle ScriptHandle The script handle returned from ni845xSpiScriptOpen.
                uInt8 PortNumber: The DIO port that contains the LineNumber.
                uInt8 LineNumber: The DIO line to configure.
                int32 ConfigurationValue: The line configuration. ConfigurationValue uses the following values:
                • kNi845xDioInput (0): The line is configured for input.
                • kNi845xDioOutput (1): The line is configured for output.

        :return: The function call status. Zero means the function executed successfully. Negative specifies
        an error, meaning the function did not perform the expected behavior. Positive specifies a
        warning, meaning the function performed as expected, but a condition arose that might
        require attention. For more information, refer to ni845xStatusToString.
        """

        PortNumber = c.c_uint8(PortNumber)
        LineNumber = c.c_uint8(LineNumber)
        ConfigurationValue = c.c_int32(ConfigurationValue)
        returnValue = self.spi.ni845xSpiScriptDioConfigureLine(self.script_handle, PortNumber, LineNumber,
                                                               ConfigurationValue)
        print("PortNumber set to: ", PortNumber)
        print("LineNumber set to: ", LineNumber)
        print("ConfigurationValue set to: ", ConfigurationValue)
        print("Return values of ni845xSpiScriptDioConfigureLine: ", returnValue)
        self.ni845xStatusToString(returnValue)

    def ni845xDioWritePort(self, PortNumber, WriteData):
        """
        Adds an SPI Script DIO Configure Line command to an SPI script referenced by ScriptHandle. This command writes to a DIO line on an NI 845x device.
        int32 ni845xSpiScriptDioWriteLine (NiHandle ScriptHandle,uInt8 PortNumber,int32 WriteData);

        :param: NiHandle DeviceHandle Device handle returned from ni845xOpen.
                uInt8 PortNumber: The DIO port to write
                int32 WriteData:  The value to write to the DIO port. Only lines configured for output are updated.

        :return: The function call status. Zero means the function executed successfully. Negative specifies an error, meaning the function did not perform the expected behavior.
        Use ni845xDioWritePort to write all 8 bits on a byte-wide DIO port. For NI 845x devices with multiple DIO ports, use the PortNumber input to select the desired port.

        """

        PortNumber = c.c_uint8(PortNumber)
        WriteData = c.c_uint8(WriteData)
        returnValue = self.spi.ni845xDioWritePort(self.device_handle, PortNumber, WriteData)
        print("PortNumber set to: ", PortNumber)
        print("WriteData set to: ", WriteData)
        print("Return values of ni845xSpiScriptDioWriteLine: ", returnValue)
        self.ni845xStatusToString(returnValue)

    def ni845xSpiScriptDioWriteLine(self, PortNumber, LineNumber, WriteData):
        """
        Adds an SPI Script DIO Configure Line command to an SPI script referenced by ScriptHandle. This command writes to a DIO line on an NI 845x device.
        int32 ni845xSpiScriptDioWriteLine (NiHandle ScriptHandle,uInt8 PortNumber,uInt8 LineNumber,int32 WriteData);

        :param: NiHandle ScriptHandle The script handle returned from ni845xSpiScriptOpen.
                uInt8 PortNumber: The DIO port that contains the LineNumber.
                uInt8 LineNumber: The DIO line to write.
                int32 WriteData:  The value to write to the line. WriteData uses the following values:
                    • kNi845xDioLogicLow (0): The line is set to the logic low state.
                    • kNi845xDioLogicHigh (1): The line is set to the logic high state

        :return: The function call status. Zero means the function executed successfully. Negative specifies
        an error, meaning the function did not perform the expected behavior. Positive specifies a
        warning, meaning the function performed as expected, but a condition arose that might
        require attention. For more information, refer to ni845xStatusToString.
        """

        PortNumber = c.c_uint8(PortNumber)
        LineNumber = c.c_uint8(LineNumber)
        WriteData = c.c_uint32(WriteData)
        returnValue = self.spi.ni845xSpiScriptDioWriteLine(self.script_handle, PortNumber, LineNumber, WriteData)
        print("PortNumber set to: ", PortNumber)
        print("LineNumber set to: ", LineNumber)
        print("WriteData set to: ", WriteData)
        print("Return values of ni845xSpiScriptDioWriteLine: ", returnValue)
        self.ni845xStatusToString(returnValue)

    def ni845xSpiConfigurationSetClockPolarity(self, ClockPolarity):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationSetClockPolarity whose prototype is
        int32 ni845xSpiConfigurationSetClockPolarity (NiHandle ConfigurationHandle,int32 ClockPolarity);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
                int32 ClockPolarity: Sets the clock line idle state for the SPI Port.
                    ClockPolarity uses the following values:
                        • kNi845xSpiClockPolarityIdleLow (0): Clock is low in the idle state.
                        • kNi845xSpiClockPolarityIdleHigh (1): Clock is high in the idle state.
                The default value for this property is kNi845xSpiClockPolarityIdleLow.
        :return: None
        """
        cClockPolarity = c.c_uint32(ClockPolarity)
        returnValue = self.spi.ni845xSpiConfigurationSetClockPolarity(self.configuration_handle, cClockPolarity)
        print("cClockPolarity set to: ", cClockPolarity)
        print("Return values of ni845xSpiConfigurationSetClockPolarity: ", returnValue)
        self.ni845xStatusToString(returnValue)

    def ni845xSpiConfigurationSetClockRate(self, ClockRate):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationSetClockRate whose prototype is
        int32 ni845xSpiConfigurationSetClockRate (NiHandle ConfigurationHandle,uInt16 ClockRate);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
                uInt16 ClockRate: Specifies the SPI clock rate. Refer to Chapter 3, NI USB-845x Hardware Overview, to
                    determine which clock rates your NI 845x device supports. If your hardware does not
                    support the supplied clock rate, a warning is generated, and the next smallest supported
                    clock rate is used.
                    If the supplied clock rate is smaller than the smallest supported clock rate, an error is
                    generated. The configuration does not validate the clock rate until it is committed to hardware.
                The default value for the clock rate is 1000 kHz (1 MHz).
        :return: None
        """
        cClockRate = c.c_uint16(ClockRate)
        returnValue = self.spi.ni845xSpiConfigurationSetClockRate(self.configuration_handle, cClockRate)
        print("cClockPolarity set to: ", cClockRate)
        print("Return values of ni845xSpiConfigurationSetClockRate: ", returnValue)
        self.ni845xStatusToString(returnValue)

    def ni845xSpiConfigurationSetNumBitsPerSample(self, NumBitsPerSample):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationSetNumBitsPerSample whose prototype is
        int32 ni845xSpiConfigurationSetNumBitsPerSample (NiHandle ConfigurationHandle,uInt16 NumBitsPerSample);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
                uInt16 NumBitsPerSample: Specifies the number of bits per sample to be used for SPI transmissions.
                                        The default value for the number of bits per sample is 8.
                                        Refer to Appendix A, NI USB-845x Hardware Specifications, for valid settings for this property.
        :return: None
        """
        cNumBitsPerSample = c.c_uint16(NumBitsPerSample)
        returnValue = self.spi.ni845xSpiConfigurationSetNumBitsPerSample(self.configuration_handle, cNumBitsPerSample)
        print("cNumBitsPerSample set to: ", cNumBitsPerSample)
        print("Return values of ni845xSpiConfigurationSetNumBitsPerSample: ", returnValue)
        self.ni845xStatusToString(returnValue)

    def ni845xSpiConfigurationSetPort(self, Port):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationSetPort whose prototype is
        int32 ni845xSpiConfigurationSetPort (NiHandle ConfigurationHandle,uInt8 Port);
        :param: NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
                uInt8 Port: Specifies the SPI port that this configuration communicates across.
                            Refer to Chapter 3, NI USB-845x Hardware Overview, to determine the number of SPI
                            ports your NI 845x device supports.
                            The default value for the port number is 0.
        :return: None
        """
        cPort = c.c_uint8(Port)
        returnValue = self.spi.ni845xSpiConfigurationSetPort(self.configuration_handle, cPort)
        print("cNumBitsPerSample set to: ", cPort)
        print("Return values of ni845xSpiConfigurationSetPort: ", returnValue)
        self.ni845xStatusToString(returnValue)

    def ni845xSpiWriteRead(self, WriteData, WriteSize, ReadSize):
        """
        Calls the NI USB-8452 C API function ni845xSpiConfigurationSetPort whose prototype is
        int32 ni845xSpiWriteRead (NiHandle DeviceHandle,
                                  NiHandle ConfigurationHandle,
                                  uInt32 WriteSize,
                                  uInt8 * pWriteData,
                                  uInt32 * pReadSize,
                                  uInt8 * pReadData);
        :param: NiHandle DeviceHandle: Device handle returned from ni845xOpen.
                NiHandle ConfigurationHandle: The configuration handle returned from ni845xSpiConfigurationOpen.
                uInt32 WriteSize: The number of bytes to write. This must be nonzero.
                uInt8 * pWriteData: The data bytes to be written.
        :return: None
        """
        ReadData = list()
        cWriteSize = c.c_uint32(WriteSize)
        cWriteData = (c.c_uint8 * WriteSize)(*WriteData)
        cReadSize = c.c_uint32(ReadSize)
        cReadData = (c.c_uint8 * ReadSize)(*ReadData)
        returnValue = self.spi.ni845xSpiWriteRead(self.device_handle,
                                                  self.configuration_handle,
                                                  cWriteSize,
                                                  c.byref(cWriteData),
                                                  c.byref(cReadSize),
                                                  c.byref(cReadData)
                                                  )
        self.ni845xStatusToString(returnValue)
        ReadeSize = cReadSize
        ReadData = [cReadData[i] for i in range(ReadSize)]
        return ReadSize, ReadData


    # --------------------------- ioWriteDIO() ---------------------------------
    def ioWriteDIO(self, dioData=0):
            '''Writes dioData value out of GPIO port.  Assume necessary masking
            has already been applied to dioData. Returns 0/err code'''
            if self.spi is None:
                return -1
            fRet = self.spi.ni845xDioWritePort(self.device_handle, self.__IOPORT, c.c_uint8(dioData))
            if fRet != 0:
                pass
                print(self.__errStatus(fRet))
            return fRet

    # --------------------------- ioReadDIO() ---------------------------------
    def ioReadDIO(self):
            '''Returns DIO data value (uint8) returned from GPIO lines'''
            if self.spi is None:
                return 0
            fRet = self.spi.ni845xDioReadPort(self.device_handle, self.__IOPORT, c.byref(self._cIOdataIn))
            if fRet != 0:
                pass
                print(self.__errStatus(fRet))

            rData = self._cIOdataIn.value
            return rData
