country_fields = {
    'id': None,
    'name': None
}

city_fields = {
    'id': None,
    'name': None,
    'country': None
}

district_fields = {
    'id': None,
    'name': None,
    'city': None
}

vehicle_fields = {
    'basic': {
        'id': None,
        'driver': None,
        'plate': None,
        'temperature_control': None,
        'dangerous_goods': None,
        'vehicle_model': {'id': None, 'name': None, 'length': None, 'width': None, 'height': None, 'maximum_payload': None},
        'location': None

    },
    'detailed': {
        'id': None,
        'driver': {'id': None, 'username': None, 'organization': None},
        'plate': None,
        'temperature_control': None,
        'dangerous_goods': None,
        'vehicle_model': {'id': None, 'name': None, 'length': None, 'width': None, 'height': None, 'maximum_payload': None},
        'location': None,
        'route': {'id': None, 'location': {'id': None, 'name': None}, 'next_route_id': None},
    }
}

order_fields = {
    'id': None,
    'customer': None,
    'departure': None,
    'destination': None,
    'length': None,
    'width': None,
    'height': None,
    'weight': None,
    'temperature_control': None,
    'dangerous_goods': None,
}
