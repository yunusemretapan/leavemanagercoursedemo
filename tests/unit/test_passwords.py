import pytest

from app.business.passwords import (
    MAX_LENGTH,
    MIN_LENGTH,
    PRODUCTION_SCRYPT,
    ScryptParams,
    check_policy,
    common_passwords,
    dummy_hash,
    hash_password,
    verify_password,
)
from app.business.seed import validate_demo_password
from app.models.errors import ConfigurationError

FAST = ScryptParams(n=2**10, r=8, p=1)
GOOD = "uzun ve benzersiz bir cümle"


def test_policy_rejects_short_long_common_and_username() -> None:
    assert check_policy("a" * (MIN_LENGTH - 1)) != []
    assert check_policy("a" * (MAX_LENGTH + 1)) != []
    assert check_policy("Parola123456") != []  # blocklisted, case-insensitive
    assert check_policy("Ali.Demir.12", username="  ali.demir.12 ") != []
    # Unicode length counts characters, not bytes: 11 Turkish letters are still too short.
    assert check_policy("ğüşiöçĞÜŞİÖ") != []


def test_policy_accepts_12_and_128_chars() -> None:
    assert check_policy("k" * 11 + "x") == []
    assert check_policy("ç" * MAX_LENGTH) == []
    assert check_policy(GOOD, username="ali.demir") == []


def test_policy_messages_never_echo_the_password() -> None:
    candidate = "parola123456"
    assert all(candidate not in message for message in check_policy(candidate))


def test_common_password_list_has_at_least_100_entries() -> None:
    assert len(common_passwords()) >= 100


def test_password_is_not_trimmed() -> None:
    stored = hash_password(GOOD + " ", FAST)
    assert not verify_password(GOOD, stored)
    assert verify_password(GOOD + " ", stored)


def test_hashes_differ_for_same_password_and_verify() -> None:
    first = hash_password(GOOD, FAST)
    second = hash_password(GOOD, FAST)
    assert first != second
    assert GOOD not in first
    assert verify_password(GOOD, first)
    assert verify_password(GOOD, second)
    assert not verify_password(GOOD + "x", first)


def test_dummy_hash_matches_no_password() -> None:
    assert not verify_password(GOOD, dummy_hash(FAST))


@pytest.mark.parametrize("params", [PRODUCTION_SCRYPT])
def test_verify_with_production_params(params: ScryptParams) -> None:
    stored = hash_password(GOOD, params)
    assert stored.startswith(f"scrypt${2**17}$8$1$")
    assert verify_password(GOOD, stored)


def test_validate_demo_password_boundaries_and_no_echo() -> None:
    twelve = "k" * 11 + "x"
    long_ok = "ç" * MAX_LENGTH
    assert validate_demo_password(twelve) == twelve
    assert validate_demo_password(long_ok) == long_ok
    for rejected in (None, "", "k" * 10 + "x", "ç" * (MAX_LENGTH + 1), "x" * 200):
        with pytest.raises(ConfigurationError) as caught:
            validate_demo_password(rejected)
        if rejected:
            assert rejected not in str(caught.value)


def test_validate_demo_password_checks_every_demo_username() -> None:
    # "zeynep.sahin" is 12 characters and a demo username (not the first one in the list).
    with pytest.raises(ConfigurationError, match="kullanıcı adıyla aynı"):
        validate_demo_password("zeynep.sahin")
