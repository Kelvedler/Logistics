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
        'location': {'id': None, 'name': None, 'city': None},
        'route': {'id': None, 'location': {'id': None, 'name': None, 'city': None}, 'next_route_id': None},
    }
}

order_fields = {
    'basic': {
        'id': None,
        'customer': None,
        'departure_route': None,
        'destination_route': None,
        'departure_district': None,
        'destination_district': None,
        'length': None,
        'width': None,
        'height': None,
        'weight': None,
        'temperature_control': None,
        'dangerous_goods': None,
        'payment': {'id': None, 'payment_method': None, 'payment_id': None, 'completed': None, 'currency_code': None,
                    'amount': None}
    },
    'detailed': {
        'id': None,
        'customer': None,
        'departure_route': {'id': None, 'next_route_id': None, 'location': None, 'vehicle': None},
        'destination_route': {'id': None, 'next_route_id': None, 'location': None, 'vehicle': None},
        'departure_district': {'id': None, 'name': None, 'city': None},
        'destination_district': {'id': None, 'name': None, 'city': None},
        'length': None,
        'width': None,
        'height': None,
        'weight': None,
        'temperature_control': None,
        'dangerous_goods': None,
        'payment': {'id': None, 'payment_method': None, 'payment_id': None, 'completed': None, 'currency_code': None,
                    'amount': None}
    }
}

completed_order_fields = {
    'id': None,
    'completed_at': None,
    'departure': {'id': None, 'name': None, 'city': None},
    'destination': {'id': None, 'name': None, 'city': None},
    'driver': {'id': None, 'username': None, 'organization': None, 'email': None},
    'customer': {'id': None, 'username': None, 'organization': None, 'email': None},
    'payment': {'id': None, 'payment_method': None, 'payment_id': None, 'completed': None, 'currency_code': None,
                'amount': None}
}
