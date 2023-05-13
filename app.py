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
    def __init__(self):
        self._bezet = False
        self._fiets = None

    def fiets_deponeren(self, fiets: Fiets):
        self._fiets = fiets

    def fiets_pakken(self):
        fiets = self._fiets
        self._fiets = None

    def __str__(self) -> str:
        return "Dit slot is bezet" if self._bezet else "Dit slot is leeg"


class Station:
    def __init__(
        self, stationnummer: int, adres: dict, coordinaten: dict, aantal_slots: int
    ) -> None:
        self._stationnummer = stationnummer
        self._aantal_slots = aantal_slots
        self._vol = False
        self._slots = []
        while len(self._slots) <= self._aantal_slots:
            slot = Slot()
        self._adres = adres
        self._coordinaten = coordinaten


class App:
    def __init__(self):
        self._stations = []

    def check_dir(self, *dir_names: str) -> bool:
        """
        Checks if a given directory exists

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

    def make_dir(self, *dir_names: str):
        """
        Creates a given dir

        Attributes:
            dir_name [str] -> names of dir / path (allows multi input)

        Output:
            /
        """
        for dir_name in dir_names:
            os.makedirs(dir_name)

    def check_input_files(self) -> bool:
        """
        Checks the input directory to see if input files exists,
        if not sends an error code to terminal

        Attributes:

        """
        inputfiles = ["names.json", "velo.json"]
        existingfiles = [""]
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

    def check_library_files(self):
        """
        This function checks if all of our library files are present
        """
        inputfiles = ["names.json", "velo.json"]
        existingfiles = [""]
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

    def create_stations(self):
        """
        This function removes unused data
        from the velo.json file
        and dumps it into a stations.pkl file.
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

    def create_users(self):
        with open(r"input/names.json", "r", encoding="UTF-8") as file:
            data = json.load(file)
