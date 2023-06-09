#!/usr/bin/env python3
from datetime import datetime
import logging
import os
import sys

import serial

from fusion_engine_client.messages import *
from fusion_engine_client.utils.log import DEFAULT_LOG_BASE_DIR

# Add the parent directory to the search path to enable p1_runner package imports when not installed in Python.
repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(repo_root)

from p1_runner.argument_parser import ArgumentParser, ExtendedBooleanAction
from p1_runner.device_interface import DeviceInterface, RESPONSE_TIMEOUT
from p1_runner.exported_data import add_to_exported_data, create_exported_data, is_export_valid, load_saved_data
from p1_runner.find_serial_device import find_serial_device, PortType

logger = logging.getLogger('point_one.config_tool')


def _args_to_point3f(cls, args, config_interface):
    return cls(args.x, args.y, args.z)


SERIAL_TIMEOUT = 5


_orientation_map = {
    'forward': Direction.FORWARD,
    'backward': Direction.BACKWARD,
    'left': Direction.LEFT,
    'right': Direction.RIGHT,
    'up': Direction.UP,
    'down': Direction.DOWN
}

_data_types_map = {
    'user_config': [DataType.USER_CONFIG],
    'filter_state': [DataType.FILTER_STATE],
    'calibration': [DataType.CALIBRATION_STATE],
    'all': [DataType.USER_CONFIG, DataType.FILTER_STATE, DataType.CALIBRATION_STATE],
}


def _str_to_direction(dir_str):
    return _orientation_map.get(dir_str, "")


_vehicle_model_map = {
    "unknown_vehicle": VehicleModel.UNKNOWN_VEHICLE,
    "dataspeed_cd4": VehicleModel.DATASPEED_CD4,
    "j1939": VehicleModel.J1939,
    "lexus_ct200h": VehicleModel.LEXUS_CT200H,
    "kia_sorento": VehicleModel.KIA_SORENTO,
    "kia_sportage": VehicleModel.KIA_SPORTAGE,
    "audi_q7": VehicleModel.AUDI_Q7,
    "audi_a8l": VehicleModel.AUDI_A8L,
    "tesla_model_x": VehicleModel.TESLA_MODEL_X,
    "tesla_model_3": VehicleModel.TESLA_MODEL_3,
    "hyundai_elantra": VehicleModel.HYUNDAI_ELANTRA,
    "peugeot_206": VehicleModel.PEUGEOT_206,
    "man_tgx": VehicleModel.MAN_TGX,
    "faction": VehicleModel.FACTION,
    "lincoln_mkz": VehicleModel.LINCOLN_MKZ,
    "bmw_7": VehicleModel.BMW_7
}


def _str_to_vehicle_model(vehicle_model_str):
    return _vehicle_model_map.get(vehicle_model_str, VehicleModel.UNKNOWN_VEHICLE)


_wheel_sensor_type_map = {
    "none": WheelSensorType.NONE,
    "tick_rate": WheelSensorType.TICK_RATE,
    "ticks": WheelSensorType.TICKS,
    "wheel_speed": WheelSensorType.WHEEL_SPEED,
    "vehicle_speed": WheelSensorType.VEHICLE_SPEED,
    "vehicle_ticks": WheelSensorType.VEHICLE_TICKS
}


def _str_to_wheel_sensor_type(wheel_sensor_type_str):
    return _wheel_sensor_type_map.get(wheel_sensor_type_str, WheelSensorType.NONE)


_applied_speed_type_map = {
    "none": AppliedSpeedType.NONE,
    "rear_wheels": AppliedSpeedType.REAR_WHEELS,
    "front_wheels": AppliedSpeedType.FRONT_WHEELS,
    "front_and_rear_wheels": AppliedSpeedType.FRONT_AND_REAR_WHEELS,
    "vehicle_body": AppliedSpeedType.VEHICLE_BODY
}


def _str_to_applied_speed_type(applied_speed_type_str):
    return _applied_speed_type_map.get(applied_speed_type_str, AppliedSpeedType.NONE)


_steering_type_map = {
    "unknown": SteeringType.UNKNOWN,
    "front": SteeringType.FRONT,
    "front_and_rear": SteeringType.FRONT_AND_REAR
}


def _str_to_steering_type(steering_type_str):
    return _steering_type_map.get(steering_type_str, SteeringType.UNKNOWN)


_tick_mode_map = {
    "off": TickMode.OFF,
    "rising_edge": TickMode.RISING_EDGE,
    "falling_edge": TickMode.FALLING_EDGE
}


def _str_to_tick_mode(tick_mode_str):
    return _tick_mode_map.get(tick_mode_str, TickMode.OFF)


_tick_direction_map = {
    "off": TickDirection.OFF,
    "forward_active_high": TickDirection.FORWARD_ACTIVE_HIGH,
    "forward_active_low": TickDirection.FORWARD_ACTIVE_LOW
}


def _str_to_tick_direction(tick_direction_str):
    return _tick_direction_map.get(tick_direction_str, TickDirection.OFF)


def _args_to_coarse_orientation(cls, args, config_interface):
    return DeviceCourseOrientationConfig(_str_to_direction(args.x), _str_to_direction(args.z))


def _args_to_vehicle_details(cls, args, config_interface):
    # Query the existing parameters, so we can use those values if any of the user settings are unspecified.
    config_interface.get_config(ConfigurationSource.ACTIVE, VehicleDetailsConfig.GetType())
    resp = config_interface.wait_for_message(ConfigResponseMessage.MESSAGE_TYPE)

    if resp is None:
        raise RuntimeError('Response timed out after %d seconds while querying current values.' % RESPONSE_TIMEOUT)

    if args.vehicle_model is None:
        vehicle_model = resp.config_object.vehicle_model
    else:
        vehicle_model = _str_to_vehicle_model(args.vehicle_model)

    wheelbase_m = args.wheelbase if args.wheelbase is not None else resp.config_object.wheelbase_m
    front_track_width_m = (args.front_track_width if args.front_track_width is not None else
                           resp.config_object.front_track_width_m)
    rear_track_width_m = (args.rear_track_width if args.rear_track_width is not None else
                          resp.config_object.rear_track_width_m)

    return VehicleDetailsConfig(vehicle_model=vehicle_model, wheelbase_m=wheelbase_m,
                                front_track_width_m=front_track_width_m, rear_track_width_m=rear_track_width_m)


def _args_to_wheel_config(cls, args, config_interface):
    # Query the existing parameters, so we can use those values if any of the user settings are unspecified.
    config_interface.get_config(ConfigurationSource.ACTIVE, WheelConfig.GetType())
    resp = config_interface.wait_for_message(ConfigResponseMessage.MESSAGE_TYPE)

    if resp is None:
        raise RuntimeError('Response timed out after %d seconds while querying current values.' % RESPONSE_TIMEOUT)

    new_values = {}

    if args.wheel_sensor_type is not None:
        new_values['wheel_sensor_type'] = _str_to_wheel_sensor_type(args.wheel_sensor_type)

    if args.applied_speed_type is not None:
        new_values['applied_speed_type'] = _str_to_applied_speed_type(args.applied_speed_type)

    if args.steering_type is not None:
        new_values['steering_type'] = _str_to_steering_type(args.steering_type)

    if args.steering_ratio is not None:
        new_values['steering_ratio'] = args.steering_ratio

    if args.wheel_update_interval is not None:
        new_values['wheel_update_interval_sec'] = args.wheel_update_interval

    if args.wheel_tick_interval is not None:
        new_values['wheel_tick_output_interval_sec'] = args.wheel_tick_interval

    if args.meters_per_tick is not None:
        new_values['wheel_ticks_to_m'] = args.meters_per_tick

    if args.wheel_tick_max_value is not None:
        new_values['wheel_tick_max_value'] = args.wheel_tick_max_value

    if args.wheel_ticks_signed is not None:
        new_values['wheel_ticks_signed'] = args.wheel_ticks_signed

    if args.wheel_ticks_always_increase is not None:
        new_values['wheel_ticks_always_increase'] = args.wheel_ticks_always_increase

    result = resp.config_object._replace(**new_values)
    return result


def _args_to_hardware_tick_config(cls, args, config_interface):
    # Query the existing parameters, so we can use those values if any of the user settings are unspecified.
    config_interface.get_config(ConfigurationSource.ACTIVE, HardwareTickConfig.GetType())
    resp = config_interface.wait_for_message(ConfigResponseMessage.MESSAGE_TYPE)

    if resp is None:
        raise RuntimeError('Response timed out after %d seconds while querying current values.' % RESPONSE_TIMEOUT)

    if args.tick_mode is None:
        tick_mode = resp.config_object.tick_mode
    else:
        tick_mode = _str_to_tick_mode(args.tick_mode)

    if args.tick_direction is None:
        tick_direction = resp.config_object.tick_direction
    else:
        tick_direction = _str_to_tick_direction(args.tick_direction)

    if args.meters_per_tick is None:
        wheel_ticks_to_m = resp.config_object.wheel_ticks_to_m
    else:
        wheel_ticks_to_m = args.meters_per_tick

    return HardwareTickConfig(tick_mode=tick_mode, tick_direction=tick_direction, wheel_ticks_to_m=wheel_ticks_to_m)


_interface_map = {
    'uart1': InterfaceID(TransportType.SERIAL, 1),
    'uart2': InterfaceID(TransportType.SERIAL, 2)
}

_protocol_map = {
    'fe': ProtocolType.FUSION_ENGINE,
    'fusionengine': ProtocolType.FUSION_ENGINE,
    'fusion_engine': ProtocolType.FUSION_ENGINE,
    'nmea': ProtocolType.NMEA,
    'rtcm': ProtocolType.RTCM,
    'all': ProtocolType.ALL,
}

_rate_map = {
    'off': MessageRate.OFF,
    'on': MessageRate.ON_CHANGE,
    'on_change': MessageRate.ON_CHANGE,
    '60s': MessageRate.INTERVAL_60_S,
    '30s': MessageRate.INTERVAL_30_S,
    '10s': MessageRate.INTERVAL_10_S,
    '5s': MessageRate.INTERVAL_5_S,
    '2s': MessageRate.INTERVAL_2_S,
    '1s': MessageRate.INTERVAL_1_S,
    '500ms': MessageRate.INTERVAL_500_MS,
    '200ms': MessageRate.INTERVAL_200_MS,
    '100ms': MessageRate.INTERVAL_100_MS,
    'default': MessageRate.DEFAULT,
}


def _args_to_baud(cls, args, config_interface):
    return cls(int(args.baud_rate))


def _args_to_bool(cls, args, config_interface):
    return cls(args.enabled)


def _get_message_id(protocol: ProtocolType, message_type_str) -> int:
    if message_type_str.lower() == 'all':
        message_id = ALL_MESSAGES_ID
    elif protocol == ProtocolType.NMEA:
        message_id = NmeaMessageType[message_type_str.upper()]
    elif protocol == ProtocolType.FUSION_ENGINE:
        message_id = None

        # Try the message ID as an integer first.
        try:
            message_id = int(message_type_str)
            if message_id not in message_type_to_class:
                raise ValueError('Unrecognized FusionEngine message ID %d.' % message_id)
        # If that fails, try to find the message by name or by partial-match.
        except ValueError:
            # Convert to lowercase to perform case-insensitive search.
            type_by_name = {k.lower(): v for k, v in message_type_by_name.items()}

            # Try for an exact match.
            lower_name = message_type_str.lower()
            message_type = type_by_name.get(lower_name, None)

            # If we can't find an exact match for the key, try a partial match.
            if message_type is None:
                matches = {k: v for k, v in type_by_name.items() if k.startswith(lower_name)}
                if len(matches) == 1:
                    message_type = next(iter(matches.values()))
                elif len(matches) > 1:
                    types = [v for v in matches.values()]
                    class_names = [message_type_to_class[t].__name__ for t in types]
                    raise ValueError("Found multiple types matching '%s':\n  %s" %
                                     (message_type_str, '\n  '.join(class_names)))
                else:
                    print("Unrecognized message type '%s'." % message_type_str)
                    sys.exit(1)

            if message_type is not None:
                message_id = int(message_type)
            else:
                raise ValueError("Unrecognized FusionEngine message type '%s'." % message_type_str)
    else:
        message_id = int(message_type_str)

    return message_id


def parse_message_rate_args(interface, protocol, message_id):
    interface = _interface_map[interface.lower()]
    protocol = _protocol_map[protocol.lower()]
    msg_id = _get_message_id(protocol, message_id)
    return [interface, protocol, msg_id]


def _message_rate_args_to_output_interface(cls, args, config_interface):
    (interface, protocol, message_id) = parse_message_rate_args(interface=args.param.split('_')[0],
                                                                protocol=args.protocol, message_id=args.message_id)
    try:
        rate = _rate_map[args.rate.lower()]
    except KeyError:
        rate = _rate_map[args.rate.lower().replace('_', '')]

    flags = 0
    if args.save:
        flags |= SetMessageRate.FLAG_APPLY_AND_SAVE
    if args.include_disabled:
        flags |= SetMessageRate.FLAG_INCLUDE_DISABLED_MESSAGES
    return [interface, protocol, message_id, rate, flags]


PARAM_DEFINITION = {
    'gnss': {'format': GnssLeverArmConfig, 'arg_parse': _args_to_point3f},
    'device': {'format': DeviceLeverArmConfig, 'arg_parse': _args_to_point3f},
    'orientation': {'format': DeviceCourseOrientationConfig, 'arg_parse': _args_to_coarse_orientation},
    'output': {'format': OutputLeverArmConfig, 'arg_parse': _args_to_point3f},

    'vehicle_details': {'format': VehicleDetailsConfig, 'arg_parse': _args_to_vehicle_details},
    'wheel_config': {'format': WheelConfig, 'arg_parse': _args_to_wheel_config},
    'hardware_tick_config': {'format': HardwareTickConfig, 'arg_parse': _args_to_hardware_tick_config},

    'uart1_baud': {'format': Uart1BaudConfig, 'arg_parse': _args_to_baud},
    'uart2_baud': {'format': Uart2BaudConfig, 'arg_parse': _args_to_baud},
    'uart1_diagnostics_enabled': {'format': Uart1DiagnosticMessagesEnabled, 'arg_parse': _args_to_bool},
    'uart2_diagnostics_enabled': {'format': Uart2DiagnosticMessagesEnabled, 'arg_parse': _args_to_bool},
    'watchdog_enabled': {'format': WatchdogTimerEnabled, 'arg_parse': _args_to_bool},
    'uart1_message_rate': {'format': list, 'arg_parse': _message_rate_args_to_output_interface},
    'uart2_message_rate': {'format': list, 'arg_parse': _message_rate_args_to_output_interface},
}

_cocom_type = {str(e).lower(): e for e in CoComType}


def read_config(config_interface: DeviceInterface, args):
    if args.type == 'saved':
        source = ConfigurationSource.SAVED
        desc = "Saved"
    else:
        source = ConfigurationSource.ACTIVE
        desc = "Active"

    logger.debug('Reading %s configuration.' % desc.lower())

    if len(args.param) == 0:
        params = PARAM_DEFINITION.copy()
        del params['uart1_message_rate']
        del params['uart2_message_rate']
    else:
        params = {args.param[0]: PARAM_DEFINITION[args.param[0]]}
        if args.param[0].endswith('_message_rate'):
            message_params = parse_message_rate_args(interface=args.param[0].split('_')[0], protocol=args.param[1],
                                                     message_id=args.param[2])

    first = True
    for key, definition in params.items():
        skip = definition.get('skip_read')
        if skip:
            logger.info('  %s: No read defined', key)
            continue

        format = definition['format']
        if key.endswith('_message_rate'):
            config_interface.get_message_rate(source, message_params)
            resp = config_interface.wait_for_message(MessageRateResponse.MESSAGE_TYPE)
        else:
            type = format.GetType()
            config_interface.get_config(source, type)
            resp = config_interface.wait_for_message(ConfigResponseMessage.MESSAGE_TYPE)

        if resp is None:
            logger.error('Response timed out after %d seconds.' % RESPONSE_TIMEOUT)
            return False

        if first:
            logger.info('%s parameter values:' % desc)
            first = False

        if resp.response != Response.OK:
            logger.error('  %s: %s (%d)' % (key, str(resp.response), int(resp.response)))
        else:
            if key.endswith('_message_rate'):
                for rate in resp.rates:
                    modified_str = ''
                    effective_str = ''
                    label = f'{key} {rate.protocol} {rate.message_id}'
                    if rate.configured_rate != rate.effective_rate:
                        effective_str = f' (effective rate is {rate.effective_rate} since diagnostics enabled)'
                    if rate.flags & MessageRateResponse.FLAG_ACTIVE_DIFFERS_FROM_SAVED:
                        modified_str = ' (active differs from saved)'
                    logger.info('  %s: %s%s%s', label, str(rate.configured_rate), effective_str, modified_str)
            else:
                modified_str = ''
                if resp.flags & ConfigResponseMessage.FLAG_ACTIVE_DIFFERS_FROM_SAVED:
                    modified_str = '(active differs from saved)'
                logger.info('  %s: %s %s', key, str(resp.config_object), modified_str)
    return True


def apply_config(config_interface: DeviceInterface, args):
    definition = PARAM_DEFINITION[args.param]
    format = definition['format']
    arg_parse = definition['arg_parse']

    config_object = arg_parse(cls=format, args=args, config_interface=config_interface)

    logger.debug('Applying config parameter update.')
    if args.param.endswith('_message_rate'):
        config_interface.set_message_rate(config_object)
    else:
        config_interface.set_config(config_object, args.save)

    resp = config_interface.wait_for_message(CommandResponseMessage.MESSAGE_TYPE)
    if resp is None:
        logger.error('Response timed out after %d seconds.' % RESPONSE_TIMEOUT)
        return False
    elif resp.response != Response.OK:
        logger.error('Apply command rejected: %s (%d)' % (str(resp.response), int(resp.response)))
        return False
    else:
        logger.info('Parameter changed successfully.')
        return True


def save_config(config_interface: DeviceInterface, args):
    logger.debug('Saving lever arm parameter updates.')
    config_interface.send_save()

    resp = config_interface.wait_for_message(CommandResponseMessage.MESSAGE_TYPE)
    if resp is None:
        logger.error('Response timed out after %d seconds.' % RESPONSE_TIMEOUT)
        return False
    elif resp.response != Response.OK:
        logger.error('Saving command rejected: %s (%d)' % (str(resp.response), int(resp.response)))
        return False
    else:
        logger.info('Configuration saved successfully.')
        return True


def query_version(config_interface: DeviceInterface, args):
    if args.type == 'nmea':
        return query_nmea_version(config_interface, args)
    else:
        return query_fe_version(config_interface, args)


def query_fe_version(config_interface: DeviceInterface, args):
    logger.debug('Querying version info.')
    config_interface.send_message(MessageRequest(MessageType.VERSION_INFO))

    resp = config_interface.wait_for_message(VersionInfoMessage.MESSAGE_TYPE)
    if resp is None:
        logger.error('Response timed out after %d seconds.' % RESPONSE_TIMEOUT)
        return False
    else:
        logger.info(str(resp))
        return True


def query_nmea_version(config_interface: DeviceInterface, args):
    logger.debug('Querying NMEA version info.')

    config_interface.send_message('$PQTMVERNO')
    resp = config_interface.wait_for_message('$PQTMVERNO')
    if resp is None:
        logger.error('Response timed out after %d seconds.' % RESPONSE_TIMEOUT)
        return False
    else:
        logger.info(resp)

    config_interface.send_message('$PQTMVERNO,SUB')
    resp = config_interface.wait_for_message('$PQTMVERNO,SUB')
    if resp is None:
        logger.error('Response timed out after %d seconds.' % RESPONSE_TIMEOUT)
        return False
    else:
        logger.info(resp)
        return True


def request_reset(config_interface: DeviceInterface, args):
    if args.type == 'factory':
        logger.info('Issuing factory reset request.')
        mask = ResetRequest.FACTORY_RESET
    elif args.type == 'hot':
        logger.info('Issuing hot start request.')
        mask = ResetRequest.HOT_START
    elif args.type == 'warm':
        logger.info('Issuing warm start request.')
        mask = ResetRequest.WARM_START
    elif args.type == 'cold':
        logger.info('Issuing cold start request.')
        mask = ResetRequest.COLD_START
    elif args.type == 'reboot':
        logger.info('Issuing reboot request.')
        mask = ResetRequest.REBOOT_NAVIGATION_PROCESSOR
    elif args.type == 'calibration':
        logger.info('Issuing calibration reset request.')
        mask = (ResetRequest.RESET_CALIBRATION_DATA |
                ResetRequest.RESET_NAVIGATION_ENGINE_DATA)
    elif args.type == 'config':
        logger.info('Issuing user configuration reset request. This may reset the device calibration.')
        mask = ResetRequest.RESET_CONFIG
    elif args.type == 'nav_engine':
        logger.info('Issuing navigation engine state reset request.')
        mask = ResetRequest.RESET_NAVIGATION_ENGINE_DATA
    elif args.type == 'position':
        logger.info('Issuing position reset request.')
        mask = ResetRequest.RESET_POSITION_DATA
    else:
        logger.error('Unrecognized reset type.')
        return False

    config_interface.send_message(ResetRequest(mask))

    resp = config_interface.wait_for_message(CommandResponseMessage.MESSAGE_TYPE)
    if resp is None:
        logger.error('Response timed out after %d seconds.' % RESPONSE_TIMEOUT)
        return False
    elif resp.response != Response.OK:
        logger.error('Reset command rejected: %s (%d)' % (str(resp.response), int(resp.response)))
        return False
    else:
        logger.info('Reset successful.')
        return True


def request_shutdown(config_interface: DeviceInterface, args):
    config_interface.send_message(ShutdownRequest())

    resp = config_interface.wait_for_message(CommandResponseMessage.MESSAGE_TYPE)
    if resp is None:
        logger.error('Response timed out after %d seconds.' % RESPONSE_TIMEOUT)
        return False
    elif resp.response != Response.OK:
        logger.error('Shutdown command rejected: %s (%d)' % (str(resp.response), int(resp.response)))
        return False
    else:
        logger.info('Reset successful.')
        return True


def request_export(config_interface: DeviceInterface, args):
    data_types = _data_types_map[args.type]

    # Query device for version to save with metadata.
    config_interface.send_message(MessageRequest(MessageType.VERSION_INFO))
    version_resp = config_interface.wait_for_message(VersionInfoMessage.MESSAGE_TYPE)
    if version_resp is None:
        logger.error('Response timed out after %d seconds.' % RESPONSE_TIMEOUT)
        return False
    assert isinstance(version_resp, VersionInfoMessage)

    export_file = args.export_file
    if export_file is None:
        timestr = datetime.now().strftime("%y%m%d_%H%M%S")
        device_type = '-'.join(version_resp.engine_version_str.split('-')[:2])
        export_file = device_type + '.' + timestr + '.p1nvm'

    create_exported_data(export_file, version_resp)

    for data_type in data_types:
        export_msg = ExportDataMessage(data_type)
        if data_type == DataType.USER_CONFIG and args.export_saved_config:
            export_msg.source = ConfigurationSource.SAVED

        while True:
            config_interface.send_message(export_msg)
            data_msg = config_interface.wait_for_message(MessageType.PLATFORM_STORAGE_DATA)
            if data_msg is None or not isinstance(data_msg, PlatformStorageDataMessage):
                logger.error('Device did not respond to export request.')
                return False
            # Check the response has the expected data type to avoid handling the periodic PlatformStorageDataMessage
            # output.
            if data_type == data_msg.data_type:
                break

        if data_msg.response == Response.NO_DATA_STORED:
            logger.info('No %s data store on the device.', data_type.name)
        elif data_msg.response == Response.DATA_CORRUPTED:
            logger.warning('%s data is corrupt.', data_type.name)
        elif data_msg.response != Response.OK:
            logger.warning('Export %s error: "%s"', data_type.name, data_msg.response.name)
            return False

        add_to_exported_data(export_file, data_msg)

    logger.info('Exports successful.')
    return True


def request_import(config_interface: DeviceInterface, args):
    data_types = _data_types_map[args.type]

    if not is_export_valid(args.file):
        logger.error('%s is not a valid data export.', args.file)
        return False

    import_cmds = load_saved_data(args.file, data_types)

    if len(import_cmds) == 0:
        logger.error('None of the data types %s found in %s.', [t.name for t in data_types], args.file)
        return False

    actions = []
    for import_cmd, validity in import_cmds:
        actions.append(f'\t{import_cmd.data_type.name}: ' + {
            Response.NO_DATA_STORED: 'Exported data was empty. Will be cleared on device.',
            Response.OK: 'Overriding device with loaded value.',
            Response.DATA_CORRUPTED: 'Skipping corrupted data.'
        }[validity])

    logger.info('The following stored data on the device will be modified by the import:\n%s', '\n'.join(actions))

    if args.dry_run:
        return True

    if not args.force:
        user_input = input('Continue? (Y/n): ')
        if user_input.lower().startswith('n'):
            logger.warning('Halting import operation.')
            return False

    for import_cmd, validity in import_cmds:
        if validity == Response.DATA_CORRUPTED:
            continue

        sources = [ConfigurationSource.ACTIVE]

        if import_cmd.data_type == DataType.USER_CONFIG and not args.dont_save_config:
            sources.append(ConfigurationSource.SAVED)

        for source in sources:
            logger.info('Updating %s %s data on device.', source.name.lower(), import_cmd.data_type.name)
            import_cmd.source = source

            # Clear the input buffer to avoid missing the response.
            config_interface.serial_out.reset_input_buffer()
            config_interface.send_message(import_cmd)

            resp = config_interface.wait_for_message(CommandResponseMessage.MESSAGE_TYPE)
            if resp is None or not isinstance(resp, CommandResponseMessage):
                logger.error('Device did not respond to import request.')
                return False
            elif resp.response != Response.OK:
                logger.error('Import command rejected: %s (%d)' % (str(resp.response), int(resp.response)))
                return False

    logger.info('Imports successful.')
    return True


def request_fault(config_interface: DeviceInterface, args):
    expect_response = True
    if args.fault == 'clear':
        logger.info('Sending a clear faults command.')
        payload = FaultControlMessage.ClearAll()
    elif args.fault == 'crash':
        logger.info('Sending a crash fault command.')
        payload = FaultControlMessage.Crash()
        expect_response = False
    elif args.fault == 'fatal':
        logger.info('Sending a fatal error fault command.')
        payload = FaultControlMessage.FatalError()
        expect_response = False
    elif args.fault == 'cocom':
        logger.info('Sending a COCOM fault command.')
        payload = FaultControlMessage.CoComLimit(_cocom_type[args.type])
    elif args.fault == 'gnss':
        logger.info('Sending a GNSS fault command.')
        payload = FaultControlMessage.EnableGNSS(args.enabled)
    elif args.fault == 'blackout':
        logger.info('Sending a blackout region fault command.')
        payload = FaultControlMessage.RegionBlackout(args.enabled)
    else:
        logger.error('Unrecognized fault type.')
        return False

    config_interface.send_message(FaultControlMessage(payload))

    if expect_response:
        resp = config_interface.wait_for_message(CommandResponseMessage.MESSAGE_TYPE)
        if resp is None:
            logger.error('Response timed out after %d seconds.' % RESPONSE_TIMEOUT)
            return False
        elif resp.response != Response.OK:
            logger.error('Fault command rejected: %s (%d)' % (str(resp.response), int(resp.response)))
            return False
        else:
            logger.info('Command sent successfully.')
            return True
    else:
        logger.info('Command sent successfully (no response expected).')
        return True


def main():
    execute_command = os.path.basename(sys.executable)

    parser = ArgumentParser(
        usage='%s COMMAND [OPTIONS]...' % execute_command,
        description='Update device lever arm configurations.',
        epilog="""\
EXAMPLE USAGE

Reset the device calibration and state:
    config_tool.py reset calibration

Read the active lever arm values.
    config_tool.py read

Apply changes to the GNSS and device (IMU) lever arms, then save the changes
to persistent storage.
    config_tool.py apply gnss 0 0.4 1
    config_tool.py apply device 0 2.1 1
    config_tool.py save

Change the output lever arm, but do not save it to persistent storage. The
device will revert to the previous value after a power cycle.
    config_tool.py apply output 0 0.4 1

Change the output lever arm, and save the new value immediately.
    config_tool.py apply --save output 0 0.4 1

Change the UART1 baud rate, and save the new value immediately.
    config_tool.py apply --save uart1_baud 115200

Change the UART1 output rate to 1 Hz for all messages (change not saved).
    config_tool.py apply uart1_message_rate all 1s

Read the current configuration for the NMEA GGA message rate on UART2.
    config_tool.py read uart2_message_rate nmea gga

Disable GNSS for dead reckoning performance testing.
    config_tool.py fault gnss off

Export the device's user configuration to a local file.
    config_tool.py export user_config
""")

    parser.add_argument('--device-port', default="auto",
                        help="The serial device to use when communicating with the device.  If 'auto', the serial port "
                             "will be located automatically by searching for a connected device.")
    parser.add_argument('--device-baud', type=int, default=460800,
                        help="The baud rate used by the device serial port (--device-port).")
    parser.add_argument('-v', '--verbose', action='count', default=0,
                        help="Print verbose/trace debugging messages. May be specified multiple times to increase "
                             "verbosity.")

    command_subparsers = parser.add_subparsers(
        dest='command',
        help='The command to be run.')

    # config_tool.py apply
    help = 'Apply a config parameter value.'
    apply_parser = command_subparsers.add_parser(
        'apply',
        help=help,
        description=help)

    apply_parser.add_argument(
        '-s', '--save', action=ExtendedBooleanAction,
        help="If set, the configuration will be saved after applying this value.")

    param_parser = apply_parser.add_subparsers(dest='param', help="The name of the parameter to be modified.")

    # config_tool.py apply -- lever arms and device orientation
    help = 'The GNSS antenna lever arm (in meters).'
    gnss_parser = param_parser.add_parser('gnss', help=help, description=help)
    gnss_parser.add_argument('x', type=float, help='The X offset with respect to the vehicle body (in meters).')
    gnss_parser.add_argument('y', type=float, help='The Y offset with respect to the vehicle body (in meters).')
    gnss_parser.add_argument('z', type=float, help='The Z offset with respect to the vehicle body (in meters).')

    help = 'The device (IMU) lever arm (in meters).'
    gnss_parser = param_parser.add_parser('device', help=help, description=help)
    gnss_parser.add_argument('x', type=float, help='The X offset with respect to the vehicle body (in meters).')
    gnss_parser.add_argument('y', type=float, help='The Y offset with respect to the vehicle body (in meters).')
    gnss_parser.add_argument('z', type=float, help='The Z offset with respect to the vehicle body (in meters).')

    help = 'The location of the desired output location with respect to the vehicle body frame.'
    gnss_parser = param_parser.add_parser('output', help=help, description=help)
    gnss_parser.add_argument('x', type=float, help='The X offset with respect to the vehicle body (in meters).')
    gnss_parser.add_argument('y', type=float, help='The Y offset with respect to the vehicle body (in meters).')
    gnss_parser.add_argument('z', type=float, help='The Z offset with respect to the vehicle body (in meters).')

    help = 'The orientation of the device (IMU) within the vehicle, specified using the directions of the device +X ' \
           'and +Z axes relative to the vehicle body axes (+X = forward, +Y = left, +Z = up).'
    orientation_parser = param_parser.add_parser('orientation', help=help, description=help)
    orientation_parser.add_argument('x', choices=_orientation_map.keys(),
                                    help='The orientation of the IMU +X axis relative to the vehicle body axes.')
    orientation_parser.add_argument('z', choices=_orientation_map.keys(), nargs='?', default='up',
                                    help='The orientation of the IMU +Z axis relative to the vehicle body axes.')

    # config_tool.py apply -- vehicle details
    help = """\
Information including vehicle model and dimensions.

Any omitted arguments will retain their previous values."""
    vehicle_details_parser = param_parser.add_parser('vehicle_details', help=help, description=help)
    vehicle_details_parser.add_argument('--vehicle-model', '--model', choices=_vehicle_model_map.keys(),
                                        help='Specify the type of vehicle (used to enable CAN message decoding).')
    vehicle_details_parser.add_argument('--wheelbase', type=float,
                                        help='The distance between the front axle and rear axle (in meters).')
    vehicle_details_parser.add_argument('--front-track-width', '--front-track', type=float,
                                        help='The distance between the two front wheels (in meters).')
    vehicle_details_parser.add_argument('--rear-track-width', '--rear-track', type=float,
                                        help='The distance between the two rear wheels (in meters).')

    # config_tool.py apply -- wheel speed configuration
    wheel_config_parser = param_parser.add_parser(
        'wheel_config',
        help='Configure software wheel speed/tick support.',
        description="""\
Specify the vehicle/wheel speed measurement configuration settings.""")
    wheel_config_parser.add_argument('--wheel-sensor-type', choices=_wheel_sensor_type_map.keys(),
                                     help='The type of vehicle/wheel speed measurements produced by the vehicle.')
    wheel_config_parser.add_argument('--applied-speed-type', choices=_applied_speed_type_map.keys(),
                                     help='The type of vehicle/wheel speed measurements to be applied.')
    wheel_config_parser.add_argument('--steering-type', choices=_steering_type_map.keys(),
                                     help='Indication of which of the vehicle\'s wheels are steered.')
    wheel_config_parser.add_argument('--wheel-update-interval', type=float,
                                     help='The nominal rate at which wheel speed measurements will be provided (in '
                                          'seconds).')
    wheel_config_parser.add_argument('--wheel-tick-interval', type=float,
                                     help='The nominal rate at which wheel tick measurements will be provided (in '
                                          'seconds).')
    wheel_config_parser.add_argument('--steering-ratio', type=float,
                                     help='Ratio between angle of the steering wheel and the angle of the wheels on '
                                          'the ground.')
    wheel_config_parser.add_argument('--meters-per-tick', '--wheel-ticks-to-m', type=float,
                                     help='The scale factor to convert from wheel encoder ticks to distance (in '
                                          'meters/tick).')
    wheel_config_parser.add_argument('--wheel-tick-max-value', type=int,
                                     help='The maximum value (inclusive) before the wheel tick measurement will roll '
                                          'over.')
    wheel_config_parser.add_argument('--wheel-ticks-signed', action=ExtendedBooleanAction,
                                     help='True if the reported wheel tick measurements should be interpreted as '
                                          'signed integers, or false if they should be interpreted as unsigned '
                                          'integers.')
    wheel_config_parser.add_argument('--wheel-ticks-always-increase', action=ExtendedBooleanAction,
                                     help='True if the wheel tick measurements increase by a positive amount when '
                                          'driving forward or backward. False if wheel tick measurements decrease when '
                                          'driving backward.')

    hardware_tick_config_parser = param_parser.add_parser(
        'hardware_tick_config',
        help='Configure hardware wheel encoder tick support.',
        description="""\
Specify the wheel encoder sensor configuration details.""")
    hardware_tick_config_parser.add_argument('--tick-mode', help='Indication of whether ticks are being measured.',
                                             choices=_tick_mode_map.keys())
    hardware_tick_config_parser.add_argument('--tick-direction', help='Directions in which ticks increase.',
                                             choices=_tick_direction_map.keys())
    hardware_tick_config_parser.add_argument('--meters-per-tick', '--wheel-ticks-to-m', type=float,
                                             help='The scale factor to convert from wheel encoder ticks to distance '
                                                  '(in meters/tick).')

    # config_tool.py apply -- output interface/stream control
    uart_1_baud_parser = param_parser.add_parser('uart1_baud',
                                                 help='Configure the UART1 serial baud rate.')
    uart_1_baud_parser.add_argument('baud_rate', type=float,
                                    help='The desired baud rate (in bits/second).')

    uart_2_baud_parser = param_parser.add_parser('uart2_baud',
                                                 help='Configure the UART2 serial baud rate.')
    uart_2_baud_parser.add_argument('baud_rate', type=float,
                                    help='The desired baud rate (in bits/second).')

    uart_1_diagnostics_enabled_parser = param_parser.add_parser(
        'uart1_diagnostics_enabled',
        help='Enable/disable output for all diagnostics messages on UART1.')
    uart_1_diagnostics_enabled_parser.add_argument(
        'enabled', action=ExtendedBooleanAction,
        help='Enable/disable diagnostic messages.')

    uart_2_diagnostics_enabled_parser = param_parser.add_parser(
        'uart2_diagnostics_enabled',
        help='Enable/disable output for all diagnostics messages on UART1.')
    uart_2_diagnostics_enabled_parser.add_argument(
        'enabled', action=ExtendedBooleanAction,
        help='Enable/disable diagnostic messages.')

    watchdog_enabled_parser = param_parser.add_parser(
        'watchdog_enabled',
        help='Enable/disable the watchdog timer reset after fatal errors.')
    watchdog_enabled_parser.add_argument(
        'enabled', action=ExtendedBooleanAction,
        help='Enable/disable the watchdog timer reset after fatal errors.')

    for uart_id in [1, 2]:
        supported_fe_messages = '\n'.join([f'  - {m} ({int(m)})' for m in MessageType if m.name != 'INVALID'])
        supported_nmea_messages = '\n'.join([f'  - {m}' for m in NmeaMessageType if m.name != 'INVALID'])

        message_rate_description = f'''\
Configure the output rate for a specified message type on serial UART{uart_id}.

When setting parameters for individual message types, you must specify the
protocol (FusionEngine, NMEA, RTCM) and message ID. Protocol and message names
are not case sensitive. For FusionEngine messages, you may specify either a
numeric message ID or a partial or complete message name (e.g., IMU or
IMUMeasurement).

Example usage:
  config_tool.py apply uart{uart_id}_message_rate nmea gga on_change
  config_tool.py apply uart{uart_id}_message_rate fe imu on_change
  config_tool.py apply uart{uart_id}_message_rate fe 11000 on_change'''
        message_output_rate_parser = param_parser.add_parser(
            f'uart{uart_id}_message_rate',
            help=f'Configure the output rate for a specified message type on serial UART{uart_id}.',
            description=message_rate_description,
            epilog=f'''\
FusionEngine message types:
{supported_fe_messages}

NMEA message types:
{supported_nmea_messages}''')
        message_output_rate_parser.add_argument('protocol', metavar="PROTOCOL",
                                                help='The message protocol name:\n'
                                                '  all - All messages on all protocols for an interface\n'
                                                '  fe, fusion_engine - Point One FusionEngine protocol\n'
                                                '  nmea - NMEA-0183\n'
                                                '  rtcm - RTCM 10403.3')
        message_output_rate_parser.add_argument('message_id', metavar="ID",
                                                help='The message type (name) or ID (integer). '
                                                'Alternatively, use "all" as a wildcard for all messages on the '
                                                'specified protocol.')
        message_output_rate_parser.add_argument('rate', metavar="RATE",
                                                help='The desired message rate:%s' %
                                                ''.join(['\n  %s' % n for n in _rate_map]))
        message_output_rate_parser.add_argument('-f', '--include-disabled', action=ExtendedBooleanAction,
                                                help='When setting multiple messages, include the ones that are off.')

    # config_tool.py read
    help = "Read the device's active settings and print the response."
    read_parser = command_subparsers.add_parser(
        'read',
        help=help,
        description="""\
%s

If no parameter name is specified, query the entire device configuration.

When reading the uartN_message_rate parameter, you must specify the protocol
(FusionEngine, NMEA, RTCM) and message ID. Protocol and message names are not
case sensitive. For FusionEngine messages, you may specify either a numeric
message ID or a partial or complete message name (e.g., IMU or IMUMeasurement).

For example:
  config_tool.py read uart1_message_rate nmea gga
  config_tool.py read uart1_message_rate fe imu
  config_tool.py read uart1_message_rate fe 11000
""" % help)

    read_parser.add_argument(
        '-t', '--type', metavar='TYPE', choices=['active', 'saved'], default='active',
        help="The type of settings to be queried: active, saved")

    param_names = list(PARAM_DEFINITION.keys())
    param_names.remove("uart1_message_rate")
    param_names.remove("uart2_message_rate")
    read_parser.add_argument(
        'param', nargs='*',
        help="The name of the parameter to be read. If omitted, read all parameter values. Available "
             "parameter names:" + "".join(["\n  %s" % n for n in param_names]))

    # config_tool.py fault
    help = 'Apply system fault controls.'
    fault_parser = command_subparsers.add_parser(
        'fault',
        help=help,
        description=help)

    type_parser = fault_parser.add_subparsers(dest='fault', help="The type of fault to be applied.")

    crash_parser = type_parser.add_parser(
        'clear',
        help='Clear existing faults.')

    crash_parser = type_parser.add_parser(
        'crash',
        help='Force the device to crash.')

    fatal_parser = type_parser.add_parser(
        'fatal',
        help='Force the device to exhibit a fatal error.')

    cocom_parser = type_parser.add_parser(
        'cocom',
        help='Simulate a COCOM limit.')
    choices = list(_cocom_type.keys())
    cocom_parser.add_argument(
        'type', metavar='TYPE',
        choices=choices,
        default='acceleration',
        help="The type of COCOM limit to be simulated: %s." % ', '.join(choices))

    gnss_parser = type_parser.add_parser(
        'gnss',
        help='Enable/disable use of GNSS measurements.')
    gnss_parser.add_argument(
        'enabled', action=ExtendedBooleanAction,
        help='Enable/disable GNSS measurements.')

    blackout_parser = type_parser.add_parser(
        'blackout',
        help='Enable/disable applying a simulated blackout region.')
    blackout_parser.add_argument(
        'enabled', action=ExtendedBooleanAction,
        help='Enable/disable simulated blackout region.')

    # config_tool.py reset
    help = 'Issue a device reset request.'
    reset_parser = command_subparsers.add_parser(
        'reset',
        help=help,
        description=help)

    choices = ['factory', 'hot', 'warm', 'cold', 'calibration', 'config', 'nav_engine', 'position', 'reboot']
    reset_parser.add_argument(
        'type', metavar='TYPE',
        choices=choices,
        default='cold',
        help="The type of reset to be performed: %s" % ', '.join(choices))

    # config_tool.py export
    help = 'Export data from the device to a local file.'
    export_parser = command_subparsers.add_parser(
        'export',
        help=help,
        description=help)

    export_parser.add_argument(
        "--export-file", default=None,
        help='The file name to save data exported from the device to.')
    export_parser.add_argument(
        '--type',
        choices=_data_types_map.keys(),
        default='all',
        help="The type of data to export to a local file: %s" % ', '.join(_data_types_map.keys()))
    export_parser.add_argument(
        '--export-saved-config',
        action=ExtendedBooleanAction,
        help="When exporting the user_config, export the saved values instead of the active values.")

    # config_tool.py import
    help = 'Import data from a local file to the device.'
    import_parser = command_subparsers.add_parser(
        'import',
        help=help,
        description=help)

    import_parser.add_argument(
        '--dont-save-config', action=ExtendedBooleanAction,
        help="If set, the user_config data will not be saved after importing.")
    import_parser.add_argument(
        '--dry-run', action=ExtendedBooleanAction,
        help="If set, print the actions that the import would take, but don't modify the device.")
    import_parser.add_argument(
        '-f', '--force', action=ExtendedBooleanAction,
        help="If set, the user will not be prompted to confirm any actions.")
    import_parser.add_argument(
        '--type',
        choices=_data_types_map.keys(),
        default='all',
        help="The type of data to send to the device: %s" % ', '.join(_data_types_map.keys()))
    import_parser.add_argument(
        'file', metavar='FILE',
        help="The file containing data to send to the device.")

    # config_tool.py export_file_info
    help = 'List the contents of an export file.'
    export_file_info_parser = command_subparsers.add_parser(
        'export_file_info',
        help=help,
        description=help)

    export_file_info_parser.add_argument(
        'file', metavar='FILE',
        help="The file containing the exported data.")

    # config_tool.py shutdown
    help = 'Issue a device shutdown request.'
    shutdown_parser = command_subparsers.add_parser(
        'shutdown',
        help=help,
        description=help)

    # config_tool.py save
    help = 'Save the active config so the values to persist through power cycle.'
    save_parser = command_subparsers.add_parser(
        'save',
        help=help,
        description=help)

    # config_tool.py version
    help = 'Query the device version information.'
    version_parser = command_subparsers.add_parser(
        'version',
        help=help,
        description=help)

    version_parser.add_argument(
        '-t', '--type', metavar='TYPE', choices=['fusion_engine', 'nmea'], default='fusion_engine',
        help="The type of version message to be queried: fusion_engine, nmea")

    args = parser.parse_known_args()
    args = parser.parse_args(args[1], args[0])

    if args.verbose == 0:
        logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)
    else:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            stream=sys.stdout)
        logger.setLevel(logging.DEBUG)
        if args.verbose > 1:
            logging.getLogger('point_one.fusion_engine.parsers.decoder').setLevel(logging.DEBUG)
        elif args.verbose > 2:
            logging.getLogger('point_one.fusion_engine.parsers.decoder').setLevel(logging.TRACE)

    if args.command is None:
        logger.error('No command specified.\n')
        parser.print_help()
        sys.exit(0)

    # Note: We intentionally use the Enhanced port here, whereas p1_runner uses Standard port. That way users can
    # issue configuration requests while the device is active and p1_runner is operating. If the user explicitly
    # sets --device-port, we'll use that port regardless of type.
    device_port = find_serial_device(port_name=args.device_port, port_type=PortType.ENHANCED)
    logger.info('Connecting to device using serial port %s.' % device_port)

    with serial.Serial(port=device_port, baudrate=args.device_baud, timeout=SERIAL_TIMEOUT) as device_serial:
        config_interface = DeviceInterface(device_serial, device_serial)

        passed = False

        if args.command == "read":
            passed = read_config(config_interface, args)
        elif args.command == "apply":
            passed = apply_config(config_interface, args)
        elif args.command == "save":
            passed = save_config(config_interface, args)
        elif args.command == "version":
            passed = query_version(config_interface, args)
        elif args.command == "reset":
            passed = request_reset(config_interface, args)
        elif args.command == "shutdown":
            passed = request_shutdown(config_interface, args)
        elif args.command == "fault":
            passed = request_fault(config_interface, args)
        elif args.command == "export":
            passed = request_export(config_interface, args)
        elif args.command == "import":
            passed = request_import(config_interface, args)
        elif args.command == "export_file_info":
            vars(args)['dry_run'] = True
            vars(args)['type'] = "all"
            passed = request_import(config_interface, args)
        else:
            logger.error("Unrecognized command '%s'." % args.command)
            sys.exit(2)

        if passed:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
