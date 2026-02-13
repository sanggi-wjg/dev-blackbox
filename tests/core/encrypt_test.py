from dev_blackbox.core.encrypt import EncryptService


def test_encrypt_decrypt():
    key = "test_key"
    pepper = "test_pepper"
    encrypt_service = EncryptService(key, pepper)

    # given
    secret_key = "Hello, I am a secret key!"

    # when
    encrypted_text = encrypt_service.encrypt(secret_key)
    decrypted_text = encrypt_service.decrypt(encrypted_text)

    assert decrypted_text == secret_key
