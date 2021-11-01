vehicle_fields = {
    'basic': {
        'id': 'id',
        'driver': 'driver',
        'plate': 'plate',
        'temperature_control': 'temperature_control',
        'dangerous_goods': 'dangerous_goods',
        'vehicle_model': {'vehicle_model': ['id', 'name', 'length', 'width', 'height', 'maximum_payload']},
        'location': 'location'

    },
    'detailed': {
        'id': 'id',
        'driver': {'driver': ['id', 'username', 'organization']},
        'plate': 'plate',
        'temperature_control': 'temperature_control',
        'dangerous_goods': 'dangerous_goods',
        'vehicle_model': {'vehicle_model': ['id', 'name', 'length', 'width', 'height', 'maximum_payload']},
        'location': 'location',
        'route': {'route': ['id', {'location': ['id', 'name']}, 'next_route_id']},
    }
}
