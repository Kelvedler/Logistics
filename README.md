# Logistics
* REST API application designed to organize freight shipping, allowing customers to rent an available pallet on a lorry.
* Depending on order dimentions it can either be placed on EUR 1 or EUR 6 pallet. Application is using pallet dimentions to determine whether there is available space on vehicle.
* There are no regular routes. Customers are instead free to either create new one for available vehicle or place an order on existing route.
* New route points are deleted 30 minutes after if there are no paid orders placed on them.
* Currently payment is performed via Paypal.
* To register as a driver person has to be verified by administrator.
* When driver completes route point all related paid orders are archived.
* **For more information about API endpoints, visit https://logistics-rest-api.herokuapp.com**
* Application is build with Django, Django REST Framework, PostgreSQL, Redis. Payment implemented using Paypal. Hosted on Heroku.
