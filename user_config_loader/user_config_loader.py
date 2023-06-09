from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

from construct import *

from .loader_utilities import AutoEnum, FrozenVectorAdapter, DataClassAdapter, OptionalAdapter, IntOrStrEnum

@dataclass
class ProfilingConfig:
    enabled: bool = True
    interval_sec: float = 0.0
    execution_profiling_contexts: List[int] = field(default_factory=list)

    @staticmethod
    def serialize(val: 'ProfilingConfig') -> bytes:
        return ProfilingConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'ProfilingConfig':
        return ProfilingConfigConstruct.parse(data)

_ProfilingConfigRawConstruct = Struct(
    "enabled" / Flag,
    Padding(3),
    "interval_sec" / Float32l,
    "execution_profiling_contexts" / FrozenVectorAdapter(2, Int32ul),
    Padding(32)
)
ProfilingConfigConstruct = DataClassAdapter(ProfilingConfig, _ProfilingConfigRawConstruct)


@dataclass
class Point3f:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    @staticmethod
    def serialize(val: 'Point3f') -> bytes:
        return Point3fConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'Point3f':
        return Point3fConstruct.parse(data)

_Point3fRawConstruct = Struct(
    "x" / Float32l,
    "y" / Float32l,
    "z" / Float32l
)
Point3fConstruct = DataClassAdapter(Point3f, _Point3fRawConstruct)


@dataclass
class GpsReceiverExtrinsicsConfig:
    uid: int = -1
    enabled: bool = True
    r_b_bg: Point3f = field(default_factory=lambda:Point3f(**{'x': 0.0, 'y': 0.0, 'z': 0.0}))

    @staticmethod
    def serialize(val: 'GpsReceiverExtrinsicsConfig') -> bytes:
        return GpsReceiverExtrinsicsConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'GpsReceiverExtrinsicsConfig':
        return GpsReceiverExtrinsicsConfigConstruct.parse(data)

_GpsReceiverExtrinsicsConfigRawConstruct = Struct(
    "uid" / Int32sl,
    "enabled" / Flag,
    Padding(3),
    "r_b_bg" / Point3fConstruct,
    Padding(32)
)
GpsReceiverExtrinsicsConfigConstruct = DataClassAdapter(GpsReceiverExtrinsicsConfig, _GpsReceiverExtrinsicsConfigRawConstruct)


@dataclass
class Matrix3x3Float:
    values: List[float] = field(default_factory=lambda:[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

    @staticmethod
    def serialize(val: 'Matrix3x3Float') -> bytes:
        return Matrix3x3FloatConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'Matrix3x3Float':
        return Matrix3x3FloatConstruct.parse(data)

_Matrix3x3FloatRawConstruct = Struct(
    "values" / Array(9, Float32l)
)
Matrix3x3FloatConstruct = DataClassAdapter(Matrix3x3Float, _Matrix3x3FloatRawConstruct)


@dataclass
class ImuExtrinsicsConfig:
    uid: int = -1
    enabled: bool = True
    r_b_bs: Point3f = field(default_factory=lambda:Point3f(**{'x': 0.0, 'y': 0.0, 'z': 0.0}))
    c_ds: Matrix3x3Float = field(default_factory=lambda:Matrix3x3Float(**{'values': [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]}))

    @staticmethod
    def serialize(val: 'ImuExtrinsicsConfig') -> bytes:
        return ImuExtrinsicsConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'ImuExtrinsicsConfig':
        return ImuExtrinsicsConfigConstruct.parse(data)

_ImuExtrinsicsConfigRawConstruct = Struct(
    "uid" / Int32sl,
    "enabled" / Flag,
    Padding(3),
    "r_b_bs" / Point3fConstruct,
    Padding(20),
    "c_ds" / Matrix3x3FloatConstruct,
    Padding(36)
)
ImuExtrinsicsConfigConstruct = DataClassAdapter(ImuExtrinsicsConfig, _ImuExtrinsicsConfigRawConstruct)


@dataclass
class Rotation3f:
    yaw_deg: float = 0.0
    pitch_deg: float = 0.0
    roll_deg: float = 0.0

    @staticmethod
    def serialize(val: 'Rotation3f') -> bytes:
        return Rotation3fConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'Rotation3f':
        return Rotation3fConstruct.parse(data)

_Rotation3fRawConstruct = Struct(
    "yaw_deg" / Float32l,
    "pitch_deg" / Float32l,
    "roll_deg" / Float32l
)
Rotation3fConstruct = DataClassAdapter(Rotation3f, _Rotation3fRawConstruct)


@dataclass
class ExternalPoseExtrinsicsConfig:
    uid: int = -1
    enabled: bool = True
    r_b_bp: Point3f = field(default_factory=lambda:Point3f(**{'x': 0.0, 'y': 0.0, 'z': 0.0}))
    c_pb: Rotation3f = field(default_factory=lambda:Rotation3f(**{'yaw_deg': 0.0, 'pitch_deg': 0.0, 'roll_deg': 0.0}))

    @staticmethod
    def serialize(val: 'ExternalPoseExtrinsicsConfig') -> bytes:
        return ExternalPoseExtrinsicsConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'ExternalPoseExtrinsicsConfig':
        return ExternalPoseExtrinsicsConfigConstruct.parse(data)

_ExternalPoseExtrinsicsConfigRawConstruct = Struct(
    "uid" / Int32sl,
    "enabled" / Flag,
    Padding(3),
    "r_b_bp" / Point3fConstruct,
    "c_pb" / Rotation3fConstruct,
    Padding(32)
)
ExternalPoseExtrinsicsConfigConstruct = DataClassAdapter(ExternalPoseExtrinsicsConfig, _ExternalPoseExtrinsicsConfigRawConstruct)


@dataclass
class SensorExtrinsicsConfig:
    gps_receivers: List[GpsReceiverExtrinsicsConfig] = field(default_factory=list)
    imus: List[ImuExtrinsicsConfig] = field(default_factory=list)
    external_pose: List[ExternalPoseExtrinsicsConfig] = field(default_factory=list)

    @staticmethod
    def serialize(val: 'SensorExtrinsicsConfig') -> bytes:
        return SensorExtrinsicsConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'SensorExtrinsicsConfig':
        return SensorExtrinsicsConfigConstruct.parse(data)

_SensorExtrinsicsConfigRawConstruct = Struct(
    "gps_receivers" / FrozenVectorAdapter(2, GpsReceiverExtrinsicsConfigConstruct),
    "imus" / FrozenVectorAdapter(1, ImuExtrinsicsConfigConstruct),
    "external_pose" / FrozenVectorAdapter(4, ExternalPoseExtrinsicsConfigConstruct),
    Padding(128)
)
SensorExtrinsicsConfigConstruct = DataClassAdapter(SensorExtrinsicsConfig, _SensorExtrinsicsConfigRawConstruct)


class VehicleModel(IntOrStrEnum):
    UNKNOWN_VEHICLE = 0
    DATASPEED_CD4 = 1
    J1939 = 2
    LEXUS_CT200H = 20
    KIA_SORENTO = 40
    KIA_SPORTAGE = 41
    AUDI_Q7 = 60
    AUDI_A8L = 61
    TESLA_MODEL_X = 80
    TESLA_MODEL_3 = 81
    HYUNDAI_ELANTRA = 100
    PEUGEOT_206 = 120
    MAN_TGX = 140
    FACTION = 160
    LINCOLN_MKZ = 180
    BMW_7 = 200
    VW_4 = 220

class WheelSensorType(IntOrStrEnum):
    NONE = 0
    TICK_RATE = 1
    TICKS = 2
    WHEEL_SPEED = 3
    VEHICLE_SPEED = 4
    VEHICLE_TICKS = 5

class AppliedSpeedType(IntOrStrEnum):
    NONE = 0
    REAR_WHEELS = 1
    FRONT_WHEELS = 2
    FRONT_AND_REAR_WHEELS = 3
    VEHICLE_BODY = 4

class SteeringType(IntOrStrEnum):
    UNKNOWN = 0
    FRONT = 1
    FRONT_AND_REAR = 2

class TickMode(IntOrStrEnum):
    OFF = 0
    RISING_EDGE = 1
    FALLING_EDGE = 2

class TickDirection(IntOrStrEnum):
    OFF = 0
    FORWARD_ACTIVE_HIGH = 1
    FORWARD_ACTIVE_LOW = 2

@dataclass
class CanConfig:
    id_whitelist: List[int] = field(default_factory=list)

    @staticmethod
    def serialize(val: 'CanConfig') -> bytes:
        return CanConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'CanConfig':
        return CanConfigConstruct.parse(data)

_CanConfigRawConstruct = Struct(
    "id_whitelist" / FrozenVectorAdapter(10, Int32ul),
    Padding(32)
)
CanConfigConstruct = DataClassAdapter(CanConfig, _CanConfigRawConstruct)


@dataclass
class VehicleConfig:
    vehicle_model: VehicleModel = VehicleModel.UNKNOWN_VEHICLE
    wheel_tick_output_interval_sec: float = float("NAN")
    wheelbase_m: float = float("NAN")
    front_track_width_m: float = float("NAN")
    rear_track_width_m: float = float("NAN")
    wheel_sensor_type: WheelSensorType = WheelSensorType.NONE
    applied_speed_type: AppliedSpeedType = AppliedSpeedType.REAR_WHEELS
    steering_type: SteeringType = SteeringType.UNKNOWN
    wheel_update_interval_sec: float = float("NAN")
    steering_ratio: float = float("NAN")
    wheel_ticks_to_m: float = float("NAN")
    wheel_tick_max_value: int = 0
    wheel_ticks_signed: bool = False
    wheel_ticks_always_increase: bool = True
    tick_mode: TickMode = TickMode.OFF
    tick_direction: TickDirection = TickDirection.OFF
    can: CanConfig = field(default_factory=lambda:CanConfig())

    @staticmethod
    def serialize(val: 'VehicleConfig') -> bytes:
        return VehicleConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'VehicleConfig':
        return VehicleConfigConstruct.parse(data)

_VehicleConfigRawConstruct = Struct(
    "vehicle_model" / AutoEnum(Int16ul, VehicleModel),
    Padding(6),
    "wheel_tick_output_interval_sec" / Float32l,
    "wheelbase_m" / Float32l,
    "front_track_width_m" / Float32l,
    "rear_track_width_m" / Float32l,
    "wheel_sensor_type" / AutoEnum(Int8ul, WheelSensorType),
    "applied_speed_type" / AutoEnum(Int8ul, AppliedSpeedType),
    "steering_type" / AutoEnum(Int8ul, SteeringType),
    Padding(1),
    "wheel_update_interval_sec" / Float32l,
    "steering_ratio" / Float32l,
    "wheel_ticks_to_m" / Float32l,
    "wheel_tick_max_value" / Int32ul,
    "wheel_ticks_signed" / Flag,
    "wheel_ticks_always_increase" / Flag,
    "tick_mode" / AutoEnum(Int8ul, TickMode),
    "tick_direction" / AutoEnum(Int8ul, TickDirection),
    "can" / CanConfigConstruct,
    Padding(24)
)
VehicleConfigConstruct = DataClassAdapter(VehicleConfig, _VehicleConfigRawConstruct)


@dataclass
class NavigationConfig:
    r_b_bo: Point3f = field(default_factory=lambda:Point3f(**{'x': 0.0, 'y': 0.0, 'z': 0.0}))
    enu_datum_shift_m: Point3f = field(default_factory=lambda:Point3f(**{'x': 0.0, 'y': 0.0, 'z': 0.0}))
    enable_gps: bool = True
    enable_glonass: bool = True
    enable_galileo: bool = True
    enable_beidou: bool = True
    enable_qzss: bool = True
    enable_sbas: bool = True
    enable_irnss: bool = True
    enable_l1: bool = True
    enable_l2: bool = True
    enable_l5: bool = True

    @staticmethod
    def serialize(val: 'NavigationConfig') -> bytes:
        return NavigationConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'NavigationConfig':
        return NavigationConfigConstruct.parse(data)

_NavigationConfigRawConstruct = Struct(
    "r_b_bo" / Point3fConstruct,
    "enu_datum_shift_m" / Point3fConstruct,
    "enable_gps" / Flag,
    "enable_glonass" / Flag,
    "enable_galileo" / Flag,
    "enable_beidou" / Flag,
    "enable_qzss" / Flag,
    "enable_sbas" / Flag,
    "enable_irnss" / Flag,
    "enable_l1" / Flag,
    "enable_l2" / Flag,
    "enable_l5" / Flag,
    Padding(2),
    Padding(64)
)
NavigationConfigConstruct = DataClassAdapter(NavigationConfig, _NavigationConfigRawConstruct)


@dataclass
class FusionEngineMessageConfig:
    pose_enabled: bool = True
    pose_aux_enabled: bool = False
    gnss_info_enabled: bool = True
    gnss_satellite_enabled: bool = False
    imu_enabled: bool = False
    gnss_enabled: bool = False
    ros_pose_enabled: bool = False
    ros_gps_fix_enabled: bool = False
    ros_imu_enabled: bool = False
    shutter_enabled: bool = False
    config_enabled: bool = False
    profile_system_status_enabled: bool = True
    profile_pipeline_enabled: bool = True
    profile_execution_enabled: bool = False

    @staticmethod
    def serialize(val: 'FusionEngineMessageConfig') -> bytes:
        return FusionEngineMessageConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'FusionEngineMessageConfig':
        return FusionEngineMessageConfigConstruct.parse(data)

_FusionEngineMessageConfigRawConstruct = Struct(
    "pose_enabled" / Flag,
    "pose_aux_enabled" / Flag,
    "gnss_info_enabled" / Flag,
    "gnss_satellite_enabled" / Flag,
    "imu_enabled" / Flag,
    "gnss_enabled" / Flag,
    "ros_pose_enabled" / Flag,
    "ros_gps_fix_enabled" / Flag,
    "ros_imu_enabled" / Flag,
    "shutter_enabled" / Flag,
    "config_enabled" / Flag,
    "profile_system_status_enabled" / Flag,
    "profile_pipeline_enabled" / Flag,
    "profile_execution_enabled" / Flag,
    Padding(18)
)
FusionEngineMessageConfigConstruct = DataClassAdapter(FusionEngineMessageConfig, _FusionEngineMessageConfigRawConstruct)


@dataclass
class FusionEngineClientConfig:
    enabled: bool = True
    messages: FusionEngineMessageConfig = field(default_factory=lambda:FusionEngineMessageConfig())
    output_interval_sec: float = 0.1
    log_to_disk: bool = False
    ignored_incoming_message_types: List[int] = field(default_factory=list)

    @staticmethod
    def serialize(val: 'FusionEngineClientConfig') -> bytes:
        return FusionEngineClientConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'FusionEngineClientConfig':
        return FusionEngineClientConfigConstruct.parse(data)

_FusionEngineClientConfigRawConstruct = Struct(
    "enabled" / Flag,
    Padding(3),
    "messages" / FusionEngineMessageConfigConstruct,
    Padding(64),
    "output_interval_sec" / Float32l,
    "log_to_disk" / Flag,
    Padding(3),
    "ignored_incoming_message_types" / FrozenVectorAdapter(4, Int16ul),
    Padding(64)
)
FusionEngineClientConfigConstruct = DataClassAdapter(FusionEngineClientConfig, _FusionEngineClientConfigRawConstruct)


@dataclass
class UIConfig:
    enabled: bool = True

    @staticmethod
    def serialize(val: 'UIConfig') -> bytes:
        return UIConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'UIConfig':
        return UIConfigConstruct.parse(data)

_UIConfigRawConstruct = Struct(
    "enabled" / Flag,
    Padding(3)
)
UIConfigConstruct = DataClassAdapter(UIConfig, _UIConfigRawConstruct)


@dataclass
class NMEAConfig:
    enabled: bool = True

    @staticmethod
    def serialize(val: 'NMEAConfig') -> bytes:
        return NMEAConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'NMEAConfig':
        return NMEAConfigConstruct.parse(data)

_NMEAConfigRawConstruct = Struct(
    "enabled" / Flag,
    Padding(67)
)
NMEAConfigConstruct = DataClassAdapter(NMEAConfig, _NMEAConfigRawConstruct)


class SerialParity(IntOrStrEnum):
    NONE = 0
    EVEN = 1
    ODD = 2

class SerialStopBit(IntOrStrEnum):
    STOPBITS_0_5 = 0
    STOPBITS_1 = 1
    STOPBITS_1_5 = 2
    STOPBITS_2 = 3

@dataclass
class SerialConfig:
    baud_rate: int = 460800
    data_width: int = 8
    parity: SerialParity = SerialParity.NONE
    stop_bits: SerialStopBit = SerialStopBit.STOPBITS_1

    @staticmethod
    def serialize(val: 'SerialConfig') -> bytes:
        return SerialConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'SerialConfig':
        return SerialConfigConstruct.parse(data)

_SerialConfigRawConstruct = Struct(
    "baud_rate" / Int32ul,
    "data_width" / Int8ul,
    "parity" / AutoEnum(Int8ul, SerialParity),
    "stop_bits" / AutoEnum(Int8ul, SerialStopBit),
    Padding(1)
)
SerialConfigConstruct = DataClassAdapter(SerialConfig, _SerialConfigRawConstruct)


class MessageRate(IntOrStrEnum):
    OFF = 0
    ON_CHANGE = 1
    INTERVAL_10_MS = 2
    INTERVAL_20_MS = 3
    INTERVAL_40_MS = 4
    INTERVAL_50_MS = 5
    INTERVAL_100_MS = 6
    INTERVAL_200_MS = 7
    INTERVAL_500_MS = 8
    INTERVAL_1_S = 9
    INTERVAL_2_S = 10
    INTERVAL_5_S = 11
    INTERVAL_10_S = 12
    INTERVAL_30_S = 13
    INTERVAL_60_S = 14

@dataclass
class FusionEngineMessageRates:
    pose: MessageRate = MessageRate.OFF
    gnss_info: MessageRate = MessageRate.OFF
    gnss_satellite: MessageRate = MessageRate.OFF
    pose_aux: MessageRate = MessageRate.OFF
    calibration_status: MessageRate = MessageRate.OFF
    relative_enu_position: MessageRate = MessageRate.OFF
    imu_measurement: MessageRate = MessageRate.OFF
    wheel_speed_measurement: MessageRate = MessageRate.OFF
    vehicle_speed_measurement: MessageRate = MessageRate.OFF
    wheel_tick_measurement: MessageRate = MessageRate.OFF
    vehicle_tick_measurement: MessageRate = MessageRate.OFF
    ros_pose: MessageRate = MessageRate.OFF
    ros_gps_fix: MessageRate = MessageRate.OFF
    ros_imu: MessageRate = MessageRate.OFF
    version_info: MessageRate = MessageRate.OFF
    event_notification: MessageRate = MessageRate.OFF

    @staticmethod
    def serialize(val: 'FusionEngineMessageRates') -> bytes:
        return FusionEngineMessageRatesConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'FusionEngineMessageRates':
        return FusionEngineMessageRatesConstruct.parse(data)

_FusionEngineMessageRatesRawConstruct = Struct(
    "pose" / AutoEnum(Int8ul, MessageRate),
    "gnss_info" / AutoEnum(Int8ul, MessageRate),
    "gnss_satellite" / AutoEnum(Int8ul, MessageRate),
    "pose_aux" / AutoEnum(Int8ul, MessageRate),
    "calibration_status" / AutoEnum(Int8ul, MessageRate),
    "relative_enu_position" / AutoEnum(Int8ul, MessageRate),
    "imu_measurement" / AutoEnum(Int8ul, MessageRate),
    "wheel_speed_measurement" / AutoEnum(Int8ul, MessageRate),
    "vehicle_speed_measurement" / AutoEnum(Int8ul, MessageRate),
    "wheel_tick_measurement" / AutoEnum(Int8ul, MessageRate),
    "vehicle_tick_measurement" / AutoEnum(Int8ul, MessageRate),
    "ros_pose" / AutoEnum(Int8ul, MessageRate),
    "ros_gps_fix" / AutoEnum(Int8ul, MessageRate),
    "ros_imu" / AutoEnum(Int8ul, MessageRate),
    "version_info" / AutoEnum(Int8ul, MessageRate),
    "event_notification" / AutoEnum(Int8ul, MessageRate),
    Padding(24)
)
FusionEngineMessageRatesConstruct = DataClassAdapter(FusionEngineMessageRates, _FusionEngineMessageRatesRawConstruct)


@dataclass
class NMEAMessageRates:
    gga: MessageRate = MessageRate.OFF
    gll: MessageRate = MessageRate.OFF
    gsa: MessageRate = MessageRate.OFF
    gsv: MessageRate = MessageRate.OFF
    rmc: MessageRate = MessageRate.OFF
    vtg: MessageRate = MessageRate.OFF
    p1calstatus: MessageRate = MessageRate.OFF
    p1msg: MessageRate = MessageRate.OFF
    pqtmverno: MessageRate = MessageRate.OFF
    pqtmver: MessageRate = MessageRate.OFF
    pqtmgnss: MessageRate = MessageRate.OFF
    pqtmverno_sub: MessageRate = MessageRate.OFF
    pqtmver_sub: MessageRate = MessageRate.OFF
    pqtmtxt: MessageRate = MessageRate.OFF

    @staticmethod
    def serialize(val: 'NMEAMessageRates') -> bytes:
        return NMEAMessageRatesConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'NMEAMessageRates':
        return NMEAMessageRatesConstruct.parse(data)

_NMEAMessageRatesRawConstruct = Struct(
    "gga" / AutoEnum(Int8ul, MessageRate),
    "gll" / AutoEnum(Int8ul, MessageRate),
    "gsa" / AutoEnum(Int8ul, MessageRate),
    "gsv" / AutoEnum(Int8ul, MessageRate),
    "rmc" / AutoEnum(Int8ul, MessageRate),
    "vtg" / AutoEnum(Int8ul, MessageRate),
    "p1calstatus" / AutoEnum(Int8ul, MessageRate),
    "p1msg" / AutoEnum(Int8ul, MessageRate),
    "pqtmverno" / AutoEnum(Int8ul, MessageRate),
    "pqtmver" / AutoEnum(Int8ul, MessageRate),
    "pqtmgnss" / AutoEnum(Int8ul, MessageRate),
    "pqtmverno_sub" / AutoEnum(Int8ul, MessageRate),
    "pqtmver_sub" / AutoEnum(Int8ul, MessageRate),
    "pqtmtxt" / AutoEnum(Int8ul, MessageRate),
    Padding(2)
)
NMEAMessageRatesConstruct = DataClassAdapter(NMEAMessageRates, _NMEAMessageRatesRawConstruct)


@dataclass
class RTCMMessageRates:


    @staticmethod
    def serialize(val: 'RTCMMessageRates') -> bytes:
        return RTCMMessageRatesConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'RTCMMessageRates':
        return RTCMMessageRatesConstruct.parse(data)

_RTCMMessageRatesRawConstruct = Struct(
    Padding(40)
)
RTCMMessageRatesConstruct = DataClassAdapter(RTCMMessageRates, _RTCMMessageRatesRawConstruct)


@dataclass
class ProtocolMessageRates:
    fusion_engine_rates: FusionEngineMessageRates = field(default_factory=lambda:FusionEngineMessageRates())
    nmea_rates: NMEAMessageRates = field(default_factory=lambda:NMEAMessageRates())
    rtcm_rates: RTCMMessageRates = field(default_factory=lambda:RTCMMessageRates())
    diagnostic_messages_enabled: bool = False

    @staticmethod
    def serialize(val: 'ProtocolMessageRates') -> bytes:
        return ProtocolMessageRatesConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'ProtocolMessageRates':
        return ProtocolMessageRatesConstruct.parse(data)

_ProtocolMessageRatesRawConstruct = Struct(
    "fusion_engine_rates" / FusionEngineMessageRatesConstruct,
    "nmea_rates" / NMEAMessageRatesConstruct,
    "rtcm_rates" / RTCMMessageRatesConstruct,
    "diagnostic_messages_enabled" / Flag,
    Padding(3)
)
ProtocolMessageRatesConstruct = DataClassAdapter(ProtocolMessageRates, _ProtocolMessageRatesRawConstruct)


@dataclass
class OutputInterfaceConfig:
    fe_client: FusionEngineClientConfig = field(default_factory=lambda:FusionEngineClientConfig())
    ui: UIConfig = field(default_factory=lambda:UIConfig())
    nmea: NMEAConfig = field(default_factory=lambda:NMEAConfig())
    serial_ports: List[SerialConfig] = field(default_factory=list)
    uart1_output_rates: ProtocolMessageRates = field(default_factory=lambda:ProtocolMessageRates())
    uart2_output_rates: ProtocolMessageRates = field(default_factory=lambda:ProtocolMessageRates())

    @staticmethod
    def serialize(val: 'OutputInterfaceConfig') -> bytes:
        return OutputInterfaceConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'OutputInterfaceConfig':
        return OutputInterfaceConfigConstruct.parse(data)

_OutputInterfaceConfigRawConstruct = Struct(
    "fe_client" / FusionEngineClientConfigConstruct,
    "ui" / UIConfigConstruct,
    "nmea" / NMEAConfigConstruct,
    Padding(4),
    "serial_ports" / FrozenVectorAdapter(2, SerialConfigConstruct),
    "uart1_output_rates" / ProtocolMessageRatesConstruct,
    "uart2_output_rates" / ProtocolMessageRatesConstruct,
    Padding(20)
)
OutputInterfaceConfigConstruct = DataClassAdapter(OutputInterfaceConfig, _OutputInterfaceConfigRawConstruct)


@dataclass
class SystemControlConfig:
    enable_watchdog_timer: bool = True

    @staticmethod
    def serialize(val: 'SystemControlConfig') -> bytes:
        return SystemControlConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'SystemControlConfig':
        return SystemControlConfigConstruct.parse(data)

_SystemControlConfigRawConstruct = Struct(
    "enable_watchdog_timer" / Flag,
    Padding(3),
    Padding(128)
)
SystemControlConfigConstruct = DataClassAdapter(SystemControlConfig, _SystemControlConfigRawConstruct)


@dataclass
class UserConfig:
    profiling: ProfilingConfig = field(default_factory=lambda:ProfilingConfig())
    sensors: SensorExtrinsicsConfig = field(default_factory=lambda:SensorExtrinsicsConfig())
    vehicle: VehicleConfig = field(default_factory=lambda:VehicleConfig())
    navigation: NavigationConfig = field(default_factory=lambda:NavigationConfig())
    output_interfaces: OutputInterfaceConfig = field(default_factory=lambda:OutputInterfaceConfig())
    system_controls: SystemControlConfig = field(default_factory=lambda:SystemControlConfig())
    VERSION: str = "4.3"

    @staticmethod
    def serialize(val: 'UserConfig') -> bytes:
        return UserConfigConstruct.build(val)

    @staticmethod
    def deserialize(data: bytes) -> 'UserConfig':
        return UserConfigConstruct.parse(data)

    @staticmethod
    def get_version() -> Tuple[int, int]:
        """
        Ver 3 - Added serial port configuration support at the end of the output_interfaces member.
        Ver 3.1 - Modified fields in VehicleConfig.
        Ver 4.0 - Replaced protocol_output_mappings with generated output_rates.
        Ver 4.1 - Added system_controls with enable_watchdog_timer.
        Ver 4.2 - Update to force enable watchdog on current devices. 8/31/2022
        Ver 4.3 - Update to include NMEA PQTMTXT type. 1/31/2023

        """
        return 4, 3

_UserConfigRawConstruct = Struct(
    "profiling" / ProfilingConfigConstruct,
    "sensors" / SensorExtrinsicsConfigConstruct,
    "vehicle" / VehicleConfigConstruct,
    "navigation" / NavigationConfigConstruct,
    "output_interfaces" / OutputInterfaceConfigConstruct,
    "system_controls" / SystemControlConfigConstruct
)
UserConfigConstruct = DataClassAdapter(UserConfig, _UserConfigRawConstruct)

