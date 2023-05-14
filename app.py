"""
Dit is een simulator voor 
het leenfietsen project van 
de stad Antwerpen.
"""
import pickle
import json
import sys
import os
import re
import numpy as np


class Fietstransporteur:
    """
    Deze class representeert een fietstransporteur
    """

    aantal_transporteurs = 0
    max_transporteurs = 0
    max_aantal_fietsen = 20

    def __init__(self):
        self._nummer = Fietstransporteur.aantal_transporteurs
        Fietstransporteur.aantal_transporteurs += 1


class Gebruiker:
    """
    Deze class representeert een gebruiker

    Class attributen:
        - aantal_gebruikers [int]
        - max_gebruikers [int]

    Instance attrbuten:
        - _sex [str] (2 options)
        - _voornaam [str]
        - _achternaam [str]
        - _aantal_ritten [int]
        - _laatste_rit [Rit]
    """

    aantal_gebruikers = 0
    max_gebruikers = 0
    totaal_aantal_ritten = 0

    def __init__(self, voornaam_man: list, voornaam_vrouw: list, achternaam: list):
        self._sex = "Man" if np.random.randint(0, 2) > 0.5 else "Vrouw"
        self._voornaam = (
            voornaam_man[np.random.randint(0, 101)]
            if self._sex == "Man"
            else voornaam_vrouw[np.random.randint(0, 101)]
        )
        self._achternaam = achternaam[np.random.randint(0, 101)]
        self._aantal_ritten = 0
        self._laatste_rit = None
        Gebruiker.aantal_gebruikers += 1


class Fiets:
    """
    Deze class representeert een fiets

    Class attributen:
        - aantal_fietsen [int]
        - max_fietsen [int]

    Instance attrbuten:
        - _laatste_gebruiker [Gebruiker]
        - _nummer [int]
    """

    aantal_fietsen = 0
    max_fietsen = 0

    def __init__(self):
        self._laatste_gebruiker = None
        self._nummer = Fiets.aantal_fietsen
        Fiets.aantal_fietsen += 1


class Slot:
    """
    Deze class representeert een slot in een station

    Instance attrbuten:
        - _bezet [Bool]
        - _fiets [Fiets]
    """

    def __init__(self):
        self._bezet = False
        self._fiets = None

    def fiets_deponeren(self, fiets: Fiets):
        """
        Je zet een fiets in het slot
        """
        self._fiets = fiets

    def fiets_pakken(self):
        """
        Je haalt een fiets uit een slot
        """
        fiets = self._fiets
        self._fiets = None
        return fiets

    def __str__(self) -> str:
        return "Dit slot is bezet" if self._bezet else "Dit slot is leeg"


class Station:
    """
    Deze class representeert een station

    Instance attrbuten:
        - stationnummer [int]
        - aantal_slots [int]
        - vol [bool]
        - slots [Slot]
        - adres [dict[str]]
        - coordinaten [dict[float]]
    """

    def __init__(
        self, stationnummer: int, adres: dict, coordinaten: dict, aantal_slots: int
    ) -> None:
        self._stationnummer = stationnummer
        self._aantal_slots = aantal_slots
        self._vol = False
        self._slots = []
        while len(self._slots) <= self._aantal_slots:
            slot = Slot()
            self._slots.append(slot)
        self._adres = adres
        self._coordinaten = coordinaten


class Rit:
    """
    Deze class representeert een rit van
    station A -> Station B met Fiets x

    Instance attrbuten:
        - startstation [Station]
        - eindstation [Station]
        - fiets [Fiets]
        - afstand [float] (km)
        - geschatte_tijd [float] (min)
    """

    def __init__(
        self, startstation: Station, eindstation: Station, fiets: Fiets
    ) -> None:
        self._fiets = fiets
        self._startstation = startstation
        self._eindstation = eindstation

        self._afstand = self.__calculate_distance(
            startstation._coordinaten["Y"],
            startstation._coordinaten["X"],
            eindstation._coordinaten["Y"],
            eindstation._coordinaten["X"],
        )
        self._geschatte_tijd = self.__calculate_estimate_time(self._afstand)

    def __calculate_distance(
        self, x_a: float, y_a: float, x_b: float, y_b: float
    ) -> float:
        lat1, lat2 = np.radians(x_a), np.radians(x_b)
        lon1, lon2 = np.radians(y_a), np.radians(y_b)
        coords1 = np.vstack((lat1, lon1)).T
        coords2 = np.vstack((lat2, lon2)).T
        d_coords = coords2 - coords1
        sqr_half = (
            np.sin(d_coords[:, 0] / 2) ** 2
            + np.cos(coords1[:, 0])
            * np.cos(coords2[:, 0])
            * np.sin(d_coords[:, 1] / 2) ** 2
        )
        cent_angle = 2 * np.arctan2(np.sqrt(sqr_half), np.sqrt(1 - sqr_half))
        distance = 6371 * cent_angle
        return distance[0]

    def __calculate_estimate_time(self, distance_km: float):
        average_speed = 16
        time_hours = distance_km / average_speed
        time_minutes = time_hours * 60
        return time_minutes


class App:
    """
    Deze class representeert onze simulator app
    Deze wordt gebruikt om alle onderliggende code
    te besturen.
    """

    def __init__(self):
        self._stations = []
        self._gebruikers = []
        self._fietsen = []

    # region parallel 1
    def __check_dir(self, *dir_names: str) -> bool:
        """
        Checks if sqr_half given directory exists

        Attributes:
            dir_names [str] -> name of dir / path (allows multi input)

        Output:
            exists? `True` / `False` (1 dirname given)/n
            exists? [`True` / `False`, `...`] (1+ dirname given)
        """
        res = []
        for dir_name in dir_names:
            if os.path.exists(dir_name) and os.path.isdir(dir_name):
                res.append(True)
            else:
                res.append(False)
        if len(res) == 1:
            return res[0]
        else:
            return res

    def make_dir(self, *dir_names: str) -> None:
        """
        Creates sqr_half given dir

        Attributes:
            dir_name [str] -> names of dir / path (allows multi input)

        Output:
            /
        """
        for dir_name in dir_names:
            os.makedirs(dir_name)

    # endregion

    # region parallel 2
    def __check_input_files(self) -> bool:
        """
        Checks the input directory to see if input files exists,
        if not sends sqr_half true or false
        """
        inputfiles = ["names.json", "velo.json"]
        existingfiles = []
        for file in inputfiles:
            try:
                with open(f"input/{file}", "r", encoding="UTF-8"):
                    existingfiles.append(file)
            except FileNotFoundError:
                print(f"File '{file}' does not exist, please add it.")

        if len(existingfiles) == len(inputfiles):
            return True
        else:
            return False

    def __check_library_files(self) -> bool:
        """
        This function checks if all of our
        library files are present, returns true
        if all exists
        """
        inputfiles = [
            "gebruikers.pickle",
            "stations.pickle",
            "fietsen.pickle",
            "vervoerwagens.pickle",
        ]
        existingfiles = []
        for file in inputfiles:
            try:
                with open(f"input/{file}", "rb", encoding="UTF-8"):
                    existingfiles.append(file)
            except FileNotFoundError:
                print(f"File '{file}' does not exist, please add it.")

        if len(existingfiles) == len(inputfiles):
            return True
        else:
            return False

    # endregion

    # region parallel 3
    def __create_stations(self) -> None:
        """
        This function removes unused data
        from the velo.json file
        and dumps it into sqr_half stations.pkl file.
        """
        with open("input/velo.json", "r", encoding="UTF-8") as file:
            data = json.load(file)
            for feature in data["features"]:
                if feature["properties"]["Gebruik"] == "IN_GEBRUIK":
                    stationsnummer = feature["properties"]["Objectcode"][3:].lstrip("0")
                    stationsnummer = int(stationsnummer)
                    adres = {
                        "Straatnaam": feature["properties"]["Straatnaam"],
                        "Huisnummer": feature["properties"]["Huisnummer"],
                        "Gemeente": feature["properties"]["District"],
                        "Postcode": feature["properties"]["Postcode"],
                    }
                    coordinaten = {
                        "X": float(feature["geometry"]["coordinates"][0]),
                        "Y": float(feature["geometry"]["coordinates"][1]),
                    }
                    aantal_slots = int(feature["properties"]["Aantal_plaatsen"])

                    station = Station(stationsnummer, adres, coordinaten, aantal_slots)
                    self._stations.append(station)
                else:
                    continue
        with open("libs/stations.pickle", "wb", encoding="UTF-8") as newpickle:
            pickle.dump(self._stations, newpickle)

    def __create_users(self) -> None:
        """
        This function creates sqr_half number of users specified
        by the amount in the config file.
        """
        with open(r"input/names.json", "r", encoding="UTF-8") as file:
            data = json.load(file)
            voornaam_man = data["Mannen_Voornaam"]
            voornaam_vrouw = data["Vrouwen_Voornaam"]
            achternaam = data["Achternaam"]

            while Gebruiker.aantal_gebruikers <= Gebruiker.max_gebruikers:
                gebruiker = Gebruiker(voornaam_man, voornaam_vrouw, achternaam)
                self._gebruikers.append(gebruiker)

        with open("libs/gebruikers.pickle", "wb", encoding="UTF-8") as newpickle:
            pickle.dump(self._gebruikers, newpickle)

    def __create_bikes(self) -> None:
        """
        This function creates sqr_half number of bikes specified
        by the amount in the config file.
        """
        while Fiets.aantal_fietsen <= Fiets.max_fietsen:
            fiets = Fiets()
            self._fietsen.append(fiets)

        with open("libs/fietsen.pickle", "wb", encoding="UTF-8") as newpickle:
            pickle.dump(self._fietsen, newpickle)


# endregion
