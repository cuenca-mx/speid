## SPEI Daemon 

[![Build Status](https://travis-ci.com/cuenca-mx/speid.svg?branch=master)](https://travis-ci.com/cuenca-mx/speid)

Envía y recibe órdenes SPEI. Utilizando RabbitMQ y Postgress para almacenar 
los datos.

### Requerimientos

- Python v3 o superior.
- Postgres
- RabbitMQ

### Instalación

Primero hay que declarar las variables de ambiente que se encuentran en
env.template.

Ejecutar la migración de base de datos:

```
flask docker create_db
flask db upgrade
flask docker drop_db
```


Se puede usar el archivo docker-compose como:

```
docker-compose up
```

### Test

Para ejecutar los test utlizando el archivo Makefile

```
$ make test
```

### Uso básico

#### Recibir una orden

Cuando se recibe una nueva orden SPEI, se hace una llamada al
servicio /ordenes. Se crea una transacción en la tabla `transactions`
y se asocia un evento tipo `create` a la tabla `Events`. Posteriormente
se guarda la orden en RabbitMQ para ser utilizado por el backend.
El servicio aguarda 15 segundos a obtener una respuesta la cual es 
almacenada en un nuevo Evento asociado a la Transacción y se devuelve la
respuesta.

El cuerpo del mensaje almacenado en RabbitMQ es como sigue:

```python
{
'orden_id': 6440277,                              # Orden ID de STP 
'fecha_operacion': 20181008,                     
'institucion_ordenante': '072',                  # Código del banco definido por SPEI
'institucion_beneficiaria': '646',               # Código del banco definido por SPEI
'clave_rastreo': '7279MAP6201810060648658333', 
'monto': 1020,                                 # En centavos 
'nombre_ordenante': 'RICARDO SANCHEZ CASTILLO', 
'tipo_cuenta_ordenante': 40, 
'cuenta_ordenante': '072691004495711499', 
'rfc_curp_ordenante': 'SACR891125M47', 
'nombre_beneficiario': 'Matin Tamizi', 
'tipo_cuenta_beneficiario': 40, 
'cuenta_beneficiario': '646180157029907065', 
'rfc_curp_beneficiario': 'No capturado.', 
'concepto_pago': 'Test2', 
'referencia_numerica': 181006, 
'empresa': 'TAMIZI', 
}
```

#### Enviar una orden

Si el cliente quiere realizar una transferencia, entonces el backend debe
colocar la tarea en RabbitMQ como una orden de Celery: 

```python
from celery import Celery

order = order = dict(
            concepto_pago='PRUEBA',
            institucion_ordenante='646',
            cuenta_beneficiario='072691004495711499',
            institucion_beneficiaria='072',
            monto=1020,
            nombre_beneficiario='Ricardo Sánchez',
            nombre_ordenante='BANCO',
            cuenta_ordenante='646180157000000004',
            rfc_curp_ordenante='ND',
            speid_id='SOME_RANDOM_ID',
            version=1
        )
app = Celery('stp_client')
app.config_from_object('speid.daemon.celeryconfig')
app.send_task('speid.daemon.tasks.send_order',
              kwargs={'order_val': order})
```

Se puede utilizar el archivo de configuración `speid.daemon.celeryconfig` o hacer una configuración
básica desde el backend para no tener dependencias.

Estos son los campos obligatorios a incluir en la orden:

```javascript
{
    "concepto_pago": "Concepto"
    "institucion_ordenante": "Código del banco en SPEI",
    "cuenta_beneficiario": "CLABE del beneficiario",
    "institucion_beneficiaria": "Código del banco en SPEI",
    "monto": 120, //Cantidad en centavos
    "nombre_beneficiario": "Nombre",
    "nombre_ordenante": "Nombre",
    "cuenta_ordenante": "CLABE del ordenante",
    "rfc_curp_ordenante": "RFC",
}
```

Campos opcionales:

````javascript
{
    "speid_id": "ID generado por el backend para identificar la orden",
    "version": 1, //Se asume versión 0 si no es especificado
    "empresa": "Default: Aquella que fue ingresada en las credenciales de STP",
    "folio_origen": "",
    "clave_rastreo": "Default: CR{TIME}",
    "tipo_pago": 1, //Default: 1
    "tipo_cuenta_ordenante": "",
    "tipo_cuenta_beneficiario": 40, //Default: 40
    "rfc_curp_beneficiario": "Default: ND",
    "email_beneficiario": "",
    "tipo_cuenta_beneficiario2": "",
    "nombre_beneficiario2": "",
    "cuenta_beneficiario2": "",
    "rfc_curpBeneficiario2": "",
    "concepto_pago2": "",
    "clave_cat_usuario1": "",
    "clave_cat_usuario2": "",
    "clave_pago": "",
    "referencia_cobranza": "",
    "referencia_numerica": 0, //Default: Número aleatorio
    "tipo_operacion": "",
    "topologia": "Default: T",
    "usuario": "",
    "medio_entrega": 3, //Default: 3
    "prioridad": 1, //Default: 1
    "iva": "",
}
````

Al momento de agregar la tarea de Celery, está es ejecutada por el Daemon
y se genera una nueva transacción con su correspondiente evento,
posteriormente se envía la orden al proveedor (STP) y el resultado se almacena
en un nuevo evento y se devuelve a RabbitMQ una notificación:

```python
{
'speid_id': 'SOME_ID',
'orden_id': 'orden_id',
'estado': 'submitted'
}
```

Cuando STP responde con el resultado de la operación, se recibe en el
servicio `/orden_events` el cual busca la transacción por el ID de la orden y
almacena un nuevo Evento. Posteriormente se envía a RabbitMQ para ser
procesado por el Backend.

Este es el cuerpo del mensaje en RabbitMQ:

````python
{
'orden_id': 'orden_id', 
'estado': 'success',    # Opciones [success, failed] 
'speid_id': 'SOME_ID'
}
````