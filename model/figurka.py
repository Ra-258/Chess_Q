class Figurka:
    def __init__(
        self,
        barva,
        typ,
        vektory_pohybu=None,
        vektory_utoku=None,
        muze_v_nasobcich=False,
        maximalni_nasobek=1,
        muze_preskakovat=False
    ):
        self.__barva = barva
        self._typ = typ
        self._vektory_pohybu = vektory_pohybu if vektory_pohybu is not None else []
        self._vektory_utoku = vektory_utoku if vektory_utoku is not None else []
        self._muze_v_nasobcich = muze_v_nasobcich
        self._maximalni_nasobek = maximalni_nasobek
        self._muze_preskakovat = muze_preskakovat

    def get_smery_pohybu(self):
        return self._vektory_pohybu

    def getSmeryUtoku(self):
        return self._vektory_utoku

    def muzeVNasobcich(self):
        return self._muze_v_nasobcich

    def getMaximalniNasobek(self) -> int:
        return self._maximalni_nasobek

    def muzePreskakovat(self):
        return self._muze_preskakovat

    def getBarva(self):
        return self.__barva

    def getTyp(self):
        return self._typ


class Kral(Figurka):
    def __init__(self, barva, typ):
        vektory = [
            (0, 1), (0, -1),
            (1, 0), (-1, 0),
            (1, 1), (1, -1),
            (-1, 1), (-1, -1)
        ]

        super().__init__(
            barva,
            typ,
            vektory_pohybu=vektory,
            vektory_utoku=vektory,
            muze_v_nasobcich=False,
            maximalni_nasobek=1,
            muze_preskakovat=False
        )


class Kun(Figurka):
    def __init__(self, barva, typ):
        vektory = [
            (1, 2), (2, 1),
            (-1, 2), (-2, 1),
            (1, -2), (2, -1),
            (-1, -2), (-2, -1)
        ]

        super().__init__(
            barva,
            typ,
            vektory_pohybu=vektory,
            vektory_utoku=vektory,
            muze_v_nasobcich=False,
            maximalni_nasobek=1,
            muze_preskakovat=True
        )


class Vez(Figurka):
    def __init__(self, barva, typ):
        vektory = [
            (0, 1), (0, -1),
            (1, 0), (-1, 0)
        ]

        super().__init__(
            barva,
            typ,
            vektory_pohybu=vektory,
            vektory_utoku=vektory,
            muze_v_nasobcich=True,
            maximalni_nasobek=7,
            muze_preskakovat=False
        )


class Strelec(Figurka):
    def __init__(self, barva, typ):
        vektory = [
            (1, 1), (1, -1),
            (-1, 1), (-1, -1)
        ]

        super().__init__(
            barva,
            typ,
            vektory_pohybu=vektory,
            vektory_utoku=vektory,
            muze_v_nasobcich=True,
            maximalni_nasobek=7,
            muze_preskakovat=False
        )


class Pesec(Figurka):
    def __init__(self, barva, typ):
        smer = 1 if barva == 1 else -1

        vektory_pohybu = [
            (0, smer)
        ]

        vektory_utoku = [
            (1, smer),
            (-1, smer)
        ]

        super().__init__(
            barva,
            typ,
            vektory_pohybu=vektory_pohybu,
            vektory_utoku=vektory_utoku,
            muze_v_nasobcich=False,
            maximalni_nasobek=1,
            muze_preskakovat=False
        )


class Dama(Figurka):
    def __init__(self, barva, typ):
        vektory = [
            (0, 1), (0, -1),
            (1, 0), (-1, 0),
            (1, 1), (1, -1),
            (-1, 1), (-1, -1)
        ]

        super().__init__(
            barva,
            typ,
            vektory_pohybu=vektory,
            vektory_utoku=vektory,
            muze_v_nasobcich=True,
            maximalni_nasobek=7,
            muze_preskakovat=False
        )


if __name__ == "__main__":
    figurka = Dama(1, "Dama")

    print(figurka.getTyp())
    print(figurka.getBarva())
    print(figurka.get_smery_pohybu())
    print(figurka.getSmeryUtoku())
    print(figurka.muzeVNasobcich())
    print(figurka.getMaximalniNasobek())
    print(figurka.muzePreskakovat())