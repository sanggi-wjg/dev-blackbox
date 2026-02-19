from dev_blackbox.core.encrypt import EncryptService


def test_encrypt_service():
    key = "test_key"
    pepper = "test_pepper"
    encrypt_service = EncryptService(key, pepper)

    # given
    secret_key = "Hello, I am a secret key!"

    # when
    encrypted_text = encrypt_service.encrypt(secret_key)
    decrypted_text = encrypt_service.decrypt(encrypted_text)

    assert decrypted_text == secret_key


def test_encrypt_service_when_empty_secret():
    key = "test_key"
    pepper = "test_pepper"
    encrypt_service = EncryptService(key, pepper)

    # given
    empty_secret_key = ""

    # when
    encrypted_text = encrypt_service.encrypt(empty_secret_key)
    decrypted_text = encrypt_service.decrypt(encrypted_text)

    assert decrypted_text == empty_secret_key
