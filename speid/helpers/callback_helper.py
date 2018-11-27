import os
import json
import requests
from requests.auth import HTTPBasicAuth

CALLBACK_URL = os.getenv('CALLBACK_URL')
CALLBACK_API_KEY = os.getenv('CALLBACK_API_KEY')
CALLBACK_API_SECRET = os.getenv('CALLBACK_API_SECRET')


def send_transaction(transaction):
    body = dict(
        orden_id=transaction.orden_id,
        fecha_operacion=transaction.fecha_operacion.strftime('%Y%m%d'),
        institucion_ordenante=transaction.institucion_ordenante,
        institucion_beneficiaria=transaction.institucion_beneficiaria,
        clave_rastreo=transaction.clave_rastreo,
        monto=transaction.monto,
        nombre_ordenante=transaction.nombre_ordenante,
        tipo_cuenta_ordenante=transaction.tipo_cuenta_ordenante,
        cuenta_ordenante=transaction.cuenta_ordenante,
        rfc_curp_ordenante=transaction.rfc_curp_ordenante,
        nombre_beneficiario=transaction.nombre_beneficiario,
        tipo_cuenta_beneficiario=transaction.tipo_cuenta_beneficiario,
        cuenta_beneficiario=transaction.cuenta_beneficiario,
        rfc_curp_beneficiario=transaction.rfc_curp_beneficiario,
        concepto_pago=transaction.concepto_pago,
        referencia_numerica=transaction.referencia_numerica,
        empresa=transaction.empresa
    )
    response = requests.post(CALLBACK_URL,
                             json=body,
                             auth=HTTPBasicAuth(CALLBACK_API_KEY,
                                                CALLBACK_API_SECRET))
    return json.loads(response.text)


def set_status_transaction(request_id, status):
    response = requests.post('{0}/{1}'.format(CALLBACK_URL, request_id),
                             json=status,
                             auth=HTTPBasicAuth(CALLBACK_API_KEY,
                                                CALLBACK_API_SECRET))
    return response
