from .fixtures import *


def test_foo(user_manager):
    print(user_manager.get(1))
