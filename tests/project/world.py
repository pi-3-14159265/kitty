import kitty


class Animal(kitty.Sprite):
    title = "pet"

    def __init__(self):
        self.hp = 1

    def speak(self):
        self.set_y(4)


class Cat(Animal):
    def __init__(self, lives):
        super().__init__()
        self.hp = lives

    def speak(self):
        super().speak()
        self.set_x(self.hp)

    def nudge(self, dx):
        self.change_x(dx)

    hit = lambda n: self.hp - n

    def wounded(self):
        self.set_size(self.hit(1))


felix = Cat(9)


class Game(kitty.Stage):
    kitty.backdrop("plain.svg", name="plain")

    def stamp(self):
        self.switch_backdrop("plain")


game = Game()
