# Código para establecer una clave compartida con un compañero utilizando Diffie-Hellman. Este código supone que una entidad confiable genera los parámetros DH públicos que utilizaremos para crear nuestras claves. Pasaremos nuestra clave pública al compañero/a y el/ella nos dará la suya con lo que generamos la clave compartida

from cryptography.hazmat.primitives.asymmetric import dh
from cryptography.hazmat.primitives.serialization import ParameterFormat
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.hazmat.primitives.asymmetric.dh import DHParameterNumbers

#Referencia: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/dh/#exchange-algorithm

# Generate Public DH parameters to be shared between Alice and Bob
print("Generando parámetros públicos...\n")
parameters = dh.generate_parameters(generator=2, key_size=512)
params_pem = parameters.parameter_bytes(Encoding.PEM, ParameterFormat.PKCS3)
print("Parámetros públicos en formato PKCS3: ")
print(params_pem.decode("utf-8"))
print("Parámetros públicos en formato numérico: ")
print("g = %d" % parameters.parameter_numbers().g)
print("p = %d\n" % parameters.parameter_numbers().p)

# --------------------------------------------------------
print("Introduce los parámetros públicos:")
b_g = int(input("g: "))
b_p = int(input("p: "))

b_params_from_number = DHParameterNumbers(b_p, b_g).parameters()
#b_params_from_pem = load_pem_parameters(b_pem, backend=default_backend())

print("Parámetros Número: ")
print("g (alpha) = %d" % b_params_from_number.parameter_numbers().g)
print("p = %d\n" % b_params_from_number.parameter_numbers().p)
print("Parámetros PKCS3: ")
print(
    b_params_from_number.parameter_bytes(
        Encoding.PEM, ParameterFormat.PKCS3).decode("utf-8"))

parameters = b_params_from_number

#Generate keys.
a_private_key = parameters.generate_private_key()
a_public_key = a_private_key.public_key()

print("Esta es tu clave pública: %d\n" % a_public_key.public_numbers().y)
print("Introduce la clave pública de tu compañero")
b_public_key_number = int(input("clave: "))

#Des-serializando
peer_public_numbers = dh.DHPublicNumbers(
    b_public_key_number, b_params_from_number.parameter_numbers())
b_public_key = peer_public_numbers.public_key()

#Key exchange
shared_key_a = a_private_key.exchange(b_public_key)

print("\nClave calculada por mi = %s\n" % shared_key_a.hex())
