# MQT Bridge API Specification

## Topics

### Status Topics
- [`root_topic`]/v1/[`friendly_name`]/panel/status
- [`root_topic`]/v1/[`friendly_name`]/panel/settings

### State Topics
- [`root_topic`]/v1/[`friendly_name`]/automation/`virtual_node_id`
- [`root_topic`]/v1/[`friendly_name`]/partition/`partition_id`
- [`root_topic`]/v1/[`friendly_name`]/zone/`zone_id`
- [`root_topic`]/v1/[`friendly_name`]/scene/`scene_id`


### Command Topics
- [`root_topic`]/v1/[`friendly_name`]/automation/command
- [`root_topic`]/v1/[`friendly_name`]/partition/command
- [`root_topic`]/v1/[`friendly_name`]/panel/command

## MQTT Behavior
- State topics: QoS 1, retained
- Status topics: QoS 1, retained
- Command topics: QoS 1, not retained

## State Payloads

### Zone State Payload
```json
{
   "id":5,
   "type": "zone",
   "state":{
      "status":"normal"
   },
   "capabilities":{
      "ac":false,
      "battery":true,
      "average_dbm":false,
      "latest_dbm":false,
      "powerg":false,
      "powerg_temperature":false,
      "powerg_light":false,
      "powerg_battery_level":false,
      "powerg_battery_voltage":false
   },
   "attributes":{
      "name":"Panel Glass Break",
      "device_type":"panel_glass_break",
      "partition_id":0,
      "group":"glass_break"
   },
   "timestamp":"2026-04-10T19:28:42.127810Z",
   "version":1
}
```

The following fields will be present in `state` if the corresponding capability is true:
- "average_dbm": -50
- "latest_dbm": -50
- "ac_on": true
- "powerg_battery_level": 75
- "powerg_battery_voltage": 4.5
- "powerg_light": 0.5
- "powerg_temperature": 69.5

`status`: in -> ['active', 'activated', 'alarmed', 'arm_away', 'arm_stay', 'auxiliary_emergency', 'bell_trouble', 'closed', 'connected', 'disarm', 'failure', 'fire_emergency', 'open', 'occupied', 'police_emergency', 'inactive', 'idle', 'normal', 'not_networked', 'unreachable', 'silent_police_emergency', 'silent_auxiliary_emergency', 'tampered', 'synchronizing', 'disconnected', 'trouble', 'vacant']

`device_type` in -> ['auxiliary_pendant', 'bluetooth', 'co_detector', 'doorbell', 'door_window', 'door_window_m', 'external_siren', 'freeze', 'glass_break', 'heat', 'high_temperature', 'img_sensor', 'key_fob', 'keypad', 'motion', 'occupancy', 'panel_glass_break', 'panel_motion', 'panic', 'powerg_siren', 'siren', 'shock', 'smoke_detector', 'smoke_m', 'takeover_module', 'tamper', 'temperature', 'tilt', 'translator', 'unknown', 'water', 'zwave_siren']

`group` in -> ['co', 'delayer_reporting_safety', 'fixed_intrusion', 'fixed_silent', 'freeze', 'freeze_non_reporting', 'mobile_intrusion', 'mobile_silent', 'fixed_auxiliary', 'fixed_silent_auxiliary', 'local_safety_sensor', 'high_temperature_non_reporting', 'mobile_auxiliary', 'mobile_silent_auxiliary', 'safety_motion', 'glass_break', 'glass_break_away_only', 'smoke_heat', 'tamper_zone', 'shock', 'entry_exit_normal_delay', 'entry_exit_long_delay', 'instant_perimeter_dw', 'instant_interior_door', 'away_instant_follower_delay', 'reporting_safety_sensor', 'away_instant_motion', 'stay_instant_motion', 'stay_delay_motion', 'away_delay_motion', 'water', 'water_non_reporting']

### Partition State Payload
```json
{
   "id":0,
   "type": "partition",
   "state":{
      "status":"disarm",
      "alarm_state":"none",
      "alarm_array":[],
      "status_changed_time":"2025-08-25T16:58:14.939000Z",
      "entry_delays":true,
      "exit_sounds":true
   },
   "attributes":{
      "name":"systemo"
   },
   "timestamp":"2026-04-10T20:04:48.937857Z",
   "version":1
}
```

`status` in -> ['arm_stay', 'arm_away', 'arm_night', 'disarm', 'arm_away_exit_delay', 'arm_stay_exit_delay', 'arm_night_exit_delay', 'unknown']

`alarm_state` in -> ['none', 'delay', 'alarm', 'unknown']

`alarm_type` in -> ['police_emergency', 'fire_emergency', 'gaz_co', 'auxiliary_emergency', 'silent_auxiliary_emergency', 'silent_police_emergency', 'water_sensor']

### Automation Device State Payload
```json
{
   "id":6,
   "type": "automation_device",
   "state":{
      "services":[
         {
            "service_type":"LightService",
            "state":{
               "is_on":true,
               "level":1
            },
            "attributes":{
               "endpoint":0
            },
            "capabilities":{
               "supports_level":true
            }
         },
         {
            "service_type":"StatusService",
            "state":{
               "is_malfunctioning":false
            },
            "attributes":{
               "endpoint":0
            },
            "capabilities":{
               "supports_status":true
            }
         },
         {
            "service_type":"BatteryService",
            "state":{
               "is_disabled":true
            },
            "attributes":{
               "endpoint":0
            },
            "capabilities":{
               "supports_battery_level":false,
               "supports_battery_low":false
            }
         }
      ]
   },
   "attributes":{
      "protocol":"zwave",
      "name":"Off",
      "device_type":"light"
   },
   "timestamp":"2026-04-10T20:06:50.682681Z",
   "version":1
}
```

`protocol` in -> ['adc', 'powerg', 'zwave', 'unknown']

`service_type` in -> ['BatteryService', 'CoverService', 'LightService', 'MeterService', 'SensorService', 'SirenService', 'StatusService', 'ThermostatService', 'ValveService']

`device_type` in -> ['light', 'door_lock', 'garage_door', 'external_siren', 'water_valve', 'thermostat', 'thermometer', 'energy_clamp', 'repeater', 'smart_socket']

### Scene State Payload
```json
{
   "id":1,
   "attributes":{
      "name":"Home",
      "icon":"94",
      "color":"635473"
   },
   "timestamp":"2026-04-12T02:39:36.829622Z",
   "version":1
}
```

## Commands

### Partition Commands

DISARM COMMAND:
```json
{
  "command": "DISARM",
  "command_id": "46707d92-02f4-4817-8116-a4c3b23e6266",
  "response_topic": "per_client_unique_response_topic",
  "partition_id": 0,
  "user_code": "1234",
  "silent_disarm": false,
  "response_topic": "per_client_unique_response_topic",
  "version": 1
}
```

ARM_AWAY COMMAND:
```json
{
  "command": "ARM_AWAY",
  "command_id": "46707d92-02f4-4817-8116-a4c3b23e6266",
  "response_topic": "per_client_unique_response_topic",
  "partition_id": 0,
  "user_code": "1234",
  "exit_sounds":false,
  "version": 1
}
```

ARM_STAY COMMAND
```json
{
  "command": "ARM_STAY",
  "command_id": "46707d92-02f4-4817-8116-a4c3b23e6266",
  "response_topic": "per_client_unique_response_topic",
  "partition_id": 0,
  "user_code": "1234",
  "exit_delay": true,
  "exit_sounds":false,
  "instant_arm": false,
  "version": 1
}
```

ARM_NIGHT COMMAND:
```json
{
  "command": "ARM_NIGHT",
  "command_id": "46707d92-02f4-4817-8116-a4c3b23e6266",
  "response_topic": "per_client_unique_response_topic",
  "partition_id": 0,
  "user_code": "1234",
  "exit_sounds":false,
  "version": 1
}
```

TRIGGER_POLICE_EMERGENCY COMMAND:
```json
{
  "command": "TRIGGER_POLICE_EMERGENCY",
  "command_id": "46707d92-02f4-4817-8116-a4c3b23e6266",
  "response_topic": "per_client_unique_response_topic",
  "partition_id": 0,
  "version": 1
}

TRIGGER_POLICE_EMERGENCY_SILENT COMMAND:
```json
{
  "command": "TRIGGER_POLICE_EMERGENCY_SILENT",
  "command_id": "46707d92-02f4-4817-8116-a4c3b23e6266",
  "response_topic": "per_client_unique_response_topic",
  "partition_id": 0,
  "version": 1
}

TRIGGER_AUXILIARY_EMERGENCY COMMAND:
```json
{
  "command": "TRIGGER_AUXILIARY_EMERGENCY",
  "command_id": "46707d92-02f4-4817-8116-a4c3b23e6266",
  "response_topic": "per_client_unique_response_topic",
  "partition_id": 0,
  "version": 1
}

TRIGGER_AUXILIARY_EMERGENCY_SILENT COMMAND:
```json
{
  "command": "TRIGGER_AUXILIARY_EMERGENCY_SILENT",
  "command_id": "46707d92-02f4-4817-8116-a4c3b23e6266",
  "response_topic": "per_client_unique_response_topic",
  "partition_id": 0,
  "response_topic": "per_client_unique_response_topic",
  "version": 1
}

TRIGGER_FIRE_EMERGENCY COMMAND:
```json
{
  "command": "TRIGGER_FIRE_EMERGENCY",
  "command_id": "46707d92-02f4-4817-8116-a4c3b23e6266",
  "response_topic": "per_client_unique_response_topic",
  "partition_id": 0,
  "version": 1
}

Success response:
```json
{
   "success":true,
   "command_id":"46707d92-02f4-4817-8116-a4c3b23e6266"
}
 ```

Error response:
```json
{
   "success":false,
   "error":"invalid_partition_id",
   "error_msg":"Automation Command - Missing level for light_level command",
   "command_id":"46707d92-02f4-4817-8116-a4c3b23e6266"
}
 ```

 `error` in -> ['invalid_partition_id', 'invalid_partition_command']


### Automation Device Commands

```json
{
  "command": "LIGHT_OFF",
  "command_id": "46707d92-02f4-4817-8116-a4c3b23e6266",
  "response_topic": "per_client_unique_response_topic",
  "virtual_node_id": 8,
  "endpoint": 0,
  "version": 1
}
```

Success response:
```json
{
   "success":true,
   "command_id":"46707d92-02f4-4817-8116-a4c3b23e6266"
}
 ```

Error response:
```json
{
   "success":false,
   "error":"light_level_missing",
   "error_msg":"Automation Command - Missing level for light_level command",
   "command_id":"46707d92-02f4-4817-8116-a4c3b23e6266"
}
 ```

`command` in ->  [
  "LIGHT_ON",
  "LIGHT_OFF",
  "LIGHT_LEVEL",
  "LOCK",
  "UNLOCK",
  "COVER_OPEN",
  "COVER_CLOSE",
  "COVER_POSITION",
  "SIREN_ON",
  "SIREN_OFF",
  "VALVE_OPEN",
  "VALVE_CLOSE",
  "VALVE_STOP",
  "VALVE_POSITION",
  "THERMOSTAT_MODE",
  "THERMOSTAT_FAN_MODE",
  "THERMOSTAT_HEAT",
  "THERMOSTAT_COOL"
]

`error` in -> ['invalid_automation_command', 'light_level_missing', 'cover_position_missing', 'valve_position_missing', 'operation_not_supported_by_service', 'endpoint_missing', 'automation_device_not_found', 'service_not_found']

### Panel Commands

PANEL_SPEAK COMMAND:
```json
{
  "command": "PANEL_SPEAK",
  "command_id": "46707d92-02f4-4817-8116-a4c3b23e6266",
  "response_topic": "per_client_unique_response_topic",
  "message": "Test Message",
  "version": 1
}
```

EXECUTE_SCENE COMMAND:
```json
{
  "command": "EXECUTE_SCENE",
  "command_id": "46707d92-02f4-4817-8116-a4c3b23e6266",
  "response_topic": "per_client_unique_response_topic",
  "scene_id": "1",
  "version": 1
}
```

Success response:
```json
{
   "success":true,
   "command_id":"46707d92-02f4-4817-8116-a4c3b23e6266"
}
 ```

Error response:
```json
{
   "success":false,
   "error":"invalid_scene_id",
   "command_id":"46707d92-02f4-4817-8116-a4c3b23e6266"
}
 ```

`error` in -> ['panel_speak_message_missing', 'invalid_scene_id']

