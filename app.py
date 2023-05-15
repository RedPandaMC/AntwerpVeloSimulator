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
import yaml
import numpy as np


class MissingJsonFilesError(Exception):
    """
    A custom error to let the user know what went wrong
    """

    def __init__(self, missing_files):
        self.missing_files = missing_files

    def __str__(self):
        return (
            "De volgende .JSON files die nodig"
            + f" zijn voor het setup process missen: {', '.join(self.missing_files)}"
        )


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

    def _verplaatsings_update(self, rit: Rit):
        """
        Deze functie update een aantal instance attributen
        """
        self._laatste_rit = rit
        self._aantal_ritten += 1
        Gebruiker.totaal_aantal_ritten += 1


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
        self._transporteurs = []
        self._willekeurigheid = 0

    def setup(self):
        """
        Runs the program setup process:

        Step 1
            -> check if all directories are available
                - input,config,libs
            -> create missing directories if needed
        step 2
            -> check if all files are in each directory
                - config: config.yaml
                - libs: gebruikers.pickle, stations.pickle, fietsen.pickle, vervoerwagens.pickle
                - input: names.json, velo.json if missing and gebruikers.pickle,
                         stations.pickle does not exist ===> send error to user
            -> load and assign config parameters
            -> create missing files if needed
        """

        # region stap1
        dirs_needed = ["input", "config", "libs"]
        dirs_present = self._check_dir("input", "config", "libs")
        dirs_to_create = self._mask_list(dirs_needed, dirs_present)
        self._make_dir(*dirs_to_create)

        if "input" in dirs_to_create and "libs" in dirs_to_create:
            missing_files = ["names.json", "velo.json"]
            raise MissingJsonFilesError(missing_files)
        # endregion

        # region stap2
        config_file_present = self._check_files("config", "config.yaml")
        if config_file_present[0] is False:
            self._create_config()
        self._load_config()

        lib_files_needed = [
            "gebruikers.pickle",
            "stations.pickle",
            "fietsen.pickle",
            "vervoerwagens.pickle",
        ]
        lib_files_present = self._check_files(
            "libs",
            "gebruikers.pickle",
            "stations.pickle",
            "fietsen.pickle",
            "vervoerwagens.pickle",
        )
        lib_files_to_create = self._mask_list(lib_files_needed, lib_files_present)
        if "gebruikers.pickle" in lib_files_to_create:
            self._create_users()
        if "stations.pickle" in lib_files_to_create:
            self._create_stations()
        if "fietsen.pickle" in lib_files_to_create:
            self._create_bikes()
        if "vervoerwagens.pickle" in lib_files_to_create:
            self._create_bikemovers()
        # endregion

    # region __functions-setup__
    def _check_dir(self, *dir_names: str) -> list[bool]:
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
        return res

    def _make_dir(self, *dir_names: str) -> None:
        """
        Creates a given dir

        Attributes:
            dir_name [str] -> names of dir / path (allows multi input)

        Output:
            /
        """
        for dir_name in dir_names:
            os.makedirs(dir_name)

    def _mask_list(self, original_list: list[str], mask: list[bool]) -> list[str]:
        masked_list = []
        for item, mask in zip(original_list, mask):
            if not mask:
                masked_list.append(item)
        return masked_list

    def _check_files(self, directory: str, *files: list) -> list[bool]:
        """
        Checks the input directory to see if specified files exist,
        returns True if all files exist, False otherwise.
        """
        existing_files = []
        for file in files:
            try:
                with open(
                    f"{directory}/{file}",
                    "r",
                    encoding="UTF-8",
                ):
                    existing_files.append(True)
            except FileNotFoundError:
                existing_files.append(False)
        return existing_files

    def _create_stations(self) -> None:
        """
        This function removes unused data
        from the velo.json file
        and dumps it into libs/stations.pkl file.
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
        with open("libs/stations.pickle", "wb") as newpickle:
            pickle.dump(self._stations, newpickle)

    def _create_users(self) -> None:
        """
        This function creates a number of 'users'
        specified by the amount in the config file.
        """
        with open(r"input/names.json", "r", encoding="UTF-8") as file:
            data = json.load(file)
            voornaam_man = data["Mannen_Voornaam"]
            voornaam_vrouw = data["Vrouwen_Voornaam"]
            achternaam = data["Achternaam"]

            while Gebruiker.aantal_gebruikers <= Gebruiker.max_gebruikers:
                gebruiker = Gebruiker(voornaam_man, voornaam_vrouw, achternaam)
                self._gebruikers.append(gebruiker)

        with open("libs/gebruikers.pickle", "wb") as newpickle:
            pickle.dump(self._gebruikers, newpickle)

    def _create_bikes(self) -> None:
        """
        This function creates a number of 'bikes' specified
        by the amount in the config file.
        """
        while Fiets.aantal_fietsen <= Fiets.max_fietsen:
            fiets = Fiets()
            self._fietsen.append(fiets)

        with open("libs/fietsen.pickle", "wb") as newpickle:
            pickle.dump(self._fietsen, newpickle)

    def _create_bikemovers(self) -> None:
        """
        This function creates a number of 'bikemovers' specified
        by the amount in the config file
        """
        while (
            Fietstransporteur.aantal_transporteurs
            <= Fietstransporteur.max_aantal_fietsen
        ):
            fietstransporteur = Fietstransporteur()
            self._transporteurs.append(fietstransporteur)

        with open("libs/vervoerwagens.pickle", "wb") as newpickle:
            pickle.dump(self._fietsen, newpickle)

    def _create_config(self) -> None:
        file_path = os.path.join("config", "config.yaml")
        config_data = {
            "max_log_bestandsgrote": 10,
            "aantal_gebruikers": 100,
            "aantal_fietsen": 50,
            "aantal_transporteurs": 25,
            "willekeurigheid": 50,
        }
        with open(file_path, "w", encoding="UTF-8") as config_file:
            yaml.dump(config_data, config_file)
        with open(file_path, "a", encoding="UTF-8") as config_file:
            config_file.write(
                "\n# Max log file size in megabytes\n# Randomness percentage (between 0-100)"
            )

    def _load_config(self) -> None:
        with open("config/config.yaml", "r", encoding="UTF-8") as config_file:
            config_data = yaml.safe_load(config_file)
            Gebruiker.max_gebruikers = config_data["aantal_gebruikers"]
            Fiets.max_fietsen = config_data["aantal_fietsen"]
            Fietstransporteur.max_transporteurs = config_data["aantal_transporteurs"]
            self._willekeurigheid = config_data["willekeurigheid"]
            # add log class here

    # endregion


def main():
    """
    Processes sys.argv flags, and
    runs the according functions
    """
    # region patterns
    help_pat = r"^(-{1,2}[hH]|-{1,2}[hH]elp)$"
    setup_pat = r"^(-{1,2}[sS]|-{1,2}[sS]etup)$"
    run_pat = r"^(-{1,2}[rR]|-{1,2}[rR]un)$"
    load_pat = r"^(-{1,2}[lL]|-{1,2}[lL]oad)$"
    # endregion
    if len(sys.argv) > 1:
        user_flag = str(sys.argv[1])
        if re.match(help_pat, user_flag):
            print("Running help")
        elif re.match(setup_pat, user_flag):
            velosim.setup()
        elif re.match(run_pat, user_flag):
            print("Running run")
        elif re.match(load_pat, user_flag):
            print("Running load")
        else:
            print("Flag not recognized.")
    else:
        print("Please add a flag")


if __name__ == "__main__":
    velosim = App()
    main()
