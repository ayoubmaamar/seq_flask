import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
#from cryptography.hazmat.primitives import padding # If we want Padding

#For CBC

iv = os.urandom(16)
mode_CBC = modes.CBC(iv)


#Change the first bit of the Byte indicated within the message
def flip_first_bit_from_byte_n(msg, n):
     byte_list = list(msg)
     byte_list[n] = byte_list[n] ^ (1 << 7) # Change Byte 0
     return bytes(byte_list)


#Returns the number of different bits between the two bytes
def compare_bits(byte_a, byte_b):
     byte_a_str = bin(byte_a)[2:].zfill(8)
     byte_b_str = bin(byte_b)[2:].zfill(8)
     counter = 0
     for i in range(0, len(byte_a_str)):
         if (byte_a_str[i] != byte_b_str[i]):
             counter = counter + 1
     return counter


#Returns the number of different bits between the two byte arrays
def compare_bytes(bytes_a, bytes_b):
     counter = 0
     for i in range(0, len(bytes_a)):
         counter = counter + compare_bits(bytes_a[i], bytes_b[i])
     return counter


def exercise1():
     return 0


exercise1()

# To perform the Padding of 128-bit blocks (AES) you would have to use a padder
# padder = padding.PKCS7(128).padder()

# Generate a random key
key = os.urandom(16)

# Creates an encryption object using the indicated algorithm and mode and initializes it with the key key
cipher_ecb = Cipher(algorithms.AES(key), modes.ECB())

# Create an encryptor, a decryptor could also have been created
encryptor_ecb = cipher_ecb.encryptor()

msg1 = os.urandom(16)
print(msg1.hex())

#Change a bit in the first byte of the message
msg2 = flip_first_bit_from_byte_n(msg1, 0)
print(msg2.hex())

# If we want padding first we would have to use the padder
# p = padder.update(msg)
# p += padder.finalize()

# msg has length multiple of 128 bits
encryption1 = encryptor_ecb.update(msg1)
# if I want to encrypt less than 16 bytes it does not return anything

#Since there is no padding, finalize does not return anything additional
encryptor_ecb.finalize()

print(encryption1.hex())

encryptor_ecb = cipher_ecb.encryptor()

# msg has length multiple of 128 bits
encryption2 = encryptor_ecb.update(msg2)

#Since there is no padding, finalize does not return anything additional
encryptor_ecb.finalize()

print(encryption2.hex())

print('Differences %d ' % (compare_bytes(encryption1, encryption2)))