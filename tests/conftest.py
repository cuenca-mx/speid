from dataclasses import dataclass

import pytest


@dataclass
class Response:
    status_code: int
    text: str


def substitute_patch_status(*_, **__):
    return Response(status_code=201, text='{"status": "succeeded"}')


@pytest.fixture
def mock_callback_api(monkeypatch):
    import requests

    monkeypatch.setattr(requests, 'patch', substitute_patch_status)
    monkeypatch.setattr(requests, 'post', substitute_patch_status)


@pytest.fixture(scope='module')
def vcr_config():
    config = dict()
    # config['record_mode'] = 'none'
    return config


@pytest.fixture(scope='module')
def file_recon():
    body = (
        "STP received successfully (1):\n"
        "{'id': 22673742, 'institucion': 'STP', 'contraparte': 'BANORTE/I"
        "XE', 'rastreo': 'CR1547453521', 'fecha_operacion': 20181213, 'mo"
        "nto': 1232, 'estado_orden': 'Liquidada', 'referencia_numerica': "
        "7382934, 'ordenante': 'BANCO', 'cuenta_ordenante': '072696273648"
        "711499', 'rfc_curp_ordenante': 'ND', 'beneficiario': 'Carlos Gon"
        "zalez', 'cuenta_beneficiario': '646180827000027384', 'rfc_curp_b"
        "eneficiario': 'ND', 'concepto_pago': 'PRUEBA', 'empresa': 'TAMIZ"
        "I'}\n\nSTP sent successfully (1):\n{'id': 25663741, 'institucion"
        "': 'STP', 'contraparte': 'BANORTE/IXE', 'rastreo': 'CUENCA263', "
        "'fecha_operacion': 20190301, 'monto': 2500000, 'estado_orden': '"
        "Liquidada', 'referencia_numerica': 3526516, 'ordenante': 'TAMIZI"
        " SA DE CV', 'cuenta_ordenante': '646187283000000004', 'rfc_curp_"
        "ordenante': 'TAM180309C16', 'beneficiario': 'Optimizacion de Rec"
        "ursos Regalii', 'cuenta_beneficiario': '072078002960364722', 'rf"
        "c_curp_beneficiario': 'None', 'concepto_pago': 'mas dinero', 'em"
        "presa': 'TAMIZI'}\n\nSTP others (1):\n{'id': 7432344, 'instituci"
        "on': 'STP', 'contraparte': 'ACCENDO BANCO', 'rastreo': 'MANU-006"
        "47368751', 'fecha_operacion': 20190116, 'monto': 100000, 'estado"
        "_orden': 'Devuelta', 'referencia_numerica': 19843, 'ordenante': "
        "'None', 'cuenta_ordenante': 'None', 'rfc_curp_ordenante': 'None'"
        ", 'beneficiario': 'Josefina Antonieta Caras Noriega', 'cuenta_be"
        "neficiario': '646180157020536253', 'rfc_curp_beneficiario': 'ND'"
        ", 'concepto_pago': 'FONDEO', 'empresa': 'TAMIZI'}\n\nSPEID submi"
        "tted (1):\n{'orden_id': 'None', 'institucion_ordenante': 646, 'i"
        "nstitucion_beneficiaria': 14, 'clave_rastreo': 'CR1540950253', '"
        "fecha_operacion': 20181031, 'monto': 120, 'estado': 'submitted',"
        " 'cuenta_ordenante': '12180026543282738', 'cuenta_beneficiario':"
        " '14180567188562673'}\n\nSPEID success (1):\n{'orden_id': 244834"
        "6, 'institucion_ordenante': 12, 'institucion_beneficiaria': 'Non"
        "e', 'clave_rastreo': 'PRUEBATAMIZI1', 'fecha_operacion': 2018061"
        "8, 'monto': 10000, 'estado': 'success', 'cuenta_ordenante': '846"
        "267300500000008', 'cuenta_beneficiario': '646180157000037824'}\n"
        "\nSPEID others (0):\n\nCUENCA created (1):\n{'id': '"
        "SP36XEZuOVZms7VtutjzYvcf', 'clave_rastreo': 'CUENCA1552184653', "
        "'created_at': '09-03-2019 04:03:1552104253', 'amount': 3450, 'st"
        "atus': 'created', 'numero_referencia': '7263564'}\n\nCUENCA subm"
        "itted (1):\n{'id': 'LT2F8RtCjZwI2DQvJAPe5b00', 'clave_rastreo': "
        "'CUENCA1541512409', 'created_at': '06-11-2018 13:11:1541512409',"
        " 'amount': 1000, 'status': 'submitted', 'numero_referencia': '56"
        "65503'}\n\nCUENCA succeeded (0):\n\nCUENCA others (0):\n\nSTP/CU"
        "ENCA (0):\n\nSTP/SPEID same status (2):\n{'id': 6345658, 'instit"
        "ucion': 'STP', 'contraparte': 'BBVA BANCOMER', 'rastreo': '00264"
        "73000265786', 'fecha_operacion': 20181031, 'monto': 675600, 'est"
        "ado_orden': 'Confirmada', 'referencia_numerica': 3165364, 'orden"
        "ante': 'CC MEXICO HOLDINGS S  DE RL DE CV', 'cuenta_ordenante': "
        "'012180001571847460', 'rfc_curp_ordenante': 'CMH6476252M1', 'ben"
        "eficiario': 'Dario Davila', 'cuenta_beneficiario': '646180157029"
        "907647', 'rfc_curp_beneficiario': 'None', 'concepto_pago': 'CITA"
        "DEL74651591', 'empresa': 'TAMIZI'}\n{'orden_id': 6345658, 'insti"
        "tucion_ordenante': 12, 'institucion_beneficiaria': 'None', 'clav"
        "e_rastreo': '0026473000265786', 'fecha_operacion': 20181031, 'mo"
        "nto': 3165364, 'estado': 'success', 'cuenta_ordenante': '0121800"
        "01571847460', 'cuenta_beneficiario': '646180157029907647'}\n\nST"
        "P/SPEID different status (2):\n{'id': 21073705, 'institucion': '"
        "STP', 'contraparte': 'BANORTE/IXE', 'rastreo': 'CR1539036578', '"
        "fecha_operacion': 20181008, 'monto': 2046, 'estado_orden': 'Liqu"
        "idada', 'referencia_numerica': 3314058, 'ordenante': 'BANCO', 'c"
        "uenta_ordenante': '646180157000000004', 'rfc_curp_ordenante': 'N"
        "D', 'beneficiario': 'Ricardo Sánchez', 'cuenta_beneficiario': '0"
        "72691004495711499', 'rfc_curp_beneficiario': 'ND', 'concepto_pag"
        "o': 'PRUEBA', 'empresa': 'TAMIZI'}\n{'orden_id': 21073705, 'inst"
        "itucion_ordenante': 646, 'institucion_beneficiaria': 72, 'clave_"
        "rastreo': 'CR1539036578', 'fecha_operacion': 20181008, 'monto': "
        "2046, 'estado': 'submitted', 'cuenta_ordenante': '64618015700000"
        "0004', 'cuenta_beneficiario': '72691004495711499'}\n\nSPEID/CUEN"
        "CA submitted (2):\n{'orden_id': 'None', 'institucion_ordenante':"
        " 646, 'institucion_beneficiaria': 72, 'clave_rastreo': 'CUENCA15"
        "44567707', 'fecha_operacion': 20181211, 'monto': 231, 'estado': "
        "'submitted', 'cuenta_ordenante': '646180157063641989', 'cuenta_b"
        "eneficiario': '72691004495711499'}\n{'id': 'SP5q1a3wCVC3g4BU0uY5"
        "fZE', 'clave_rastreo': 'CUENCA1544567707', 'created_at': '11-12-"
        "2018 22:12:1544567707', 'amount': 231, 'status': 'submitted', 'n"
        "umero_referencia': '4091444'}\n\nSPEID/CUENCA succeeded (2):\n{'"
        "orden_id': 28282738, 'institucion_ordenante': 90646, 'institucio"
        "n_beneficiaria': 40012, 'clave_rastreo': 'CUENCA1556029364', 'fe"
        "cha_operacion': 20190423, 'monto': 150000, 'estado': 'succeeded'"
        ", 'cuenta_ordenante': '646180157062370426', 'cuenta_beneficiario"
        "': '4152313498971212'}\n{'id': 'SP3qKlB2zTEtrSIbXrJZGcA2', 'clav"
        "e_rastreo': 'CUENCA1556029364', 'created_at': '23-04-2019 14:04:"
        "1556029441', 'amount': 150000, 'status': 'succeeded', 'numero_re"
        "ferencia': '5705984'}\n\nSPEID/CUENCA different status (2):\n{'o"
        "rden_id': 8489980, 'institucion_ordenante': 40127, 'institucion_"
        "beneficiaria': 90646, 'clave_rastreo': '190423070825308455I', 'f"
        "echa_operacion': 20190423, 'monto': 10000, 'estado': 'None', 'cu"
        "enta_ordenante': '127180013501165438', 'cuenta_beneficiario': '6"
        "46180157029206957'}\n{'id': 'SP4v371cyTNvV1TgQtRWbCz8', 'clave_r"
        "astreo': '190423070825308455I', 'created_at': '23-04-2019 03:04:"
        "1555989127', 'amount': 10000, 'status': 'succeeded', 'numero_ref"
        "erencia': '206957'}\n\nSPEID/CUENCA others (0):\n"
    )
    return body


@pytest.fixture(scope='module')
def file_recon1():
    body = (
        "STP received successfully (1):\n"
        "{'id': 22672732, 'institucion': 'STP', 'contraparte': 'BAN"
        "ORTE/IXE', 'rastreo': 'HG745321', 'fecha_operacion': 20181213, '"
        "monto': 1435, 'estado_orden': 'Liquidada', 'referencia_numerica'"
        ": 7382253, 'ordenante': 'BANCO', 'cuenta_ordenante': '0726962736"
        "48711499', 'rfc_curp_ordenante': 'ND', 'beneficiario': 'Carlos C"
        "astro', 'cuenta_beneficiario': '646180827000027384', 'rfc_curp_b"
        "eneficiario': 'ND', 'concepto_pago': 'PRUEBA', 'empresa': 'TAMIZ"
        "I'}\n\nSTP sent successfully (1):\n{'id': 25663741, 'institucion"
        "': 'STP', 'contraparte': 'BANORTE/IXE', 'rastreo': 'CUENCA263', "
        "'fecha_operacion': 20190301, 'monto': 2500000, 'estado_orden': '"
        "Liquidada', 'referencia_numerica': 3526516, 'ordenante': 'TAMIZI"
        " SA DE CV', 'cuenta_ordenante': '646187283000000004', 'rfc_curp_"
        "ordenante': 'TAM180309C16', 'beneficiario': 'Optimizacion de Rec"
        "ursos Regalii', 'cuenta_beneficiario': '072078002960364722', 'rf"
        "c_curp_beneficiario': 'None', 'concepto_pago': 'mas dinero', 'em"
        "presa': 'TAMIZI'}\n\nSTP others (1):\n{'id': 7432344, 'instituci"
        "on': 'STP', 'contraparte': 'ACCENDO BANCO', 'rastreo': 'MANU-006"
        "47368751', 'fecha_operacion': 20190116, 'monto': 100000, 'estado"
        "_orden': 'Devuelta', 'referencia_numerica': 19843, 'ordenante': "
        "'None', 'cuenta_ordenante': 'None', 'rfc_curp_ordenante': 'None'"
        ", 'beneficiario': 'Josefina Antonieta Caras Noriega', 'cuenta_be"
        "neficiario': '646180157020536253', 'rfc_curp_beneficiario': 'ND'"
        ", 'concepto_pago': 'FONDEO', 'empresa': 'TAMIZI'}\n\nSPEID submi"
        "tted (1):\n{'orden_id': 'None', 'institucion_ordenante': 646, 'i"
        "nstitucion_beneficiaria': 14, 'clave_rastreo': 'CR1540950253', '"
        "fecha_operacion': 20181031, 'monto': 120, 'estado': 'submitted',"
        " 'cuenta_ordenante': '12180026543282738', 'cuenta_beneficiario':"
        " '14180567188562673'}\n\nSPEID success (1):\n{'orden_id': 244834"
        "6, 'institucion_ordenante': 12, 'institucion_beneficiaria': 'Non"
        "e', 'clave_rastreo': 'PRUEBATAMIZI1', 'fecha_operacion': 2018061"
        "8, 'monto': 10000, 'estado': 'success', 'cuenta_ordenante': '846"
        "267300500000008', 'cuenta_beneficiario': '646180157000037824'}\n"
        "\nSPEID others (0):\n\nCUENCA created (1):\n{'id': '"
        "SP36XEZuOVZms7VtutjzYvcf', 'clave_rastreo': 'CUENCA1552184653', "
        "'created_at': '09-03-2019 04:03:1552104253', 'amount': 3450, 'st"
        "atus': 'created', 'numero_referencia': '7263564'}\n\nCUENCA subm"
        "itted (1):\n{'id': 'LT2F8RtCjZwI2DQvJAPe5b00', 'clave_rastreo': "
        "'CUENCA1541512409', 'created_at': '06-11-2018 13:11:1541512409',"
        " 'amount': 1000, 'status': 'submitted', 'numero_referencia': '56"
        "65503'}\n\nCUENCA succeeded (0):\n\nCUENCA others (0):\n\nSTP/CU"
        "ENCA (0):\n\nSTP/SPEID same status (2):\n{'id': 6345658, 'instit"
        "ucion': 'STP', 'contraparte': 'BBVA BANCOMER', 'rastreo': '00264"
        "73000265786', 'fecha_operacion': 20181031, 'monto': 675600, 'est"
        "ado_orden': 'Confirmada', 'referencia_numerica': 3165364, 'orden"
        "ante': 'CC MEXICO HOLDINGS S  DE RL DE CV', 'cuenta_ordenante': "
        "'012180001571847460', 'rfc_curp_ordenante': 'CMH6476252M1', 'ben"
        "eficiario': 'Dario Davila', 'cuenta_beneficiario': '646180157029"
        "907647', 'rfc_curp_beneficiario': 'None', 'concepto_pago': 'CITA"
        "DEL74651591', 'empresa': 'TAMIZI'}\n{'orden_id': 6345658, 'insti"
        "tucion_ordenante': 12, 'institucion_beneficiaria': 'None', 'clav"
        "e_rastreo': '0026473000265786', 'fecha_operacion': 20181031, 'mo"
        "nto': 3165364, 'estado': 'success', 'cuenta_ordenante': '0121800"
        "01571847460', 'cuenta_beneficiario': '646180157029907647'}\n\nST"
        "P/SPEID different status (2):\n{'id': 21073705, 'institucion': '"
        "STP', 'contraparte': 'BANORTE/IXE', 'rastreo': 'CR1539036578', '"
        "fecha_operacion': 20181008, 'monto': 2046, 'estado_orden': 'Liqu"
        "idada', 'referencia_numerica': 3314058, 'ordenante': 'BANCO', 'c"
        "uenta_ordenante': '646180157000000004', 'rfc_curp_ordenante': 'N"
        "D', 'beneficiario': 'Ricardo Sánchez', 'cuenta_beneficiario': '0"
        "72691004495711499', 'rfc_curp_beneficiario': 'ND', 'concepto_pag"
        "o': 'PRUEBA', 'empresa': 'TAMIZI'}\n{'orden_id': 21073705, 'inst"
        "itucion_ordenante': 646, 'institucion_beneficiaria': 72, 'clave_"
        "rastreo': 'CR1539036578', 'fecha_operacion': 20181008, 'monto': "
        "2046, 'estado': 'submitted', 'cuenta_ordenante': '64618015700000"
        "0004', 'cuenta_beneficiario': '72691004495711499'}\n\nSPEID/CUEN"
        "CA submitted (2):\n{'orden_id': 'None', 'institucion_ordenante':"
        " 646, 'institucion_beneficiaria': 72, 'clave_rastreo': 'CUENCA15"
        "44567707', 'fecha_operacion': 20181211, 'monto': 231, 'estado': "
        "'submitted', 'cuenta_ordenante': '646180157063641989', 'cuenta_b"
        "eneficiario': '72691004495711499'}\n{'id': 'SP5q1a3wCVC3g4BU0uY5"
        "fZE', 'clave_rastreo': 'CUENCA1544567707', 'created_at': '11-12-"
        "2018 22:12:1544567707', 'amount': 231, 'status': 'submitted', 'n"
        "umero_referencia': '4091444'}\n\nSPEID/CUENCA succeeded (2):\n{'"
        "orden_id': 28282738, 'institucion_ordenante': 90646, 'institucio"
        "n_beneficiaria': 40012, 'clave_rastreo': 'CUENCA1556029364', 'fe"
        "cha_operacion': 20190423, 'monto': 150000, 'estado': 'succeeded'"
        ", 'cuenta_ordenante': '646180157062370426', 'cuenta_beneficiario"
        "': '4152313498971212'}\n{'id': 'SP3qKlB2zTEtrSIbXrJZGcA2', 'clav"
        "e_rastreo': 'CUENCA1556029364', 'created_at': '23-04-2019 14:04:"
        "1556029441', 'amount': 150000, 'status': 'succeeded', 'numero_re"
        "ferencia': '5705984'}\n\nSPEID/CUENCA different status (2):\n{'o"
        "rden_id': 8489980, 'institucion_ordenante': 40127, 'institucion_"
        "beneficiaria': 90646, 'clave_rastreo': '190423070825308455I', 'f"
        "echa_operacion': 20190423, 'monto': 10000, 'estado': 'None', 'cu"
        "enta_ordenante': '127180013501165438', 'cuenta_beneficiario': '6"
        "46180157029206957'}\n{'id': 'SP4v371cyTNvV1TgQtRWbCz8', 'clave_r"
        "astreo': '190423070825308455I', 'created_at': '23-04-2019 03:04:"
        "1555989127', 'amount': 10000, 'status': 'succeeded', 'numero_ref"
        "erencia': '206957'}\n\nSPEID/CUENCA others (0):\n"
    )
    return body


@pytest.fixture(scope='module')
def file_recon2():
    body = (
        "STP received successfully (1):\n"
        "{'id': 22673745, 'institucion': 'STP', 'contraparte': 'BAN"
        "ORTE/IXE', 'rastreo': 'GH458434', 'fecha_operacion': 20181213, '"
        "monto': 3000, 'estado_orden': 'Liquidada', 'referencia_numerica'"
        ": 7382253, 'ordenante': 'BANCO', 'cuenta_ordenante': '3336962736"
        "48711499', 'rfc_curp_ordenante': 'ND', 'beneficiario': 'Carlos C"
        "astro', 'cuenta_beneficiario': '646180827000027384', 'rfc_curp_b"
        "eneficiario': 'ND', 'concepto_pago': 'PRUEBA', 'empresa': 'TAMIZ"
        "I'}\n\nSTP sent successfully (0):\n\nSTP others (0):\n\nSPEID su"
        "ccess (0):\n\nSPEID others (0):\n\nCUENCA created (0):\n\nCUENCA"
        " submitted (0):\n\nCUENCA succeeded (0):\n\nCUENCA others (0):\n"
        "\nSTP/CUENCA (0):\n\nSTP/SPEID same status (0):\n\nSTP/SPEID dif"
        "ferent status (0):\n\nSPEID/CUENCA submitted (0):\n\nSPEID/CUENC"
        "A succeeded (0):\n\nSPEID/CUENCA different status (0):\n\nSPEID/"
        "CUENCA others (0):\n"
    )
    return body
