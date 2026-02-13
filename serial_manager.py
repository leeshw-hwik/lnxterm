"""
시리얼 포트 관리 모듈
- 포트 스캔, 연결/해제, 데이터 송수신
- QThread 기반 비동기 수신
"""

import glob
import serial
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker


class SerialReaderThread(QThread):
    """시리얼 데이터 수신 스레드"""
    data_received = pyqtSignal(bytes)
    error_occurred = pyqtSignal(str)

    def __init__(self, serial_port: serial.Serial, parent=None):
        super().__init__(parent)
        self._serial = serial_port
        self._running = False
        self._mutex = QMutex()

    def run(self):
        self._running = True
        while self._running:
            try:
                if self._serial and self._serial.is_open:
                    if self._serial.in_waiting > 0:
                        data = self._serial.read(self._serial.in_waiting)
                        if data:
                            self.data_received.emit(data)
                    else:
                        # 짧은 대기 (CPU 부하 방지)
                        self.msleep(10)
                else:
                    break
            except serial.SerialException as e:
                self.error_occurred.emit(f"수신 오류: {str(e)}")
                break
            except Exception as e:
                self.error_occurred.emit(f"예기치 않은 오류: {str(e)}")
                break

    def stop(self):
        self._running = False
        self.wait(2000)  # 최대 2초 대기


class SerialManager:
    """시리얼 포트 관리 클래스"""

    # 기본 설정값
    DEFAULT_BAUDRATE = 115200
    BAUDRATES = [
        9600, 19200, 38400, 57600, 115200,
        230400, 460800, 921600, 1000000, 2000000
    ]
    DATABITS = {
        "5": serial.FIVEBITS,
        "6": serial.SIXBITS,
        "7": serial.SEVENBITS,
        "8": serial.EIGHTBITS,
    }
    PARITIES = {
        "None": serial.PARITY_NONE,
        "Even": serial.PARITY_EVEN,
        "Odd": serial.PARITY_ODD,
        "Mark": serial.PARITY_MARK,
        "Space": serial.PARITY_SPACE,
    }
    STOPBITS = {
        "1": serial.STOPBITS_ONE,
        "1.5": serial.STOPBITS_ONE_POINT_FIVE,
        "2": serial.STOPBITS_TWO,
    }

    def __init__(self):
        self._serial: serial.Serial | None = None
        self._reader_thread: SerialReaderThread | None = None

    @staticmethod
    def scan_ports() -> list[dict]:
        """사용 가능한 시리얼 포트 목록 반환"""
        ports = []
        # /dev/ttyACM* (ST-Link 등 USB CDC)
        for path in sorted(glob.glob("/dev/ttyACM*")):
            ports.append({"path": path, "description": "USB CDC (ACM)"})
        # /dev/ttyUSB* (USB-Serial 어댑터)
        for path in sorted(glob.glob("/dev/ttyUSB*")):
            ports.append({"path": path, "description": "USB-Serial"})
        # 가상 시리얼 (pts) - 테스트용
        for path in sorted(glob.glob("/dev/pts/*")):
            try:
                # 숫자로 끝나는 pts만
                int(path.split("/")[-1])
                ports.append({"path": path, "description": "Virtual (pts)"})
            except ValueError:
                continue
        return ports

    def connect(
        self,
        port: str,
        baudrate: int = DEFAULT_BAUDRATE,
        databits: int = serial.EIGHTBITS,
        parity: str = serial.PARITY_NONE,
        stopbits: float = serial.STOPBITS_ONE,
        timeout: float = 0.1,
    ) -> None:
        """시리얼 포트 연결"""
        if self._serial and self._serial.is_open:
            self.disconnect()

        self._serial = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=databits,
            parity=parity,
            stopbits=stopbits,
            timeout=timeout,
        )

    def disconnect(self) -> None:
        """시리얼 포트 연결 해제"""
        self.stop_reading()
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._serial is not None and self._serial.is_open

    def write(self, data: bytes) -> int:
        """데이터 송신"""
        if not self.is_connected():
            raise serial.SerialException("포트가 연결되지 않았습니다.")
        return self._serial.write(data)

    def start_reading(self) -> SerialReaderThread:
        """비동기 수신 스레드 시작"""
        if not self.is_connected():
            raise serial.SerialException("포트가 연결되지 않았습니다.")
        if self._reader_thread and self._reader_thread.isRunning():
            self.stop_reading()
        self._reader_thread = SerialReaderThread(self._serial)
        return self._reader_thread

    def stop_reading(self) -> None:
        """수신 스레드 중지"""
        if self._reader_thread:
            self._reader_thread.stop()
            self._reader_thread = None

    @property
    def port_name(self) -> str:
        """현재 연결된 포트 이름"""
        if self._serial:
            return self._serial.port
        return ""

    @property
    def baudrate(self) -> int:
        """현재 baudrate"""
        if self._serial:
            return self._serial.baudrate
        return 0
