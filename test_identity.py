import identity
from tool import *

class TestIdentity(TestCase):
    def test_identity(self):
        self.assertEquals(identity.identity(1), 1)
        self.assertEquals(identity.identity(2), 2)
        self.assertEquals(identity.identity(3), 3)

    def test_doubler(self):
        self.assertIOEquals(identity.doubler, ['1'], '11')

    def test_greeter(self):
        self.assertIOEquals(identity.greeter, ['John', 'Doe'], 'Hello John Doe')

    def test_museum01(self):
        self.assertIOFromFileEquals(identity.museum, ['y', 'John'], 'testMuseum01.txt')

    def test_museum02(self):
        self.assertIOFromFileEquals(identity.museum, ['n'], 'testMuseum02.txt')


